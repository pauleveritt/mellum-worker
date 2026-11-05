"""Per-rental conformance check (LC.39): may this host's sessions count?

Runs on the host itself, against its own llama-server, and writes host-card.json.
A host that fails any item contributes no counted session
(docs/superpowers/specs/2026-11-05-portable-floor-design.md §2).
"""
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import rig
from isolation import isolation_probe

PPL_TEXT = rig.REPO / "scripts/rig/ppl.txt"
PPL = re.compile(r"Final estimate: PPL = ([0-9]+(?:\.[0-9]+)?)")


def parse_perplexity(text: str) -> float:
    match = PPL.search(text)
    if not match:
        raise ValueError("llama-perplexity printed no final estimate")
    return float(match[1])


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _item(passed: bool, detail) -> dict:
    return {"passed": bool(passed), "detail": detail}


def _identity(pins, endpoint, model, reference_template):
    props, slots = _get(endpoint, "/props"), _get(endpoint, "/slots")
    problems = identity_problems(props, slots, pins)
    if _sha256(model) != pins["weights"]["sha256"]:
        problems.append("model file hash is not the pinned sha256")
    template = hashlib.sha256(str(props.get("chat_template", "")).encode()).hexdigest()
    if reference_template is not None and template != reference_template:
        problems.append("chat template hash differs from the reference host")
    return _item(not problems, {"problems": problems, "build_info": props.get("build_info"),
                                "chat_template_sha256": template, "slots": len(slots)})


def _capacity(pins, endpoint):
    words = int(pins["server"]["slot_context"] * 0.85)
    results = []
    for slot in range(pins["server"]["parallel"]):
        status, reply = _chat(endpoint, {"messages": [{"role": "user", "content": "hello " * words}],
                                         "max_tokens": 1, "id_slot": slot}, timeout=1800)
        prompt = reply.get("usage", {}).get("prompt_tokens", 0)
        results.append({"slot": slot, "status": status, "prompt_tokens": prompt})
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


def _numerics(perplexity_binary, model, reference_ppl, tolerance):
    argv = [str(perplexity_binary), "-m", str(model), "-f", str(PPL_TEXT), "-c", "2048", "-ngl", "999"]
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=3600)
        value = parse_perplexity(out.stdout + out.stderr)
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        return _item(False, {"error": str(error)})
    if reference_ppl is None:
        return _item(True, {"perplexity": value, "role": "reference", "text_sha256": _sha256(PPL_TEXT)})
    drift = abs(value - reference_ppl) / reference_ppl
    return _item(drift <= tolerance, {"perplexity": value, "reference": reference_ppl, "relative_drift": drift,
                                      "tolerance": tolerance, "role": "compared", "text_sha256": _sha256(PPL_TEXT)})


def _tooling(pins, prefix):
    boot = pins["bootstrap"]
    expected = {"node": boot["node"]["version"], "pi": boot["pi"].rsplit("@", 1)[-1], "uv": boot["uv"],
                "python": boot["python"]}
    found = rig.tool_versions(prefix)
    return _item(found == expected, {"expected": expected, "found": found})


def _isolation(session_user, protected, pids):
    if session_user is None:
        return _item(True, {"uncontained": True})
    result = isolation_probe(session_user, list(protected), list(pids))
    return _item(result["ok"], result)


def check(pins: dict, endpoint: str, *, perplexity_binary: Path, model: Path, reference_ppl: float | None,
          tolerance: float, host: dict, out: Path, prefix: str | None, session_user: str | None = None,
          protected: tuple = (), pids: tuple = (), reference_template: str | None = None) -> dict:
    started = time.monotonic()
    items = {"identity": _identity(pins, endpoint, model, reference_template),
             "capacity": _capacity(pins, endpoint)}
    items["protocol"], sample = _protocol(endpoint)
    timings = sample.get("timings", {})
    items["throughput"] = _item(True, {"prompt_per_second": timings.get("prompt_per_second"),
                                       "predicted_per_second": timings.get("predicted_per_second")})
    items["stability"] = _stability(endpoint)
    items["numerics"] = _numerics(perplexity_binary, model, reference_ppl, tolerance)
    items["tooling"] = _tooling(pins, prefix)
    items["isolation"] = _isolation(session_user, protected, pids)
    card = {"schema": "mellum-host-card/1", "passed": all(item["passed"] for item in items.values()),
            "pins_digest": rig.pins_digest(pins), "items": items, **host,
            "checked_at": datetime.now(UTC).isoformat(), "check_seconds": round(time.monotonic() - started, 3),
            "post_check": None, "stopped": None}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(card, indent=2) + "\n")
    return card


def post_check(pins: dict, endpoint: str, *, model: Path, prefix: str | None) -> dict:
    """After a rental's last session: the server, its weights and the tools must still be as pinned."""
    items = {"identity": _identity(pins, endpoint, model, None), "stability": _stability(endpoint),
             "tooling": _tooling(pins, prefix)}
    return {"passed": all(item["passed"] for item in items.values()), "items": items,
            "checked_at": datetime.now(UTC).isoformat()}
