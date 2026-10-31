#!/usr/bin/env python3
"""Mellum's local backend on llama.cpp, and one-shot chat against it.

Settings come from [tool.mellum] in the repo's pyproject.toml, so the
learner can read every value the server and the request receive. Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import ntpath
import os
import posixpath
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "learn" / "code" / "profile" / "models.json"
HOST = "127.0.0.1"
PORT = 8002
ALIAS = "Mellum2.1-12B-A2.5B-Thinking"
PIDFILE = Path(tempfile.gettempdir()) / "llamacpp-mellum.pid"
LOGFILE = Path(tempfile.gettempdir()) / "llamacpp-mellum.log"
MISSING = "llama-server not found on PATH; install it: docs/backends/llamacpp.md"
START_HINT = "start it: uv run scripts/backend.py start"
PROGRESS_EVERY = 10
# llama.cpp learned the mellum architecture in build 9482 (ggml-org/llama.cpp#23966);
# this repo was tested on 11669.
MIN_BUILD = 9482
TESTED_BUILD = 11669
UPGRADE = "upgrade llama.cpp: docs/backends/llamacpp.md"
STOP_CMD = "uv run scripts/backend.py stop"
VERIFY_CMD = "uv run scripts/backend.py verify"


def load_settings(root: Path = ROOT) -> dict:
    data = tomllib.loads((root / "pyproject.toml").read_text())
    return data["tool"]["mellum"]


def serve_argv(
    settings: dict,
    host: str = HOST,
    port: int = PORT,
    binary: str = "llama-server",
) -> list[str]:
    argv = [
        binary, "-hf", settings["model"], "-a", ALIAS,
        "--host", host, "--port", str(port),
        # No -ngl by default: llama.cpp's --fit splits the model between GPU and
        # CPU to fit free device memory, which keeps the recipe portable to a
        # small machine. -c is set, so --fit never shrinks it. Set MELLUM_NGL
        # (e.g. 999) to force full GPU offload where there is memory to spare.
        "-c", str(settings["context"]), "-np", "1",
        "--jinja", "-fa", "auto", "-b", "512", "-ub", "512",
        "-ctk", "q8_0", "-ctv", "q8_0",
    ]
    ngl = os.environ.get("MELLUM_NGL")
    if ngl:
        argv += ["-ngl", ngl]
    return argv


def chat_body(settings: dict, prompt: str) -> dict:
    return {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": settings["max_tokens"],
        "temperature": settings["temperature"],
        "top_p": settings["top_p"],
        "top_k": settings["top_k"],
    }


def _get_json(url: str, timeout: float = 2) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def health(host: str = HOST, port: int = PORT) -> dict | None:
    return _get_json(f"http://{host}:{port}/health")


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def _alive(pid: int) -> bool:
    if os.name == "nt":
        # os.kill(pid, 0) terminates the process on Windows; ask tasklist instead.
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True,
        ).stdout
        return f'"{pid}"' in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def progress_line(log: str) -> str | None:
    """The log's last non-empty line, with a model download read as a percentage."""
    lines = [line.strip() for line in re.split(r"[\r\n]+", log) if line.strip()]
    if not lines:
        return None
    # A curl-style row from llama-server's -hf download, 12 columns:
    # "47 7697M 47 3634M 0 0 16.0M 0 0:08:00 0:03:46 0:04:14 17.0M"
    fields = lines[-1].split()
    if len(fields) == 12 and fields[0].isdigit() and ":" in fields[10]:
        return f"downloading the model: {fields[0]}% of {fields[1]}, {fields[10]} left"
    return lines[-1]


def progress_report(tick: int, line: str | None, previous: str | None, changed_at: int) -> str:
    """One progress line; a log line seen last time is reported as quiet, not repeated."""
    if line is None:
        return f"[{tick}s] waiting for output"
    if line == previous:
        return f"[{tick}s] no new output for {tick - changed_at}s; last: {line}"
    return f"[{tick}s] {line}"


def parse_build(text: str) -> int | None:
    """The build number from `llama-server --version`: newer builds print
    "version: 0.7.0-dev (build 11829, commit 184f65360)", older ones
    "version: 7360 (53ecd4fdb)"."""
    match = (re.search(r"\(build (\d+)", text)
             or re.search(r"^version: (\d+) \(", text, re.MULTILINE))
    return int(match.group(1)) if match else None


def server_build(binary: str) -> int | None:
    try:
        done = subprocess.run([binary, "--version"], capture_output=True, text=True,
                              timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_build(done.stdout + done.stderr)


def version_problem(build: int) -> str | None:
    if build >= MIN_BUILD:
        return None
    return (f"llama-server build {build} is too old for Mellum: llama.cpp added the "
            f"mellum architecture in build {MIN_BUILD} (tested on {TESTED_BUILD}); "
            f"{UPGRADE}")


def on_path(binary: str) -> list[str]:
    """Every `binary` on PATH, in the order the shell tries them; an explicit path as is."""
    if os.path.dirname(binary):
        found = shutil.which(binary)
        return [found] if found else []
    hits, seen = [], set()
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        hit = folder and shutil.which(binary, path=folder)
        if hit and (key := os.path.normcase(os.path.abspath(hit))) not in seen:
            seen.add(key)
            hits.append(hit)
    return hits


def choose_server(found: list) -> tuple[str | None, int | None, list[str]]:
    """The first llama-server on PATH new enough for Mellum, its build, and notes.

    An old one earlier on PATH is skipped and named, since it would otherwise
    win and fail to load the model. One whose build can't be read is tried.
    """
    notes = []
    for path, build in found:
        if build is None:
            notes.append(f"could not read a build number from {path} --version; trying it anyway")
            return path, None, notes
        if build >= MIN_BUILD:
            return path, build, notes
        notes.append(f"skipping {path} (build {build}, too old for Mellum); "
                     f"remove {os.path.dirname(path)} from PATH so it stops coming first")
    first = found[0][1] if found else 0
    notes = [version_problem(first) or "", "found on PATH:"]
    notes += [f"  {path} (build {build})" for path, build in found]
    return None, None, notes


def diagnose(log: str) -> list[str]:
    """What to do next, from the known failures in llama-server's log."""
    hints = []
    if "unable to rename file" in log:
        hints.append("another llama-server was using the same model files; stop it "
                     f"({STOP_CMD}, or end every llama-server process) and start again")
    if "unknown model architecture" in log:
        hints.append(f"llama.cpp is too old for this model; {UPGRADE}")
    elif "failed to load model" in log:
        hints.append(f"the downloaded model may be damaged; check it: {VERIFY_CMD} "
                     "(add --delete to remove a bad copy so start downloads it again)")
    return hints


MODEL_IN_LOG = re.compile(
    r"using cached file: (.+?\.gguf)"
    r"|failed to load model '(.+?\.gguf)'"
    r"|(?:^| )to ((?:[A-Za-z]:)?[\\/][^\r\n]*?\.gguf)\.downloadInProgress",
    re.MULTILINE,
)


def logged_model_file(log: str) -> str | None:
    """The model path the newest log line names, whichever llama.cpp cache it uses."""
    matches = list(MODEL_IN_LOG.finditer(log))
    if not matches:
        return None
    return next(group for group in matches[-1].groups() if group)


def model_candidates(model: str, filename: str, osname: str, env: dict) -> list[str]:
    """Where llama-server -hf keeps the file: llama.cpp's own cache (older builds),
    then the Hugging Face hub cache (newer builds), as a glob over snapshots."""
    path = ntpath if osname == "nt" else posixpath
    repo = model.split(":")[0]
    home = env.get("USERPROFILE" if osname == "nt" else "HOME", "~")
    if env.get("LLAMA_CACHE"):
        llama = env["LLAMA_CACHE"]
    elif osname == "nt":
        llama = path.join(env.get("LOCALAPPDATA", path.join(home, "AppData", "Local")), "llama.cpp")
    elif osname == "darwin":
        llama = path.join(home, "Library", "Caches", "llama.cpp")
    else:
        llama = path.join(env.get("XDG_CACHE_HOME", path.join(home, ".cache")), "llama.cpp")
    hub = (env.get("HF_HUB_CACHE")
           or (env.get("HF_HOME") and path.join(env["HF_HOME"], "hub"))
           or path.join(home, ".cache", "huggingface", "hub"))
    return [
        path.join(llama, f"{repo.replace('/', '_')}_{filename}"),
        path.join(hub, f"models--{repo.replace('/', '--')}", "snapshots", "*", filename),
    ]


def pick_file(tree: list, quant: str) -> tuple[str, int, str] | None:
    """The quant's GGUF in a Hugging Face tree listing: (path, size, sha256)."""
    for entry in tree:
        name = entry.get("path", "")
        if name.endswith(f"-{quant}.gguf") and not name.startswith("mtp-") and entry.get("lfs"):
            return name, entry["lfs"]["size"], entry["lfs"]["oid"]
    return None


def _log_tail(logfile: Path, offset: int, size: int = 4000) -> str:
    try:
        with logfile.open("rb") as log:
            log.seek(max(offset, logfile.stat().st_size - size))
            return log.read().decode(errors="replace")
    except FileNotFoundError:
        return ""


def _say(line: str) -> None:
    print(line, file=sys.stderr, flush=True)


def _explain_failure(logfile: Path, offset: int) -> None:
    for hint in diagnose(_log_tail(logfile, offset, size=200_000)):
        _say(f"next: {hint}")


def status(host: str, port: int, pidfile: Path = PIDFILE, logfile: Path = LOGFILE) -> int:
    if health(host, port) is None:
        pid = _read_pid(pidfile)
        if pid is not None and _alive(pid):
            print(f"starting (pid {pid}); not answering on {host}:{port} yet")
            line = progress_line(_log_tail(logfile, 0))
            if line:
                print(f"  {line}")
            return 0
        print(f"down on {host}:{port}")
        print(f"  {START_HINT}")
        return 0
    print(f"up on {host}:{port}")
    props = _get_json(f"http://{host}:{port}/props") or {}
    n_ctx = (props.get("default_generation_settings") or {}).get("n_ctx")
    if n_ctx is not None:
        print(f"  n_ctx {n_ctx}")
    return 0


def start(settings: dict, host: str, port: int, pidfile: Path, logfile: Path,
          binary: str, wait: int = 900) -> int:
    pid = _read_pid(pidfile)
    if health(host, port) is not None:
        suffix = f" (pid {pid})" if pid else ""
        print(f"already up on {host}:{port}{suffix}")
        return 0
    if pid is not None and _alive(pid):
        # Two servers downloading into one cache file corrupt it.
        _say(f"llama-server is still starting (pid {pid}); not starting a second one")
        _say(f"watch: uv run scripts/backend.py status   stop: {STOP_CMD}")
        return 1
    found = [(path, server_build(path)) for path in on_path(binary)]
    if not found:
        print(MISSING, file=sys.stderr)
        return 2
    path, build, notes = choose_server(found)
    for note in notes:
        _say(note)
    if path is None:
        return 2
    binary = path
    logfile.parent.mkdir(parents=True, exist_ok=True)
    offset = logfile.stat().st_size if logfile.exists() else 0
    # Detach the server so Ctrl+C here, or closing this terminal, leaves it running.
    detach = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
              else {"start_new_session": True})
    with logfile.open("ab") as log:
        process = subprocess.Popen(
            serve_argv(settings, host, port, binary),
            stdout=log, stderr=subprocess.STDOUT, **detach,
        )
    pidfile.write_text(str(process.pid))
    say = _say
    build_note = f", build {build}" if build is not None else ""
    say(f"starting {binary}{build_note} on {host}:{port} (pid {process.pid})")
    say(f"log {logfile}")
    say("the first start downloads the model (about 7.7 GB) and can take minutes; "
        f"progress every {PROGRESS_EVERY}s, Ctrl+C stops waiting, not the server")
    started = time.monotonic()
    previous, changed_at = None, 0
    try:
        for tick in range(1, wait + 1):
            if health(host, port) is not None:
                print(f"up on {host}:{port} (pid {process.pid}) "
                      f"after {time.monotonic() - started:.0f}s")
                return 0
            if process.poll() is not None:
                pidfile.unlink(missing_ok=True)
                say(f"llama-server exited with code {process.returncode}; "
                    f"the end of {logfile}:")
                for line in _log_tail(logfile, offset).splitlines()[-15:]:
                    say(f"  | {line}")
                _explain_failure(logfile, offset)
                return 1
            if tick % PROGRESS_EVERY == 0:
                line = progress_line(_log_tail(logfile, offset))
                say(progress_report(tick, line, previous, changed_at))
                if line != previous:
                    previous, changed_at = line, tick
            time.sleep(1)
    except KeyboardInterrupt:
        say(f"stopped waiting; the server keeps starting (pid {process.pid}).")
        say("check: uv run scripts/backend.py status   "
            "stop: uv run scripts/backend.py stop")
        return 130
    say(f"no health response after {wait}s; see {logfile}; "
        "stop with: uv run scripts/backend.py stop")
    _explain_failure(logfile, offset)
    return 1


def stop(pidfile: Path) -> int:
    pid = _read_pid(pidfile)
    if pid is None:
        print("not running")
        return 0
    if not _alive(pid):
        pidfile.unlink(missing_ok=True)
        print("not running")
        return 0
    _end(pid)
    pidfile.unlink(missing_ok=True)
    print(f"stopped pid {pid}")
    return 0


def _end(pid: int, force: bool = False) -> None:
    if os.name == "nt":
        # Windows has no SIGTERM; end the process and anything it started.
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)
        return
    try:
        os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
    except ProcessLookupError:
        pass


def server_pids(name: str) -> list[int]:
    """Every running process called `name` (llama-server.exe on Windows)."""
    if os.name == "nt":
        out = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {name}.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True,
        ).stdout
        return [int(row[1]) for row in csv.reader(out.splitlines())
                if len(row) > 1 and row[1].isdigit()]
    out = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True).stdout
    return [int(pid) for pid in out.split()]


def kill_all(name: str, pidfile: Path, grace: int = 5) -> int:
    """End every `name` process, whatever started it: a lost pidfile, a `serve`
    in another terminal, or a second server still downloading."""
    pidfile.unlink(missing_ok=True)
    pids = server_pids(name)
    if not pids:
        print(f"no {name} running")
        return 0
    for pid in pids:
        _end(pid)
    for _ in range(grace * 10):
        if not set(pids) & set(server_pids(name)):
            break
        time.sleep(0.1)
    else:
        for pid in set(pids) & set(server_pids(name)):
            _end(pid, force=True)
    left = set(pids) & set(server_pids(name))
    for pid in pids:
        if pid not in left:
            print(f"killed {name} pid {pid}")
    if left:
        _say(f"could not end {name} pid(s) {', '.join(map(str, sorted(left)))}; "
             "they may belong to another user")
        return 1
    return 0


def _find_model(settings: dict, filename: str, logfile: Path) -> Path | None:
    logged = logged_model_file(_log_tail(logfile, 0, size=2_000_000))
    if logged and Path(logged).exists():
        return Path(logged)
    osname = "darwin" if sys.platform == "darwin" else os.name
    for candidate in model_candidates(settings["model"], filename, osname, dict(os.environ)):
        found = sorted(glob.glob(candidate))
        if found:
            return Path(found[-1])
    return None


def _sha256(path: Path, size: int) -> str:
    digest, done, step = hashlib.sha256(), 0, 1 << 30
    with path.open("rb") as model:
        while chunk := model.read(1 << 24):
            digest.update(chunk)
            if (done + len(chunk)) // step > done // step:
                _say(f"  {done + len(chunk) >> 30} of {size / (1 << 30):.1f} GiB checked")
            done += len(chunk)
    return digest.hexdigest()


def _remove_model(path: Path) -> None:
    # The Hugging Face cache links snapshots to blobs; remove both.
    target = path.resolve()
    for doomed in {path, target, Path(f"{path}.etag")}:
        doomed.unlink(missing_ok=True)


def verify(settings: dict, model_file: Path | None, logfile: Path, delete: bool) -> int:
    repo, quant = settings["model"].split(":")
    tree = _get_json(f"https://huggingface.co/api/models/{repo}/tree/main", timeout=30)
    picked = pick_file(tree, quant) if isinstance(tree, list) else None
    if picked is None:
        _say(f"could not read {repo}'s file list from Hugging Face; check the network")
        return 1
    filename, size, sha = picked
    path = model_file or _find_model(settings, filename, logfile)
    if path is None or not path.exists():
        _say(f"no downloaded {filename} found; {START_HINT}")
        return 1
    print(f"model {path}")
    actual = path.stat().st_size
    if actual != size:
        problem = f"size is {actual:,} bytes; Hugging Face has {size:,}"
    else:
        _say(f"checking sha256 of {size / (1 << 30):.1f} GiB; this takes a minute or two")
        digest = _sha256(path, size)
        if digest == sha:
            print(f"ok: matches Hugging Face (sha256 {sha[:12]}...)")
            return 0
        problem = f"sha256 is {digest[:12]}...; Hugging Face has {sha[:12]}..."
    print(f"damaged: {problem}")
    if not delete:
        print(f"  remove it so start downloads it again: {VERIFY_CMD} --delete")
        return 1
    pid = _read_pid(PIDFILE)
    if pid is not None and _alive(pid):
        print(f"  not deleting while llama-server runs (pid {pid}); {STOP_CMD} first")
        return 1
    _remove_model(path)
    print(f"  deleted; {START_HINT}")
    return 1


def profile_models(settings: dict) -> dict:
    return {
        "providers": {
            "llamacpp": {
                "name": "llama.cpp",
                "baseUrl": f"http://{HOST}:{PORT}/v1",
                "api": "openai-completions",
                "apiKey": "not-needed",
                "models": [
                    {
                        "id": ALIAS,
                        "name": "Mellum 2.1 12B-A2.5B Thinking (Q4_K_M, llama.cpp)",
                        "reasoning": True,
                        "input": ["text"],
                        "contextWindow": settings["context"],
                        "maxTokens": settings["max_tokens"],
                        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                        "samplingParams": {
                            "temperature": settings["temperature"],
                            "top_p": settings["top_p"],
                            "top_k": settings["top_k"],
                            "min_p": 0,
                            "presence_penalty": 0,
                            "repetition_penalty": 1,
                        },
                        "compat": {
                            "supportsDeveloperRole": False,
                            "supportsReasoningEffort": False,
                            "maxTokensField": "max_tokens",
                            "thinkingFormat": "qwen-chat-template",
                        },
                    }
                ],
            }
        }
    }


def render_profile(settings: dict) -> str:
    return json.dumps(profile_models(settings), indent=2) + "\n"


def chat(settings: dict, prompt: str, host: str = HOST, port: int = PORT) -> None:
    request = urllib.request.Request(
        f"http://{host}:{port}/v1/chat/completions",
        data=json.dumps(chat_body(settings, prompt)).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            data = json.load(response)
    except urllib.error.URLError as error:
        raise SystemExit(
            f"no server on {host}:{port} ({error.reason}); "
            "run: uv run scripts/backend.py start"
        )
    message = data["choices"][0]["message"]
    if message.get("reasoning_content"):
        print("[thinking] " + message["reasoning_content"][:400], file=sys.stderr)
    print(message.get("content", ""))
    usage = data.get("usage") or {}
    if "completion_tokens" in usage:
        print(f"({usage['completion_tokens']} tokens)", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run llama-server in the foreground")
    serve.add_argument("--dry-run", action="store_true")
    serve.add_argument("--host", default=HOST)
    serve.add_argument("--port", type=int, default=PORT)
    serve.add_argument("--server-binary", default="llama-server")

    for name, help_text in (
        ("start", "run llama-server in the background and wait for health"),
        ("stop", "stop the background server"),
        ("status", "report whether the server answers"),
    ):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--host", default=HOST)
        cmd.add_argument("--port", type=int, default=PORT)
        cmd.add_argument("--pidfile", type=Path, default=PIDFILE)
        cmd.add_argument("--logfile", type=Path, default=LOGFILE)
        if name == "start":
            cmd.add_argument("--server-binary", default="llama-server")
            cmd.add_argument("--wait-seconds", type=int, default=900)

    kill = sub.add_parser(
        "kill", help="end every llama-server process, not just the one in the pidfile")
    kill.add_argument("--name", default="llama-server",
                      help="the process name to end (default: llama-server)")
    kill.add_argument("--pidfile", type=Path, default=PIDFILE)

    check = sub.add_parser(
        "verify", help="check the downloaded model against Hugging Face's sha256")
    check.add_argument("--model-file", type=Path,
                       help="the .gguf to check; found from the log or cache by default")
    check.add_argument("--logfile", type=Path, default=LOGFILE)
    check.add_argument("--delete", action="store_true",
                       help="remove a damaged file so start downloads it again")

    profile = sub.add_parser("profile", help="write the private Pi profile")
    profile.add_argument("--dry-run", action="store_true")

    one = sub.add_parser("chat", help="one prompt against the running server")
    one.add_argument("prompt")
    one.add_argument("--dry-run", action="store_true")
    one.add_argument("--host", default=HOST)
    one.add_argument("--port", type=int, default=PORT)

    args = parser.parse_args(argv)
    settings = load_settings()

    if args.command == "status":
        return status(args.host, args.port, args.pidfile, args.logfile)
    if args.command == "kill":
        return kill_all(args.name, args.pidfile)
    if args.command == "verify":
        return verify(settings, args.model_file, args.logfile, args.delete)
    if args.command == "stop":
        return stop(args.pidfile)
    if args.command == "start":
        return start(settings, args.host, args.port, args.pidfile, args.logfile,
                     args.server_binary, args.wait_seconds)

    if args.command == "profile":
        rendered = render_profile(settings)
        if args.dry_run:
            print(rendered, end="")
            return 0
        PROFILE.parent.mkdir(parents=True, exist_ok=True)
        PROFILE.write_text(rendered)
        print(f"wrote {PROFILE.relative_to(ROOT)}")
        return 0

    if args.command == "serve":
        cmd = serve_argv(settings, args.host, args.port, args.server_binary)
        if args.dry_run:
            print(shlex.join(cmd))
            return 0
        try:
            os.execvp(cmd[0], cmd)
        except FileNotFoundError:
            raise SystemExit(MISSING)
    else:
        if args.dry_run:
            print(json.dumps(chat_body(settings, args.prompt)))
            return 0
        chat(settings, args.prompt, args.host, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
