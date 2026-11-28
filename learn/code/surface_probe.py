"""Probe a model's tool calling with the system prompt and tool set from any manifest.

The manifest can be a run record from this repository (run.json, which carries the resolved `system_prompt` and
`tools` the model was sent) or one written by hand or exported from another harness: it needs only
`system_prompt` and `tools` (OpenAI function schemas). Each case is one user request; each reply is scored as a
well-formed call to a declared tool, or by its fault: no call, unknown tool, bad arguments, missing required.

    uv run python surface_probe.py --manifest RUN_OR_MANIFEST.json --base-url http://127.0.0.1:8091/v1 \\
        --model r1d-sft-v2b --thinking off [--cases surface_probe_cases.json] [--out result.json]
"""
import argparse
import json
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "ladder"))
from ladder.surface import load_surface  # noqa: E402


def request_body(system, tools, user, model, thinking, max_tokens=4096, temperature=0.6):
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    body = {"model": model, "messages": messages, "tools": tools, "max_tokens": max_tokens, "temperature": temperature}
    if thinking is not None:
        body["chat_template_kwargs"] = {"enable_thinking": thinking}
    return body


def score_reply(message, tools):
    """{call, ok, fault} for one assistant message against the declared tools."""
    calls = message.get("tool_calls") or []
    if not calls:
        return {"call": False, "ok": False, "fault": "no call"}
    declared = {t["function"]["name"]: t["function"].get("parameters", {}) for t in tools}
    for c in calls:
        fn = c.get("function", {})
        if fn.get("name") not in declared:
            return {"call": True, "ok": False, "fault": "unknown tool"}
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            return {"call": True, "ok": False, "fault": "bad arguments"}
        if not isinstance(args, dict):
            return {"call": True, "ok": False, "fault": "bad arguments"}
        if any(k not in args for k in declared[fn["name"]].get("required", [])):
            return {"call": True, "ok": False, "fault": "missing required"}
    return {"call": True, "ok": True, "fault": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--cases", default=str(HERE / "surface_probe_cases.json"))
    ap.add_argument("--thinking", choices=["on", "off", "unset"], default="unset")
    ap.add_argument("--out")
    a = ap.parse_args()
    system, tools = load_surface(a.manifest)
    cases = json.loads(Path(a.cases).read_text())
    thinking = {"on": True, "off": False, "unset": None}[a.thinking]
    rows, t0 = [], time.time()
    for user in cases:
        body = json.dumps(request_body(system, tools, user, a.model, thinking)).encode()
        req = urllib.request.Request(a.base_url.rstrip("/") + "/chat/completions", body,
                                     {"Content-Type": "application/json"})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=600))
            message, tokens = r["choices"][0]["message"], r.get("usage", {}).get("completion_tokens")
            s = score_reply(message, tools)
        except Exception as e:  # a server that cannot parse the reply is a fault too
            message, tokens, s = {}, None, {"call": False, "ok": False, "fault": f"server error: {e}"[:120]}
        rows.append({"case": user, **s, "completion_tokens": tokens,
                     "calls": [c["function"] for c in message.get("tool_calls") or []]})
        print(f"{'ok ' if s['ok'] else 'BAD'} {s['fault'] or ''} {user}", flush=True)
    ok = sum(r["ok"] for r in rows)
    result = {"manifest": str(a.manifest), "model": a.model, "thinking": a.thinking,
              "tools": [t["function"]["name"] for t in tools], "system_prompt_chars": len(system or ""),
              "ok": ok, "cases": len(rows), "faults": dict(Counter(r["fault"] for r in rows if r["fault"])),
              "completion_tokens": sum(r["completion_tokens"] or 0 for r in rows),
              "seconds": round(time.time() - t0, 1), "rows": rows}
    print(f"well-formed calls {ok}/{len(rows)}; faults {result['faults']}; {result['completion_tokens']} tokens")
    if a.out:
        Path(a.out).write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
