"""Drive Mellum Mode interactively through Pi's RPC mode and print what each request carried.

    uv run python -m ladder.probe_mode_rpc

Needs the oMLX server and the operator's hosted parent model (the mirrored
~/.pi/agent profile). Exercises: /mellum on, a second on, a task under the
mode, /mellum off, a parent turn, a second off, and the one-shot
/mellum <task>. Record: evals/2026-10-09-ablation-a14-mellum-mode/README.md.
"""

import json
import os
import queue
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from ladder.pi_profile import mirror_agent_dir
from ladder.run_ladder import MODE_EXT, RECORD_EXT, child_env
from ladder.rungs import copy_fixture

scratch = Path(tempfile.mkdtemp(prefix="mellum-rpc-"))
ws = copy_fixture("calculator", scratch / "ws")
agent = mirror_agent_dir(
    Path.home() / ".pi" / "agent",
    scratch / "pi-agent",
    [ws],
    exclude_packages=("mellum-worker",),
)
trace = scratch / "trace.jsonl"
env = child_env(dict(os.environ), str(trace), agent, offline=False)
env["MELLUM_MODE_RUNS"] = str(scratch / "mellum-mode-runs.jsonl")
proc = subprocess.Popen(
    [
        "pi",
        "--mode",
        "rpc",
        "--no-session",
        "-e",
        str(MODE_EXT),
        "-e",
        str(RECORD_EXT),
    ],
    cwd=ws,
    env=env,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
q = queue.Queue()


def reader():
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("{"):
            try:
                q.put(json.loads(line))
            except json.JSONDecodeError:
                continue


threading.Thread(target=reader, daemon=True).start()


def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def wait_for(pred, timeout=300):
    end = time.time() + timeout
    while time.time() < end:
        try:
            e = q.get(timeout=1)
        except queue.Empty:
            continue
        if pred(e):
            return e
    raise TimeoutError("waited for event")


def model():
    send({"id": "s", "type": "get_state"})
    e = wait_for(
        lambda e: e.get("type") == "response" and e.get("command") == "get_state", 30
    )
    return e["data"].get("model", {}).get("id") or e["data"].get("model")


def requests():
    out = []
    if trace.exists():
        with open(trace) as f:
            for line in f:
                e = json.loads(line)
                if e.get("type") == "provider_request":
                    out.append(e["payload"])
    return out


def describe(p):
    ms = p["messages"]
    sysm = ms[0]["content"] if ms and ms[0]["role"] in ("system", "developer") else ""
    users = [m for m in ms if m.get("role") == "user"]
    return {
        "model": p.get("model"),
        "system_is_v5": str(sysm).startswith("<!-- mellum-worker prompt"),
        "system_chars": len(str(sysm)),
        "messages": len(ms),
        "users": len(users),
        "first_user": (str(users[0].get("content"))[:50] if users else None),
        "tools": [t.get("function", t).get("name") for t in p.get("tools", [])],
    }


wait_for(
    lambda e: e.get("type") in ("session_start", "agent_settled", "response") or True,
    20,
)
print("1 parent model:", model())
send({"type": "prompt", "message": "/mellum on"})
time.sleep(2)
print("2 after /mellum on:", model())
send({"type": "prompt", "message": "/mellum on"})
time.sleep(2)
print("3 after second /mellum on:", model())
n0 = len(requests())
send({"type": "prompt", "message": "the cart total ignores quantity, fix it"})
wait_for(lambda e: e.get("type") == "agent_settled")
reqs = requests()[n0:]
print(
    "4 task under mode: requests",
    len(reqs),
    "| first:",
    describe(reqs[0]) if reqs else None,
    "| last tools:",
    describe(reqs[-1])["tools"] if reqs else None,
)
test = subprocess.run(
    ["node", "--test", "calculator.test.js"],
    cwd=ws,
    capture_output=True,
    text=True,
    check=False,
)
print("   tests exit", test.returncode)
send({"type": "prompt", "message": "/mellum off"})
time.sleep(3)
print("5 after /mellum off:", model())
n1 = len(requests())
send({"type": "prompt", "message": "Reply with the single word ok."})
wait_for(lambda e: e.get("type") == "agent_settled")
reqs = requests()[n1:]
print("6 parent turn after off:", describe(reqs[-1]) if reqs else None)
send({"type": "prompt", "message": "/mellum off"})
time.sleep(2)
print("7 second /mellum off: model", model())
n2 = len(requests())
send({"type": "prompt", "message": "/mellum Reply with the single word done."})
wait_for(lambda e: e.get("type") == "agent_settled")
time.sleep(3)
reqs = requests()[n2:]
print(
    "8 one-shot: requests",
    len(reqs),
    "| first:",
    describe(reqs[0]) if reqs else None,
    "| model after settle:",
    model(),
)
proc.terminate()
print("scratch", scratch)
