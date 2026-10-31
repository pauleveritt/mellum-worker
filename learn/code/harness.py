#!/usr/bin/env python3
"""Run one eval suite through base Pi in a fresh directory and score it.

The ladder measures; this teaches. A suite is a project with a mission,
tech stack and roadmap; its hidden graders stay out of the workspace until
the child has exited, and the run lives outside the repo.
"""

from __future__ import annotations

import argparse
import fnmatch
import platform
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

CODE = Path(__file__).resolve().parent
RUNS = Path(tempfile.gettempdir()) / "mellum-eval-runs"
SUITES = CODE / "suites"
RECORDER = CODE.parent.parent / "extensions" / "mellum-recorder.ts"
PROFILE = CODE / "profile"
EXTENSION = CODE.parents[1] / "extensions" / "mellum-worker.ts"
# The think-tag repair (a no-op on a correctly served reply). The flow loads it in every session; in
# the harness it is the remedy unit context/repair-think-tags, listed by the lines that want it.
THINK_TAGS = CODE.parents[1] / "extensions" / "mellum-think-tags.ts"
REMEDIES = CODE.parents[1] / "remedies"
GUARDS_WITH_SERVER = {"emptyFinalNudge": 3, "loopBreaker": True,
                      "blockForegroundServer": True}
ARMS = ("bare", "worker", "no-prompt", "no-nudge", "no-loop", "no-facts",
        "server-guard", "no-facts-guard", "strip-thinking")
# Every knob an arm may set. A run clears them from the inherited environment
# first, so an exported value cannot make two arms the same policy.
ARM_ENV_KEYS = ("MELLUM_MODE", "MELLUM_GUARDS", "MELLUM_WORKER_PROMPT",
                "MELLUM_MODE_FACTS", "MELLUM_STRIP_THINKING")
FLAGS = [
    "-p", "--no-approve", "--no-extensions", "--no-skills",
    "--no-prompt-templates", "--no-themes", "--no-context-files",
]


@dataclass(frozen=True)
class Suite:
    name: str
    prompts: list[str]
    tests: Path
    start: Path | None
    expected: tuple[str, ...] = ()
    canary: str | None = None
    root: Path | None = None
    layout: dict | None = None
    # Caps on run.json fields (record.json): a failure that lives in the record.
    record: dict | None = None

    @property
    def prompt(self) -> str:
        return self.prompts[0]


def _read_prompt(path: Path) -> str:
    text = path.read_text().strip()
    if not text:
        raise SystemExit(f"empty prompt: {path}")
    return text


def load_suite(suites_dir: Path, name: str) -> Suite:
    base = Path(suites_dir) / name
    prompts_dir = base / "prompts"
    if prompts_dir.is_dir():
        files = sorted(prompts_dir.glob("*.md"))
        if not files:
            raise SystemExit(f"no prompts in {prompts_dir}")
        prompts = [_read_prompt(path) for path in files]
    else:
        prompts = [_read_prompt(base / "task.md")]
    grader = base / "grader"
    expected = ()
    if (base / "expected.json").is_file():
        expected = tuple(json.loads((base / "expected.json").read_text()))
    canary = None
    if (grader / "canary").is_file():
        canary = (grader / "canary").read_text().strip() or None
    start = base / "start"
    layout = None
    if (base / "layout.json").is_file():
        layout = json.loads((base / "layout.json").read_text())
    record = None
    if (base / "record.json").is_file():
        record = json.loads((base / "record.json").read_text())
    return Suite(
        name=name,
        prompts=prompts,
        tests=grader if grader.is_dir() else base / "tests",
        start=start if start.is_dir() else None,
        expected=expected,
        canary=canary,
        root=base,
        layout=layout,
        record=record,
    )


def record_failures(metrics: dict, caps: dict | None) -> list[str]:
    """The run.json fields over a challenge's caps, as reasons a learner can read."""
    return [f"{key} is {metrics.get(key, 0)} (at most {cap})"
            for key, cap in (caps or {}).items() if (metrics.get(key) or 0) > cap]


def profile_pin(profile_dir: Path) -> tuple[str, str]:
    providers = json.loads((Path(profile_dir) / "models.json").read_text())["providers"]
    provider = next(iter(providers))
    return provider, providers[provider]["models"][0]["id"]


def new_run(runs_dir: Path, name: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run = Path(runs_dir) / f"{stamp}-{name}-{uuid.uuid4().hex[:6]}"
    run.mkdir(parents=True)
    return run


def arm_settings(arm: str) -> dict:
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}; choose from {', '.join(ARMS)}")
    if arm == "bare":
        return {"extension": None, "env": {}}
    env = {"MELLUM_MODE": "1"}
    if arm == "no-prompt":
        env["MELLUM_WORKER_PROMPT"] = "pi"
    elif arm == "no-nudge":
        env["MELLUM_GUARDS"] = json.dumps({"loopBreaker": True})
    elif arm == "no-loop":
        env["MELLUM_GUARDS"] = json.dumps({"emptyFinalNudge": 3})
    elif arm == "no-facts":
        env["MELLUM_MODE_FACTS"] = "0"
    elif arm == "server-guard":
        # The full set: MELLUM_GUARDS replaces ENABLED, so a partial object
        # would silently drop the nudge and the loop breaker.
        env["MELLUM_GUARDS"] = json.dumps(GUARDS_WITH_SERVER)
    elif arm == "no-facts-guard":
        env["MELLUM_GUARDS"] = json.dumps(GUARDS_WITH_SERVER)
        env["MELLUM_MODE_FACTS"] = "0"
    elif arm == "strip-thinking":
        # Opens the seam the worker closes by default (A12): earlier reasoning is
        # dropped from the payload, everything else identical.
        env["MELLUM_STRIP_THINKING"] = "1"
    return {"extension": EXTENSION, "env": env}


def group_members(pgid: int) -> list[tuple[int, str]]:
    """Every live process in one process group, by pid and command line."""
    out = subprocess.run(["ps", "-A", "-o", "pid=,pgid=,command="],
                         capture_output=True, text=True, check=False).stdout
    members = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        pid, group, command = parts
        if pid.isdigit() and group.isdigit() and int(group) == pgid and int(pid) != os.getpid():
            members.append((int(pid), command.strip()))
    return members


def sweep_group(pgid: int, grace: float = 1.0) -> list[tuple[int, str]]:
    """End everything still running in a run's process group, and report it.

    The harness kills the group when a deadline expires, but a child that
    backgrounds a server and then settles leaves it holding a port. That has
    happened: five servers from earlier runs were still listening hours later.
    """
    found = group_members(pgid)
    if not found:
        return []

    def signal_all(signal_number: int) -> None:
        # killpg is the right call, but a sandboxed or re-parented group can
        # refuse it, so fall back to each pid. The sweep must never raise.
        try:
            os.killpg(pgid, signal_number)
            return
        except OSError:
            pass
        for pid, _ in group_members(pgid):
            try:
                os.kill(pid, signal_number)
            except OSError:
                pass

    for signal_number in (signal.SIGTERM, signal.SIGKILL):
        signal_all(signal_number)
        deadline = time.monotonic() + grace
        while time.monotonic() < deadline:
            if not group_members(pgid):
                return found
            time.sleep(0.05)
    return found


def workspace_members(workspace: Path) -> list[tuple[int, str]]:
    """Every live process whose working directory is inside `workspace`."""
    root = os.path.realpath(workspace)
    out = subprocess.run(["lsof", "-w", "-d", "cwd", "-F", "pn"],
                         capture_output=True, text=True, check=False).stdout
    pids, pid = [], None
    for line in out.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and pid is not None and pid != os.getpid():
            cwd = os.path.realpath(line[1:])
            if cwd == root or cwd.startswith(root + os.sep):
                pids.append(pid)
    if not pids:
        return []
    listed = subprocess.run(["ps", "-o", "pid=,command=", "-p", ",".join(map(str, pids))],
                            capture_output=True, text=True, check=False).stdout
    members = []
    for line in listed.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            members.append((int(parts[0]), parts[1].strip()))
    return members


def sweep_workspace(workspace: Path, grace: float = 1.0) -> list[tuple[int, str]]:
    """End every process still running inside a run's workspace, and report it.

    Pi's bash tool starts each command detached, in a session and process
    group of its own, so the group sweep never reaches a server the model
    started. Its working directory is the workspace, so that finds it. The
    sweep must never raise.
    """
    found = workspace_members(workspace)
    for signal_number in (signal.SIGTERM, signal.SIGKILL):
        for pid, _ in workspace_members(workspace):
            try:
                os.kill(pid, signal_number)
            except OSError:
                pass
        deadline = time.monotonic() + grace
        while time.monotonic() < deadline:
            if not workspace_members(workspace):
                return found
            time.sleep(0.05)
    return found


def machine_label() -> str:
    """What this run ran on: enough to tell an M1 Pro from an M5 Max.

    Peak token counts travel between machines; walls do not.
    """
    brand = memory = ""
    try:
        brand = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                               capture_output=True, text=True, check=False).stdout.strip()
        memory = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        pass
    if not brand:
        brand = f"{platform.system()} {platform.machine()}"
    ram = f", {int(memory) // (1024 ** 3)} GiB" if memory.isdigit() else ""
    return f"{brand}{ram}"


def file_hashes(root: Path) -> dict[str, str]:
    """Every file under root by relative posix path, with its sha256."""
    hashes: dict[str, str] = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        try:
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
    return hashes


def _matches(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def layout_report(root: Path, pristine: dict[str, str],
                  layout: dict) -> dict:
    """What the run created or modified, and which of it the layout does not allow.

    A run can pass every hidden test and still write files the project did not
    ask for. This is the check for that, and it is deliberately about paths, not
    behaviour: allowed patterns and ignored artefacts come from the suite.
    """
    now = file_hashes(root)
    allow = list(layout.get("allow") or [])
    ignore = list(layout.get("ignore") or [])
    created = sorted(p for p in set(now) - set(pristine)
                     if not _matches(p, ignore))
    modified = sorted(p for p in now
                      if p in pristine and now[p] != pristine[p]
                      and not _matches(p, ignore))
    outside = sorted(p for p in created + modified if not _matches(p, allow))
    return {"created": created, "modified": modified, "out_of_layout": outside}


def resolve_pi_binary(pi_binary: str) -> str:
    """Pi runs with the workspace as its cwd, so a --pi-binary given as a relative path is made
    absolute here; a bare command name such as `pi` is left for PATH lookup."""
    if os.sep in pi_binary or (os.altsep and os.altsep in pi_binary):
        return str(Path(pi_binary).resolve())
    return pi_binary


def resolve_extras(remedy: str | None, extensions: list[Path]) -> tuple[list[str], list[Path]]:
    """The remedy units (`--remedy`, names or `preset:<name>`) and a learner's own extensions
    (`--extension`), as (unit names, files to load in order). Unknown names are refused."""
    names: list[str] = []
    for item in (remedy or "").split(","):
        item = item.strip()
        if not item:
            continue
        if item.startswith("preset:"):
            preset = REMEDIES / "presets" / f"{item.removeprefix('preset:')}.json"
            if not preset.is_file():
                known = sorted(f"preset:{q.stem}" for q in (REMEDIES / "presets").glob("*.json"))
                raise SystemExit(f"no preset {item!r}; known: {', '.join(known)}")
            names += json.loads(preset.read_text())
        else:
            names.append(item)
    paths: list[Path] = []
    for name in names:
        path = REMEDIES / f"{name}.ts"
        if not path.is_file():
            known = sorted(str(q.relative_to(REMEDIES).with_suffix(""))
                           for q in REMEDIES.glob("*/*.ts"))
            raise SystemExit(f"no remedy unit {name!r}; known: {', '.join(known)}")
        paths.append(path)
    for path in extensions:
        if not Path(path).is_file():
            raise SystemExit(f"no extension file {path}")
        paths.append(Path(path).resolve())
    return names, paths


def extension_record(paths: list[Path]) -> list[dict]:
    """Each loaded file and its SHA-256, so a record says exactly what ran."""
    return [{"path": str(p), "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()}
            for p in paths]


def pi_argv(
    pi_binary: str,
    profile: Path,
    recorder: Path,
    provider: str,
    model: str,
    prompt: str,
    *,
    extension: Path | None = None,
    session_id: str | None = None,
    session_dir: Path | None = None,
    extras: list[Path] = (),
) -> list[str]:
    session = (
        ["--session-id", session_id, "--session-dir", str(session_dir)]
        if session_id and session_dir
        else []
    )
    extra = ["-e", str(extension)] if extension is not None else []
    for path in extras:
        extra += ["-e", str(path)]
    # The recorder goes last: Pi runs before_provider_request handlers in load
    # order and each may replace the payload, so a recorder placed first would
    # log the messages before the worker appends its facts block. The cost is
    # that a compaction the worker refuses is not visible from here.
    return [
        pi_binary, *FLAGS, "--provider", provider, "--model", model,
        *session, *extra, "-e", str(recorder), prompt,
    ]


def load_variant(suite: Suite, name: str) -> Path:
    """A suite's optional spec variant: prompts plus a workspace overlay."""
    if suite.root is None:
        raise SystemExit(f"suite {suite.name} has no root")
    variants = Path(suite.root) / "spec-variants"
    variant = variants / name
    if not variant.is_dir():
        available = sorted(p.name for p in variants.iterdir() if p.is_dir()) \
            if variants.is_dir() else []
        raise SystemExit(
            f"no spec variant {name!r} in {variants}; "
            f"available: {', '.join(available) or 'none'}")
    return variant


def open_tool_call(trace_lines, now: float) -> tuple[float, str] | None:
    """The oldest tool call still waiting for its result: (seconds open, command).

    A foreground server never returns, so its call stays open; a stall cutoff
    reads this to end the session instead of waiting out the whole deadline.
    """
    pending: list[dict] = []
    for line in trace_lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("type") == "tool_call":
            pending.append(row)
        elif row.get("type") == "tool_result" and pending:
            pending.pop(0)
    if not pending:
        return None
    call = pending[0]
    opened = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00")).timestamp()
    command = (call.get("input") or {}).get("command") or call.get("toolName", "")
    return round(now - opened, 1), command


def run_suite(
    suite: Suite,
    *,
    runs_dir: Path,
    arm: str = "bare",
    profile: Path = PROFILE,
    pi_binary: str = "pi",
    deadline: float | None = None,
    stall: float | None = None,
    single_prompt: bool = False,
    specs: str | None = None,
    extras: list[Path] = (),
) -> Path:
    run = new_run(runs_dir, suite.name)
    workspace = run / "workspace"
    workspace.mkdir()
    shutil.copytree(profile, run / "profile")
    recorder = run / "record-pi.mjs"
    shutil.copy2(RECORDER, recorder)
    if suite.root is not None and (suite.root / "base").is_dir():
        shutil.copytree(suite.root / "base", workspace, dirs_exist_ok=True)
    if suite.start is not None:
        shutil.copytree(suite.start, workspace, dirs_exist_ok=True)
    prompts = list(suite.prompts)
    if specs is not None:
        variant = load_variant(suite, specs)
        for path in sorted(variant.rglob("*")):
            rel = path.relative_to(variant)
            if rel.parts[0] == "prompts" or rel.name == "delete.json":
                continue
            target = workspace / rel
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        deletions = variant / "delete.json"
        if deletions.is_file():
            for rel in json.loads(deletions.read_text()):
                (workspace / rel).unlink(missing_ok=True)
        prompts = [_read_prompt(path)
                   for path in sorted((variant / "prompts").glob("*.md"))]
    pristine = file_hashes(workspace) if suite.layout is not None else None
    prompts = (["\n\n".join(prompts)] if single_prompt else list(prompts))
    (run / "prompt.txt").write_text("\n\n".join(prompts) + "\n")
    trace = run / "trace.jsonl"
    trace.touch()
    sessions = run / "sessions"
    sessions.mkdir()
    provider, model = profile_pin(profile)
    # Record the pinned model so run.json (assembled later, out of this scope) and the
    # scoreboard can name which model produced the run.
    (run / "model.txt").write_text(f"{provider}/{model}\n")
    session_id = str(uuid.uuid4())
    settings = arm_settings(arm)
    env = {
        **os.environ,
        "PI_CODING_AGENT_DIR": str(run / "profile"),
        "MELLUM_TRACE_FILE": str(trace),
    }
    env.pop("VIRTUAL_ENV", None)   # else uv warns in the workspace venv
    for key in ARM_ENV_KEYS:
        env.pop(key, None)
    env.update(settings["env"])
    started = time.monotonic()
    groups: list[int] = []
    leaked: list[dict] = []
    # The sweep runs however the loop ends, including a SIGTERM (main turns it
    # into SystemExit): a stopped run must still end the servers it started.
    try:
        for prompt in prompts:
            remaining = None if deadline is None else deadline - (time.monotonic() - started)
            if remaining is not None and remaining <= 0:
                (run / "deadline").write_text("hit\n")
                break
            # The spec-derived contract scopes itself to the phase this prompt names.
            env["ACCEPTANCE_PROMPT"] = prompt
            argv = pi_argv(
                pi_binary, run / "profile", recorder, provider, model, prompt,
                extension=settings["extension"],
                session_id=session_id, session_dir=sessions, extras=extras,
            )
            try:
                # No stdin: Pi with -p appends piped stdin to its prompt.
                child = subprocess.Popen(argv, cwd=workspace, env=env, stdin=subprocess.DEVNULL,
                                         start_new_session=True)
                groups.append(child.pid)
            except FileNotFoundError:
                raise SystemExit(f"pi not found: {pi_binary}; install Pi before running a suite")
            ended = wait_or_stall(child, run, trace, remaining, stall)
            if ended:
                break
    finally:
        for pgid in groups:
            leaked.extend({"pid": pid, "pgid": pgid, "command": command}
                          for pid, command in sweep_group(pgid))
        swept = {entry["pid"] for entry in leaked}
        leaked.extend({"pid": pid, "pgid": None, "command": command}
                      for pid, command in sweep_workspace(workspace) if pid not in swept)
    (run / "leaked.json").write_text(json.dumps(leaked, indent=2) + "\n")
    if pristine is not None and suite.layout is not None:
        (run / "layout.json").write_text(
            json.dumps(layout_report(workspace, pristine, suite.layout), indent=2) + "\n")
    if grader_touched(run, suite):
        (run / "contaminated").write_text("grader touched\n")
    return run


def wait_or_stall(child, run: Path, trace: Path, remaining: float | None,
                  stall: float | None) -> str | None:
    """Wait for one Pi child; end it at the deadline, or when a command stalls.

    Returns "deadline" or "stalled" when the session was ended, else None.
    """
    if stall is None:
        try:
            child.wait(timeout=remaining)
            return None
        except subprocess.TimeoutExpired:
            reason = "deadline"
    else:
        until = None if remaining is None else time.monotonic() + remaining
        reason = None
        while child.poll() is None:
            if until is not None and time.monotonic() >= until:
                reason = "deadline"
                break
            open_call = open_tool_call(trace.read_text().splitlines(), time.time())
            if open_call and open_call[0] >= stall:
                (run / "stalled").write_text(json.dumps(
                    {"seconds": open_call[0], "limit": stall, "command": open_call[1]}) + "\n")
                reason = "stalled"
                break
            time.sleep(1)
        if reason is None:
            return None
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()
    if reason == "deadline":
        (run / "deadline").write_text("hit\n")
    return reason


def grader_touched(run: Path, suite: Suite) -> bool:
    if suite.canary is None:
        return False
    text = (Path(run) / "trace.jsonl").read_text(errors="ignore")
    return suite.canary in text or f"suites/{suite.name}" in text


def grade_env(workspace: Path) -> dict[str, str]:
    """A grader subprocess's environment: the workspace on PYTHONPATH, and no
    VIRTUAL_ENV — uv warns when it points at a venv other than the run's."""
    return {k: v for k, v in os.environ.items()
            if k != "VIRTUAL_ENV"} | {"PYTHONPATH": str(workspace)}


def grade(workspace: Path) -> list[tuple[str, bool, str]]:
    workspace = Path(workspace)
    (workspace / "pyrefly.toml").write_text(
        'project-includes = [\n    "**/*.py",\n]\n'
        'project-excludes = [\n    "tests/**",\n]\n')
    def tool(name: str, *args: str) -> list[str]:
        if (workspace / "pyproject.toml").is_file():
            return ["uv", "run", "--with", name, name, *args]
        return ["uvx", name, *args]

    commands = (
        ("ruff", tool("ruff", "check", "--select", "F,E9", "--extend-exclude", "tests", "--extend-exclude", "grader_tests", ".")),
        ("pyrefly", tool("pyrefly", "check", ".")),
        ("complexipy", tool("complexipy", "--max-complexity-allowed", "10",
                            "--exclude", "tests", "--exclude", "grader_tests", ".")),
    )
    results = []
    for name, command in commands:
        result = subprocess.run(
            command, cwd=workspace, capture_output=True, text=True, check=False,
            env=grade_env(workspace),
        )
        output = [line for line in (result.stdout + result.stderr).splitlines()
                  if line.strip()]
        results.append((name, result.returncode == 0, output[0] if output else ""))
    return results


def qualify(suite: Suite) -> tuple[bool, dict[str, bool]]:
    if suite.root is None:
        raise SystemExit(f"suite {suite.name} has no root")
    results: dict[str, bool] = {}
    for name in ("known-good", "known-broken"):
        fixture = Path(suite.root) / "fixtures" / name
        if not fixture.is_dir():
            raise SystemExit(f"missing fixture: {fixture}")
        workspace = Path(tempfile.mkdtemp(prefix=f"mellum-{suite.name}-{name}-"))
        try:
            shutil.copytree(Path(suite.root) / "base", workspace, dirs_exist_ok=True)
            shutil.copytree(fixture, workspace, dirs_exist_ok=True)
            passed, _ = score_workspace(workspace, suite)
            results[name] = passed
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
    return results["known-good"] and not results["known-broken"], results


def _trace_time(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# A blocked tool call never reaches the recorder: the worker's guard stops the
# event chain first, so there is no tool_call row. What the trace does carry is
# the refusal as the model saw it, in a toolResult message. This phrase is that
# refusal's first sentence; the guard test pins it on the extension side.
SERVER_REFUSAL = "starts a server in the foreground"


def report(run: Path) -> dict:
    rows = [
        json.loads(line)
        for line in (Path(run) / "trace.jsonl").read_text().splitlines()
        if line.strip()
    ]
    final = ""
    inputs = []
    outputs = []
    times = []
    empties: list[int] = []
    guard_blocks = 0
    for index, row in enumerate(rows):
        if (when := _trace_time(row.get("timestamp"))) is not None:
            times.append(when)
        if row.get("type") != "message_end":
            continue
        message = row.get("message") or {}
        usage = message.get("usage") or {}
        value = usage.get("input", usage.get("prompt_tokens"))
        if isinstance(value, (int, float)):
            inputs.append(value)
        value = usage.get("output", usage.get("completion_tokens"))
        if isinstance(value, (int, float)):
            outputs.append(value)
        if (message.get("role") == "toolResult"
                and SERVER_REFUSAL in str(message.get("content"))):
            guard_blocks += 1
        if message.get("role") != "assistant":
            continue
        blocks = message.get("content") or []
        said = any(b.get("type") == "text" and (b.get("text") or "").strip()
                   for b in blocks)
        called = any(b.get("type") == "toolCall" for b in blocks)
        if not said and not called:
            empties.append(index)
            continue
        for block in blocks:
            if block.get("type") == "text" and block.get("text"):
                final = block["text"]
                break
    # A nudge continues a run: the empty turn is followed by another request in
    # the same Pi process. Medium and hard start one process per prompt, so an
    # empty turn that ends a prompt is an empty final, not a nudge, however many
    # requests the next prompt makes.
    starts = [index for index, row in enumerate(rows)
              if row.get("type") == "instance_start"]

    def segment_end(at: int) -> int:
        later = [start for start in starts if start > at]
        return later[0] if later else len(rows)

    continued = sum(
        any(later.get("type") == "provider_request"
            for later in rows[at + 1:segment_end(at)])
        for at in empties)
    return {
        "requests": sum(row.get("type") == "provider_request" for row in rows),
        "turns": sum(row.get("type") == "provider_request" for row in rows),
        "tool_calls": sum(row.get("type") == "tool_call" for row in rows),
        "tool_errors": sum(
            row.get("type") == "tool_result" and row.get("isError") for row in rows),
        "final_reply": final,
        "context": max(inputs) if inputs else None,
        "output_tokens": sum(outputs) if outputs else None,
        "wall": round((times[-1] - times[0]).total_seconds(), 3) if len(times) > 1 else None,
        "nudges": continued,
        "empty_finals": len(empties) - continued,
        "guard_blocks": guard_blocks,
        # Assistant turns the model was sent back with its reasoning as <think>
        # text (a serving fault; the largest history in the session).
        "reasoning_as_text": max(
            (sum("<think>" in str(m.get("content") or "")
                 for m in (row.get("payload") or {}).get("messages") or []
                 if m.get("role") == "assistant")
             for row in rows if row.get("type") == "provider_request"),
            default=0),
        # Times Pi compacted a context that neared its window, losing detail.
        "compactions": sum(row.get("type") == "before_compact" for row in rows),
    }



def score(run: Path, suite: Suite) -> tuple[bool, str]:
    return score_workspace(Path(run) / "workspace", suite)


def score_details(run: Path, suite: Suite) -> tuple[bool, str, list[str], bool]:
    return score_workspace_details(Path(run) / "workspace", suite)


def check_groups(expected, missing) -> dict[str, dict[str, int]]:
    """Count the expected checks per grader module, missing and total."""
    groups: dict[str, dict[str, int]] = {}
    for test in expected:
        module = test.split("::")[0].rsplit("/", 1)[-1]
        groups.setdefault(module, {"missing": 0, "total": 0})["total"] += 1
    for test in missing:
        module = test.split("::")[0].rsplit("/", 1)[-1]
        groups[module]["missing"] += 1
    return groups


def score_workspace_details(
    workspace: Path, suite: Suite
) -> tuple[bool, str, list[str], bool]:
    workspace = Path(workspace)
    target = workspace / "grader_tests"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(suite.tests, target)
    command = (
        ["uv", "run", "--with", "pytest", "pytest", "-q", "-rA", "grader_tests"]
        if (workspace / "pyproject.toml").is_file()
        else ["uvx", "pytest", "-q", "-rA", "grader_tests"]
    )
    result = subprocess.run(
        command, cwd=workspace, capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONPATH": str(workspace)},
    )
    output = (result.stdout + result.stderr).strip()
    # A collection error (or no tests collected) means the hidden checks never
    # executed -- usually because the workspace lacks a module they import. That
    # is still a failure, but it must not read as "every check failed".
    checks_ran = result.returncode in (0, 1) and "errors during collection" not in output
    missing = sorted(test for test in suite.expected if f"PASSED {test}" not in output)
    lines = output.splitlines()[-20:]
    if missing:
        lines.append("missing expected tests: " + ", ".join(missing))
    return result.returncode == 0 and not missing, "\n".join(lines), missing, checks_ran


def score_workspace(workspace: Path, suite: Suite) -> tuple[bool, str]:
    passed, tail, _missing, _ran = score_workspace_details(workspace, suite)
    return passed, tail


def _run_sessions(
    suite: Suite,
    *,
    runs_dir: Path,
    pi_binary: str,
    repeat: int,
    grade_run: bool,
    deadline: float | None,
    arm: str = "bare",
    single_prompt: bool = False,
    specs: str | None = None,
    profile: Path = PROFILE,
    stall: float | None = None,
    remedies: list[str] = (),
    extras: list[Path] = (),
) -> list[tuple]:
    results = []
    for _ in range(repeat):
        run_dir = run_suite(suite, runs_dir=runs_dir, pi_binary=pi_binary,
                            deadline=deadline, arm=arm,
                            single_prompt=single_prompt, specs=specs,
                            profile=profile, stall=stall, extras=extras)
        grades = grade(run_dir / "workspace") if grade_run else []
        tests_passed, tail, missing, checks_ran = score_details(run_dir, suite)
        failed_checks = len(missing)
        quality_ok = all(
            ok for name, ok, _ in grades if name in {"ruff", "complexipy"}
        ) if grades else True
        contaminated = (run_dir / "contaminated").exists()
        metrics = report(run_dir)
        over = record_failures(metrics, suite.record)
        passed = tests_passed and quality_ok and not contaminated and not over
        leaked_file = run_dir / "leaked.json"
        if leaked_file.is_file():
            metrics["leaked"] = json.loads(leaked_file.read_text())
        layout_file = run_dir / "layout.json"
        if layout_file.is_file():
            metrics["out_of_layout"] = json.loads(layout_file.read_text())["out_of_layout"]
        model_file = run_dir / "model.txt"
        record = {
            "suite": suite.name,
            "arm": arm,
            "model": model_file.read_text().strip() if model_file.is_file() else None,
            "remedies": list(remedies),
            "extensions": extension_record(list(extras)),
            "single_prompt": single_prompt,
            "specs": specs,
            "strip_thinking": arm_settings(arm)["env"].get("MELLUM_STRIP_THINKING") == "1",
            "machine": machine_label(),
            "deadline": deadline,
            "stall": stall,
            "stalled": (json.loads((run_dir / "stalled").read_text())
                        if (run_dir / "stalled").exists() else None),
            "passed": passed,
            "tests_passed": tests_passed,
            "quality_ok": quality_ok,
            "contaminated": contaminated,
            "failed_checks": failed_checks,
            "checks_ran": checks_ran,
            "missing_checks": missing,
            "check_groups": check_groups(suite.expected, missing),
            "record_failures": over,
            **{key: value for key, value in metrics.items()
               if key != "final_reply"},
        }
        (run_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n")
        results.append((run_dir, passed, tail, grades, metrics,
                        tests_passed, quality_ok, contaminated))
    return results


def _print_task(
    suite: Suite, results: list[tuple], repeat: int
) -> int:
    for index, (run_dir, passed, tail, grades, counts, tests_passed,
                quality_ok, contaminated) in enumerate(results, 1):
        print(_line(suite, run_dir, passed, counts, repeat, index,
                    tests_passed, quality_ok, contaminated))
        _print_grades(grades)
        if not passed:
            print(tail, file=sys.stderr)
    ok = sum(1 for result in results if result[1])
    if repeat > 1:
        print(f"{suite.name}: {ok}/{repeat} sessions passed")
    return ok


def run_suites(
    names: list[str],
    *,
    suites_dir: Path = SUITES,
    runs_dir: Path = RUNS,
    pi_binary: str = "pi",
    grade_run: bool = False,
    repeat: int = 1,
    deadline: float | None = 600,
    arm: str = "bare",
    single_prompt: bool = False,
    specs: str | None = None,
    profile: Path = PROFILE,
    stall: float | None = None,
    remedies: list[str] = (),
    extras: list[Path] = (),
) -> tuple[int, int]:
    # Run easiest first and hardest last, so a slow hard suite never blocks the
    # quicker ones; unknown suites keep alphabetical order after the known tiers.
    order = {"easy": 0, "medium": 1, "hard": 2}
    available = sorted(
        (
            path.name
            for path in Path(suites_dir).iterdir()
            if ((path / "grader").is_dir() or (path / "tests").is_dir())
            and ((path / "task.md").exists() or (path / "prompts").is_dir())
        ),
        key=lambda name: (order.get(name, len(order)), name),
    )
    if "all" in names:
        names = available
    missing = [name for name in names if name not in available]
    if missing:
        raise SystemExit(f"no suite named {', '.join(missing)} in {suites_dir}; "
                         f"available: {', '.join(available)}")
    suites_passed = sessions_passed = sessions_total = 0
    for name in names:
        suite = load_suite(suites_dir, name)
        results = _run_sessions(
            suite, runs_dir=runs_dir, pi_binary=pi_binary,
            repeat=repeat, grade_run=grade_run, deadline=deadline, arm=arm,
            single_prompt=single_prompt, specs=specs, profile=profile, stall=stall,
            remedies=remedies, extras=extras,
        )
        sessions_passed += _print_task(suite, results, repeat)
        sessions_total += len(results)
        if all(result[1] for result in results):
            suites_passed += 1
    print(f"{suites_passed}/{len(names)} suites passed "
          f"({sessions_passed}/{sessions_total} sessions)")
    return suites_passed, len(names)


def _line(
    suite: Suite,
    run_dir: Path,
    passed: bool,
    counts: dict,
    repeat: int = 1,
    index: int = 1,
    tests_passed: bool = True,
    quality_ok: bool = True,
    contaminated: bool = False,
) -> str:
    tag = suite.name + (f" [{index}/{repeat}]" if repeat > 1 else "")
    n_text = f"n={repeat}; " if repeat == 1 else ""
    deadline = (" deadline" if (Path(run_dir) / "deadline").exists()
                else " stalled" if (Path(run_dir) / "stalled").exists() else "")
    label = "CONTAMINATED" if contaminated else ("PASS" if passed else "FAIL")
    notes = []
    if not quality_ok:
        notes.append("quality FAIL")
    if contaminated:
        notes.append("grader touched")
    note = ("; " + ", ".join(notes)) if notes else ""
    nudges = counts.get("nudges")
    fires = "" if nudges is None else f", {nudges} nudges"
    return (f"{tag}: {label} ({n_text}run {run_dir}; "
            f"{counts['requests']} requests, {counts['tool_calls']} tool calls, "
            f"{counts['tool_errors']} tool errors{fires}{deadline}{note})")


def _print_grades(grades: list[tuple[str, bool, str]]) -> None:
    for name, ok, detail in grades:
        label = "pyrefly (advisory)" if name == "pyrefly" else name
        print(f"{label}: {'PASS' if ok else 'FAIL'}" + (f" ({detail})" if not ok else ""))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one eval suite or all of them")
    qualify_p = sub.add_parser("qualify", help="prove a suite's grader both ways")
    qualify_p.add_argument("--suite", required=True)
    qualify_p.add_argument("--suites-dir", type=Path, default=SUITES)
    run.add_argument("--suite", required=True, help="a suite name, or all")
    run.add_argument("--suites-dir", type=Path, default=SUITES)
    run.add_argument("--runs-dir", type=Path, default=RUNS)
    run.add_argument("--pi-binary", default="pi")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--grade", action="store_true")
    run.add_argument("--repeat", type=int, default=1)
    run.add_argument("--deadline", type=float, default=600)
    run.add_argument("--arm", choices=ARMS, default="bare")
    run.add_argument("--remedy", default=None, metavar="LIST",
                     help="remedy units to load on top of the arm: comma-separated names "
                          "(guard/break-repeat-loops) or preset:<name>")
    run.add_argument("--extension", type=Path, action="append", default=[], metavar="PATH",
                     help="a Pi extension of your own to load (repeatable)")
    run.add_argument("--stall", type=float, default=None, metavar="SECONDS",
                     help="end a session as stalled when one tool call has run this long "
                          "with no result (a foreground server); off by default")
    run.add_argument("--profile", type=Path, default=PROFILE,
                     help="the Pi profile directory (models.json) the sessions use; "
                          "default the pinned llama.cpp profile")
    run.add_argument("--single-prompt", action="store_true",
                     help="send the suite's prompts as one brief instead of steps")
    run.add_argument("--specs", metavar="VARIANT", default=None, choices=["joined", "split"],
                     help="use the suite's spec variant: one joined roadmap, or one file per phase")
    return parser


def main(argv: list[str] | None = None) -> int:
    # A stopped run (SIGTERM, as /lesson sends) unwinds normally, so its sweep runs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "qualify":
        suite = load_suite(args.suites_dir, args.suite)
        ok, results = qualify(suite)
        for name, passed in results.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
        print(f"{suite.name}: {'QUALIFIED' if ok else 'NOT QUALIFIED'}")
        return 0 if ok else 1

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    remedies, extras = resolve_extras(args.remedy, args.extension)
    args.pi_binary = resolve_pi_binary(args.pi_binary)
    # Pi runs with the workspace as its cwd, so every path handed to it must be absolute.
    args.runs_dir = Path(args.runs_dir).resolve()
    args.profile = Path(args.profile).resolve()
    args.suites_dir = Path(args.suites_dir).resolve()
    if args.suite == "all":
        run_suites(["all"], suites_dir=args.suites_dir, runs_dir=args.runs_dir,
                   pi_binary=args.pi_binary, grade_run=args.grade,
                   repeat=args.repeat, deadline=args.deadline, arm=args.arm,
                   single_prompt=args.single_prompt, specs=args.specs,
                   profile=args.profile, stall=args.stall,
                   remedies=remedies, extras=extras)
        return 0

    suite = load_suite(args.suites_dir, args.suite)
    provider, model = profile_pin(args.profile)
    if args.dry_run:
        settings = arm_settings(args.arm)
        if args.specs:
            variant = load_variant(suite, args.specs)
            prompt = _read_prompt(sorted((variant / "prompts").glob("*.md"))[0])
        else:
            prompt = suite.prompt
        print(shlex.join(pi_argv(args.pi_binary, args.profile, RECORDER, provider,
                                 model, prompt,
                                 extension=settings["extension"], extras=extras)))
        return 0
    results = _run_sessions(
        suite, runs_dir=args.runs_dir, pi_binary=args.pi_binary,
        repeat=args.repeat, grade_run=args.grade, deadline=args.deadline,
        arm=args.arm, single_prompt=args.single_prompt, specs=args.specs,
        profile=args.profile, stall=args.stall,
        remedies=remedies, extras=extras,
    )
    _print_task(suite, results, args.repeat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
