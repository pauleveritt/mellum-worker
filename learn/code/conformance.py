#!/usr/bin/env python3
"""The conformance check (F.5, ported from LC.39's per-rental check): may this host's sessions count?

It checks the live llama-server against a pin card (`host/pins.json` for the Mac, `host/pod-pins.json`
for a pod) and writes a host card. A counted harness session needs a card that passed, for the server
that is live (`harness.host_gate`). A pod's card has its own digest: its numbers do not pool with the Mac's.

    uv run python learn/code/conformance.py --out <runs-dir>/host-card.json --pi-binary ~/.local/bin/pi
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HOST = Path(__file__).resolve().parent / "host"
PINS = HOST / "pins.json"
POD_PINS = HOST / "pod-pins.json"
SCHEMA = "mellum-host-card/1"
# Parts of the server command that may differ between restarts of the same configuration.
VARIABLE_FLAGS = {"-m", "--port", "-t", "-tb", "--log-file"}


def load_pins(path: Path = PINS) -> dict:
    pins = json.loads(Path(path).read_text())
    for section in ("build", "weights", "server", "numerics", "tooling"):
        if section not in pins:
            raise ValueError(f"pin card is missing {section}")
    if pins["server"]["flash_attention"] != "on":
        raise ValueError("pin card must set server.flash_attention to on; auto may resolve differently")
    return pins


def card_pins(card: dict) -> dict:
    """The pin card a host card was made for: one file in `host/`; a card that names none is the Mac's."""
    name = card.get("pins_file", PINS.name)
    if Path(name).name != name or not (HOST / name).is_file():
        raise ValueError(f"host card names an unknown pin card {name!r}")
    return load_pins(HOST / name)


def pins_digest(pins: dict) -> str:
    return hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def server_argv(pins: dict, *, binary: str, model: str, port: int, threads: int, log: str) -> list[str]:
    """The LC.34–LC.38 server command the pin card describes."""
    s = pins["server"]
    argv = [binary, "-m", model, "-a", pins["weights"]["alias"], "--host", s["host"], "--port", str(port),
            "-c", str(s["context"]), "-np", str(s["parallel"])]
    if not s["kv_unified"]:
        argv.append("--no-kv-unified")
    if s["jinja"]:
        argv.append("--jinja")
    argv += ["-fa", s["flash_attention"]]
    if s["continuous_batching"]:
        argv.append("--cont-batching")
    argv += ["-t", str(threads), "-tb", str(threads), "-b", str(s["batch"]), "-ub", str(s["microbatch"]),
             "-ctk", s["cache_type_k"], "-ctv", s["cache_type_v"], "-ngl", str(s["gpu_layers"]),
             "-lv", str(s["log_verbosity"]), "--log-file", log]
    return argv


def pinned_flags(argv: list[str]) -> list[str]:
    """A server command without the binary and the parts that may vary (VARIABLE_FLAGS and their values)."""
    kept, at = [], 1
    while at < len(argv):
        if argv[at] in VARIABLE_FLAGS:
            at += 2
            continue
        kept.append(argv[at])
        at += 1
    return kept


def flags_problems(argv: list[str], pins: dict) -> list[str]:
    """The launched server command must carry every pinned flag with its pinned value."""
    expected = server_argv(pins, binary="_", model="_", port=0, threads=0, log="_")
    problems, at = [], 1
    while at < len(expected):
        flag = expected[at]
        takes_value = at + 1 < len(expected) and not expected[at + 1].startswith("-")
        if flag not in argv:
            problems.append(f"server command lacks {flag}")
        elif takes_value and flag not in VARIABLE_FLAGS:
            index = argv.index(flag) + 1
            given = argv[index] if index < len(argv) else None
            if given != expected[at + 1]:
                problems.append(f"server command has {flag} {given}, pinned {expected[at + 1]}")
        at += 2 if takes_value else 1
    allowed = {flag for flag in expected[1:] if _is_flag(flag)} | VARIABLE_FLAGS
    given = [flag for flag in argv[1:] if _is_flag(flag)]
    for flag in sorted(set(given)):
        if flag not in allowed:
            problems.append(f"server command has unpinned flag {flag}")
        elif given.count(flag) > 1:
            problems.append(f"server command repeats {flag}; llama.cpp takes the last")
    return problems


def _is_flag(token: str) -> bool:
    return token.startswith("-") and not token.lstrip("-").replace(".", "", 1).isdigit()


def identity_problems(props: dict, slots: list[dict], pins: dict) -> list[str]:
    problems = []
    if props.get("build_info") != pins["build"]["build_info"]:
        problems.append(f"build_info {props.get('build_info')!r} is not {pins['build']['build_info']!r}")
    if not str(props.get("model_path", "")).endswith(pins["weights"]["file"]):
        problems.append(f"model_path {props.get('model_path')!r} is not the pinned file")
    if len(slots) != pins["server"]["parallel"]:
        problems.append(f"{len(slots)} slots, pinned {pins['server']['parallel']}")
    for slot in slots:
        if slot.get("n_ctx") != pins["server"]["slot_context"]:
            problems.append(f"slot {slot.get('id')} n_ctx {slot.get('n_ctx')}, pinned {pins['server']['slot_context']}")
    return problems


PPL = re.compile(r"Final estimate: PPL = ([0-9]+(?:\.[0-9]+)?)")
CHUNK = re.compile(r"\[(\d+)\](nan|-?inf|[0-9]+(?:\.[0-9]+)?)")
VERSION = re.compile(r"\d+\.\d+\.\d+")


def parse_perplexity(text: str) -> float:
    match = PPL.search(text)
    if not match:
        raise ValueError("llama-perplexity printed no final estimate")
    return float(match[1])


def perplexity_chunks(text: str) -> list[float | None]:
    """Per-chunk values llama-perplexity prints ([1]14.46,[2]nan,...); a non-finite chunk is None."""
    return [float(value) if value not in ("nan", "inf", "-inf") else None for _, value in CHUNK.findall(text)]


def _item(passed: bool, detail) -> dict:
    return {"passed": bool(passed), "detail": detail}


def _reading(text: str) -> dict:
    chunks = perplexity_chunks(text)
    try:
        return {"perplexity": parse_perplexity(text), "chunks": chunks}
    except ValueError as error:
        return {"perplexity": None, "chunks": chunks, "nan_chunks": sum(c is None for c in chunks),
                "error": str(error)}


def numerics_item(gpu_text: str, cpu_text: str, tolerance: float) -> dict:
    """The GPU against the CPU on the same build and weights: both finite, within tolerance (F.5)."""
    gpu, cpu = _reading(gpu_text), _reading(cpu_text)
    if gpu["perplexity"] is None or cpu["perplexity"] is None:
        return _item(False, {"gpu": gpu, "cpu": cpu, "tolerance": tolerance})
    drift = abs(gpu["perplexity"] - cpu["perplexity"]) / cpu["perplexity"]
    return _item(drift <= tolerance, {"gpu": gpu, "cpu": cpu, "relative_drift": round(drift, 6),
                                      "tolerance": tolerance})


def _get(endpoint: str, route: str):
    with urllib.request.urlopen(endpoint + route, timeout=30) as response:
        return json.loads(response.read())


def _chat(endpoint: str, body: dict, timeout: float = 600) -> tuple[int, dict]:
    request = urllib.request.Request(endpoint + "/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, {}
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        return 0, {"error": str(error)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _identity(pins, props, slots, model, server_command):
    problems = identity_problems(props, slots, pins) + flags_problems(list(server_command), pins)
    if sha256_file(model) != pins["weights"]["sha256"]:
        problems.append("model file hash is not the pinned sha256")
    return _item(not problems, {"problems": problems, "build_info": props.get("build_info"),
                                "chat_template_sha256": hashlib.sha256(
                                    str(props.get("chat_template", "")).encode()).hexdigest()})


def _capacity(pins, endpoint):
    words = int(pins["server"]["slot_context"] * 0.85)
    results = []
    for slot in range(pins["server"]["parallel"]):
        status, reply = _chat(endpoint, {"messages": [{"role": "user", "content": "hello " * words}],
                                         "max_tokens": 1, "id_slot": slot}, timeout=1800)
        results.append({"slot": slot, "status": status, "prompt_tokens": reply.get("usage", {}).get("prompt_tokens", 0)})
    passed = all(r["status"] == 200 and r["prompt_tokens"] >= 0.8 * pins["server"]["slot_context"] for r in results)
    return _item(passed, results)


def _protocol(endpoint):
    tool = {"type": "function", "function": {"name": "read_file", "description": "Read a file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}
    status, reply = _chat(endpoint, {"messages": [{"role": "user", "content": "Read the file README.md."}],
                                     "tools": [tool], "tool_choice": "required", "max_tokens": 512})
    message = (reply.get("choices") or [{}])[0].get("message", {})
    tool_call = status == 200 and bool(message.get("tool_calls"))
    reasoning = bool(message.get("reasoning_content"))
    status_limit, limited = _chat(endpoint, {"messages": [{"role": "user", "content": "Count from one to fifty."}],
                                             "max_tokens": 16})
    honoured = status_limit == 200 and limited.get("usage", {}).get("completion_tokens", 10**9) <= 16
    return _item(tool_call and reasoning and honoured,
                 {"tool_call": tool_call, "reasoning_split": reasoning, "max_tokens_honoured": honoured}), limited


def _stability(endpoint):
    statuses = [_chat(endpoint, {"messages": [{"role": "user", "content": "Say ok."}], "max_tokens": 4})[0]
                for _ in range(10)]
    return _item(all(s == 200 for s in statuses), {"statuses": statuses})


def tool_build(binary) -> str | None:
    """A llama.cpp tool's build as /props names it (b12110-cd959bae9), from its --version."""
    try:
        out = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"build (\d+), commit ([0-9a-f]+)", out.stdout + out.stderr)
    return f"b{match[1]}-{match[2]}" if match else None


def _numerics(pins, perplexity_binary, model, threads=None):
    n = pins["numerics"]
    text = HOST / n["text"]
    if sha256_file(text) != n["text_sha256"]:
        return _item(False, {"error": "perplexity text is not the pinned one"})
    build = tool_build(perplexity_binary)
    if build != pins["build"]["build_info"]:
        return _item(False, {"error": f"llama-perplexity is {build}, not the server's {pins['build']['build_info']}"})
    outputs = {}
    for name, layers in (("gpu", "999"), ("cpu", "0")):
        argv = [str(perplexity_binary), "-m", str(model), "-f", str(text), "-c", str(n["context"]), "-ngl", layers]
        if threads:
            argv += ["-t", str(threads), "-tb", str(threads)]
        try:
            out = subprocess.run(argv, capture_output=True, text=True, timeout=3600)
            outputs[name] = out.stdout + out.stderr
        except (OSError, subprocess.TimeoutExpired) as error:
            outputs[name] = str(error)
    return numerics_item(outputs["gpu"], outputs["cpu"], n["tolerance"])


def tool_versions(pi_binary: str, path: str | None = None) -> dict[str, str | None]:
    """Versions of the session's tools: Pi as the harness runs it, node and uv from PATH."""
    versions = {}
    for name, binary in (("pi", pi_binary), ("node", shutil.which("node", path=path)),
                         ("uv", shutil.which("uv", path=path))):
        try:
            out = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=30)
            match = VERSION.search(out.stdout + out.stderr) if out.returncode == 0 else None
        except (OSError, TypeError, subprocess.TimeoutExpired):
            match = None
        versions[name] = match.group() if match else None
    return versions


def server_command(port: int) -> list[str] | None:
    """The argv of the process listening on a loopback port, or None when nothing is."""
    try:
        out = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                             capture_output=True, text=True, timeout=30).stdout.split()
        if not out:
            return None
        command = subprocess.run(["ps", "-ww", "-o", "command=", "-p", out[0]],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    return shlex.split(command) if command else None


def machine_label() -> str:
    """The machine as run.json names it (chip and memory), never its network name."""
    from harness import machine_label as label
    return label()


def check(pins: dict, endpoint: str, *, model: Path, perplexity_binary: Path, server_command: list[str],
          pi_binary: str, out: Path, tool_path: str | None = None, pins_file: str = PINS.name,
          threads: int | None = None) -> dict:
    started = time.monotonic()
    props, slots = _get(endpoint, "/props"), _get(endpoint, "/slots")
    items = {"identity": _identity(pins, props, slots, model, server_command), "capacity": _capacity(pins, endpoint)}
    items["protocol"], sample = _protocol(endpoint)
    timings = sample.get("timings", {})
    items["throughput"] = _item(True, {"prompt_per_second": timings.get("prompt_per_second"),
                                       "predicted_per_second": timings.get("predicted_per_second")})
    items["stability"] = _stability(endpoint)
    items["numerics"] = _numerics(pins, perplexity_binary, model, threads)
    found = tool_versions(pi_binary, tool_path)
    items["tooling"] = _item(found == pins["tooling"], {"expected": pins["tooling"], "found": found})
    card = {"schema": SCHEMA, "passed": all(item["passed"] for item in items.values()),
            "pins_digest": pins_digest(pins), "pins_file": pins_file, "items": items, "endpoint": endpoint,
            "build_info": props.get("build_info"), "model_path": props.get("model_path"),
            "slots": [slot.get("n_ctx") for slot in slots], "server_command": list(server_command),
            "machine": machine_label(),
            "checked_at": datetime.now(UTC).isoformat(), "check_seconds": round(time.monotonic() - started, 3)}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(card, indent=2) + "\n")
    return card


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True, help="where to write the host card")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8001")
    parser.add_argument("--pi-binary", default="pi")
    parser.add_argument("--perplexity-binary", default=shutil.which("llama-perplexity") or "llama-perplexity")
    parser.add_argument("--pins", type=Path, default=PINS, help="the pin card in host/ (default: the Mac's)")
    parser.add_argument("--threads", type=int, default=None,
                        help="llama-perplexity's threads; on a pod, the cgroup's CPUs, not nproc")
    args = parser.parse_args(argv)
    port = int(args.endpoint.rsplit(":", 1)[1].split("/")[0])
    command = server_command(port)
    if command is None or "-m" not in command:
        raise SystemExit(f"no llama-server command found listening on port {port}")
    pi = shutil.which(str(Path(args.pi_binary).expanduser())) or str(Path(args.pi_binary).expanduser())
    card = check(load_pins(args.pins), args.endpoint, model=Path(command[command.index("-m") + 1]),
                 perplexity_binary=Path(args.perplexity_binary), server_command=command, pi_binary=pi,
                 out=args.out, pins_file=Path(args.pins).name, threads=args.threads)
    for name, item in card["items"].items():
        print(f"{name}: {'PASS' if item['passed'] else 'FAIL'}")
    print(f"host card {'PASSED' if card['passed'] else 'FAILED'}: {args.out}")
    return 0 if card["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
