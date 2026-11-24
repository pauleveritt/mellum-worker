"""Tool-call smoke probe against the llama.cpp server on :8001.

Sends n sampled requests per case with the pinned profile's sampling
(temp 1.0, top_p 0.95, top_k 20, max_tokens 16384) and a Pi-like tool set,
and counts how many come back as parsed tool calls. Stdlib only.

Usage: uv run python toolprobe.py <label> [n]
"""
import json
import sys
import time
import urllib.request

URL = "http://127.0.0.1:8001/v1/chat/completions"
MODEL = "Mellum2.1-12B-A2.5B-Thinking"


def tool(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required}}}


S = {"type": "string"}
TOOLS = [
    tool("read", "Read a file's contents.", {"path": S}, ["path"]),
    tool("bash", "Run a shell command in the project directory.", {"command": S}, ["command"]),
    tool("edit", "Replace exact text in a file.", {"path": S, "oldText": S, "newText": S},
         ["path", "oldText", "newText"]),
    tool("write", "Write a whole file.", {"path": S, "content": S}, ["path", "content"]),
]
SYSTEM = ("You are a coding agent working in a Python project. Use the tools to act; "
          "do not describe what you would do.")
CASES = {
    "list-files": "List the files in this project.",
    "read-then-fix": "The test in tests/test_app.py fails. Find out why and fix it.",
    "write-module": "Create app/greet.py with a function greet(name) that returns 'Hello, <name>!'.",
}


def once(prompt):
    body = {"model": MODEL, "messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": prompt}],
            "tools": TOOLS, "max_tokens": 16384,
            "temperature": 1.0, "top_p": 0.95, "top_k": 20}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    ch = d["choices"][0]
    msg = ch["message"]
    calls = msg.get("tool_calls") or []
    valid = 0
    for c in calls:
        try:
            json.loads(c["function"]["arguments"])
            if c["function"]["name"] in {"read", "bash", "edit", "write"}:
                valid += 1
        except Exception:
            pass
    content = (msg.get("content") or "")
    return {"finish": ch.get("finish_reason"), "calls": len(calls), "valid": valid,
            "names": [c["function"]["name"] for c in calls],
            "tool_text_in_content": "<tool_call" in content or '"name"' in content,
            "completion_tokens": d.get("usage", {}).get("completion_tokens"),
            "secs": round(time.time() - t, 1)}


def main():
    label = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    summary = {}
    for case, prompt in CASES.items():
        rows = [once(prompt) for _ in range(n)]
        for i, r in enumerate(rows, 1):
            print(json.dumps({"label": label, "case": case, "rep": i, **r}), flush=True)
        ok = sum(1 for r in rows if r["valid"] >= 1)
        summary[case] = f"{ok}/{n}"
    print(json.dumps({"label": label, "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
