#!/usr/bin/env python3
"""Dependency-free data server for the live ladder dashboard.

Serves dashboard/index.html at / and a /data.json the page polls: per-rung
results from a sweep's out dir, plus the newest worker trace's recent turns.

  DASH_OUT   sweep out dir to read run.json from (default: the 6-bit sweep)
  DASH_PORT  port (default 8787)
"""
import glob
import json
import os
import re
import shlex
import signal
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_MODEL = os.environ.get("DASH_MODEL", "Mellum2.1-12B-A2.5B-Thinking-6bit")
RUNNING = {}  # rung -> subprocess.Popen, the runs this dashboard launched
DEFAULT_OUT = "/private/tmp/claude-501/-Users-mac-projects/8aed2d08-ac9d-4f56-9569-c4d3ba627b18/scratchpad/sweep-6bit"
OUT = os.environ.get("DASH_OUT", DEFAULT_OUT)
FEED = os.path.expanduser(os.environ.get("MELLUM_FEED", "~/.pi/agent/mellum-feed.ndjson"))
OVERRIDE = os.path.expanduser(
    os.environ.get("MELLUM_PROMPT_OVERRIDE", "~/.pi/agent/mellum-prompt-override.json")
)
CONTROL = os.path.expanduser(
    os.environ.get("MELLUM_CONTROL", "~/.pi/agent/mellum-control.json")
)
TRACE_GLOBS = [
    "/private/var/folders/*/*/T/ladder-*/trace.jsonl",
    "/tmp/ladder-*/trace.jsonl",
]


def feed_events(limit=12):
    """Recent events from the agnostic mellum-feed (what mellum-feed.ts writes)."""
    try:
        lines = open(FEED).read().splitlines()
    except Exception:
        return []
    out = []
    for line in lines[-200:]:
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("kind") == "turn":
            out.append({"think": (e.get("think") or "")[:180], "call": e.get("call") or ""})
    return out[-limit:]


def sweep_rows():
    rungs = {}
    # Recursive: matches both the two-level sweep layout (rungN/<run>/run.json)
    # and the screen.sh one-level layout (rungN-profile-rX/run.json).
    for f in glob.glob(os.path.join(OUT, "**", "run.json"), recursive=True):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        n = r.get("rung")
        if n is None:
            continue
        rungs.setdefault(n, []).append(
            {
                "passed": bool(r.get("check", {}).get("passed")),
                "wall": round(r.get("wall_seconds_untrusted") or 0),
            }
        )
    rows = []
    for n in sorted(rungs):
        runs = rungs[n]
        rows.append(
            {
                "rung": n,
                "pass": sum(1 for x in runs if x["passed"]),
                "n": len(runs),
                "wall": round(sum(x["wall"] for x in runs) / len(runs)),
            }
        )
    return rows


def _find_assistant(o):
    if isinstance(o, dict):
        if o.get("role") == "assistant" and "content" in o:
            return o
        for v in o.values():
            r = _find_assistant(v)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _find_assistant(v)
            if r:
                return r
    return None


def active_trace(limit=10):
    files = [f for g in TRACE_GLOBS for f in glob.glob(g) if os.path.exists(f)]
    if not files:
        return {"trace": None, "turns": []}
    newest = max(files, key=os.path.getmtime)
    turns = []
    try:
        lines = open(newest).read().splitlines()
    except Exception:
        return {"trace": os.path.basename(os.path.dirname(newest)), "turns": []}
    for line in lines[-500:]:
        try:
            o = json.loads(line)
        except Exception:
            continue
        msg = _find_assistant(o)
        if not msg:
            continue
        think, call = "", ""
        content = msg.get("content")
        if isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text"):
                    think = b["text"]
                if b.get("type") == "toolCall":
                    args = json.dumps(b.get("arguments", {}))
                    call = f"{b.get('name', '')}({args[:90]})"
        if think or call:
            turns.append({"think": think[:180], "call": call})
    return {"trace": os.path.basename(os.path.dirname(newest)), "turns": turns[-limit:]}


def latest_prompt():
    """The most recent prompt the worker was sent (system + task/injected)."""
    try:
        lines = open(FEED).read().splitlines()
    except Exception:
        return None
    for line in reversed(lines[-300:]):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("kind") == "prompt":
            return {"system": e.get("system", ""), "task": e.get("task", "")}
    return None


def intel_events(limit=20):
    """Told-vs-truth contradictions the skeptical gate found (mellum-rethink)."""
    try:
        lines = open(FEED).read().splitlines()
    except Exception:
        return []
    out = []
    for line in lines[-400:]:
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("kind") == "rethink":
            out.append({"claim": e.get("claim", ""), "observed": e.get("observed", ""), "t": e.get("t")})
    return out[-limit:]


def rung_detail(n):
    """Every past run of one rung, newest first, with a short summary of each."""
    runs = []
    for f in glob.glob(os.path.join(OUT, "**", "run.json"), recursive=True):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if r.get("rung") != n:
            continue
        chk = r.get("check", {})
        runs.append(
            {
                "run": os.path.basename(os.path.dirname(f)),
                "passed": bool(chk.get("passed")),
                "wall": round(r.get("wall_seconds_untrusted") or 0),
                "stop": r.get("stop_reason"),
                "deadline": bool(r.get("deadline_hit")),
                "sentence": r.get("sentence", ""),
                "diff": (r.get("diff_stat") or "").strip(),
                "details": chk.get("details", {}),
                "mtime": os.path.getmtime(f),
            }
        )
    runs.sort(key=lambda x: x["mtime"], reverse=True)
    for x in runs:
        del x["mtime"]
    return {"rung": n, "runs": runs}


def read_control():
    try:
        return "pause" if json.loads(open(CONTROL).read()).get("state") == "pause" else "play"
    except Exception:
        return "play"


def write_control(state):
    state = "pause" if state == "pause" else "play"
    os.makedirs(os.path.dirname(CONTROL), exist_ok=True)
    with open(CONTROL, "w") as fh:
        json.dump({"state": state}, fh)
    return {"state": state}


def read_override():
    try:
        return json.loads(open(OVERRIDE).read())
    except Exception:
        return {"system": "", "append": ""}


def write_override(data):
    os.makedirs(os.path.dirname(OVERRIDE), exist_ok=True)
    clean = {
        "system": str(data.get("system", "") or ""),
        "append": str(data.get("append", "") or ""),
    }
    with open(OVERRIDE, "w") as fh:
        json.dump(clean, fh)
    return clean


def acc_for(n):
    """The committed frozen acceptance test for an AgentClinic rung (6-12)."""
    p = n - 5
    if 6 <= n <= 9:
        return f"evals/2026-10-20-v7-ablation/acceptance/test_phase{p}.py"
    if 10 <= n <= 12:
        return f"ladder/fixtures/acceptance/test_phase{p}.py"
    return None


def running_status():
    """Which dashboard-launched runs are still going."""
    live = []
    for n, proc in list(RUNNING.items()):
        if proc.poll() is None:
            live.append(n)
        else:
            RUNNING.pop(n, None)
    return sorted(live)


def launch_run(n, model):
    """Start a run for rung n, writing into OUT. Rungs 6-12 run the mediated
    screen (frozen test); rungs 1-5 are standalone coding rungs with no frozen
    phase test, so they run un-mediated via the ladder directly."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return {"ok": False, "error": "rung must be a number"}
    if not (1 <= n <= 12):
        return {"ok": False, "error": f"rung {n} is out of range (1-12)"}
    if n in RUNNING and RUNNING[n].poll() is None:
        return {"ok": False, "error": f"rung {n} is already running"}
    relout = os.path.relpath(OUT, REPO)
    model = model or DEFAULT_MODEL
    log = open(os.path.join(OUT, f"dash-run-rung{n}.log"), "w") if os.path.isdir(OUT) else subprocess.DEVNULL
    if n <= 5:
        # coding rungs 1-5: no frozen phase test; run un-mediated via the ladder.
        proc = subprocess.Popen(
            ["uv", "run", "python", "-m", "ladder.run_ladder", "--mode", "direct",
             "--profile", "tuned", "--repeat", "1", "--thinking", "off", "--guards",
             "--rung", str(n), "--model", "omlx/" + model, "--out", "../" + relout],
            cwd=os.path.join(REPO, "ladder"), stdout=log, stderr=subprocess.STDOUT,
        )
        mediated = False
    else:
        acc = acc_for(n)
        if not os.path.isfile(os.path.join(REPO, acc)):
            return {"ok": False, "error": f"acceptance test missing: {acc}"}
        proc = subprocess.Popen(
            ["scripts/screen.sh", str(n), model, acc, relout],
            cwd=REPO, stdout=log, stderr=subprocess.STDOUT,
        )
        mediated = True
    RUNNING[n] = proc
    return {"ok": True, "rung": n, "model": model, "out": relout, "mediated": mediated}


def launch_all(model):
    """Run the whole ladder 1-12 (one pass each) as a single background sweep,
    writing into OUT with the live feed loaded for the dashboard."""
    if RUNNING.get("all") and RUNNING["all"].poll() is None:
        return {"ok": False, "error": "a full ladder run is already going"}
    relout = os.path.relpath(OUT, REPO)
    model = model or DEFAULT_MODEL
    feed_ext = os.path.join(REPO, "extensions", "mellum-feed.ts")
    log = open(os.path.join(OUT, "dash-run-all.log"), "w") if os.path.isdir(OUT) else subprocess.DEVNULL
    inner = (
        "for rung in 1 2 3 4 5 6 7 8 9 10 11 12; do "
        "uv run python -m ladder.run_ladder --mode direct --profile tuned --repeat 1 "
        "--thinking off --guards --rung $rung --model {model} --pi-extension {feed} "
        "--out ../{out} || true; done"
    ).format(model=shlex.quote("omlx/" + model), feed=shlex.quote(feed_ext), out=shlex.quote(relout))
    proc = subprocess.Popen(
        ["bash", "-c", inner], cwd=os.path.join(REPO, "ladder"),
        stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy(),
        start_new_session=True,  # own process group, so Stop can kill the whole sweep
    )
    RUNNING["all"] = proc
    return {"ok": True, "model": model, "out": relout, "rungs": "1-12"}


def full_run_active():
    p = RUNNING.get("all")
    return bool(p and p.poll() is None)


def stop_run():
    """Stop the active run: the dashboard's own sweep (whole process group) and,
    best-effort, any ladder worker running (e.g. one started from a terminal)."""
    stopped = []
    p = RUNNING.get("all")
    if p and p.poll() is None:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            p.terminate()
        stopped.append("dashboard sweep")
    try:
        if subprocess.run(["pkill", "-f", "run_ladder"], timeout=5).returncode == 0:
            stopped.append("ladder worker")
    except Exception:
        pass
    return {"ok": True, "stopped": stopped}


def activity():
    """Whether a worker is active right now, launch-agnostic: based on how fresh
    the feed and the newest trace are. A run started from a terminal shows too."""
    now_ms = time.time() * 1000
    fresh_ms = 120_000
    last_age = None
    try:
        for ln in reversed(open(FEED).read().splitlines()[-50:]):
            try:
                t = json.loads(ln).get("t")
            except Exception:
                continue
            if t:
                last_age = now_ms - t
                break
    except Exception:
        pass
    rung, trace_age_ms = None, None
    traces = glob.glob(os.path.join(OUT, "**", "trace.jsonl"), recursive=True)
    traces += [f for g in TRACE_GLOBS for f in glob.glob(g)]
    traces = [f for f in traces if os.path.exists(f)]
    if traces:
        newest = max(traces, key=os.path.getmtime)
        trace_age_ms = now_ms - os.path.getmtime(newest) * 1000
        m = re.search(r"rung(\d+)", os.path.basename(os.path.dirname(newest)))
        if m:
            rung = int(m.group(1))
    fresh = [a for a in (last_age, trace_age_ms) if a is not None and a < fresh_ms]
    active = bool(fresh)
    age_src = min([a for a in (last_age, trace_age_ms) if a is not None], default=None)
    return {"active": active, "rung": rung if active else None,
            "ageSec": round(age_src / 1000) if age_src is not None else None}


def payload():
    # Prefer the agnostic feed (mellum-feed.ts); fall back to scraping the
    # newest trace for runs that don't load the feed extension (e.g. the sweep).
    active = feed_events() or active_trace().get("turns", [])
    return {
        "updatedAt": time.strftime("%H:%M:%S"),
        "sweep": sweep_rows(),
        "active": active,
        "prompt": latest_prompt(),
        "intel": intel_events(),
        "running": running_status(),
        "runningAll": full_run_active(),
        "activity": activity(),
        "model": DEFAULT_MODEL,
        "control": read_control(),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("content-type", ctype)
        self.send_header("access-control-allow-origin", "*")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/events"):
            # Server-Sent Events: push the whole dashboard state every ~1.5s.
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("cache-control", "no-store")
            self.send_header("connection", "keep-alive")
            self.send_header("access-control-allow-origin", "*")
            self.end_headers()
            try:
                while True:
                    self.wfile.write(f"data: {json.dumps(payload())}\n\n".encode())
                    self.wfile.flush()
                    time.sleep(1.5)
            except (BrokenPipeError, ConnectionResetError):
                return
        elif self.path.startswith("/data.json"):
            self._send(json.dumps(payload()).encode(), "application/json")
        elif self.path.startswith("/rung"):
            from urllib.parse import urlparse, parse_qs

            q = parse_qs(urlparse(self.path).query)
            try:
                n = int(q.get("n", ["0"])[0])
            except ValueError:
                n = 0
            self._send(json.dumps(rung_detail(n)).encode(), "application/json")
        elif self.path.startswith("/override"):
            self._send(json.dumps(read_override()).encode(), "application/json")
        else:
            try:
                body = open(os.path.join(HERE, "index.html"), "rb").read()
            except Exception:
                body = b"<h1>index.html missing</h1>"
            self._send(body, "text/html; charset=utf-8")

    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            data = {}
        if self.path.startswith("/override"):
            self._send(json.dumps(write_override(data)).encode(), "application/json")
        elif self.path.startswith("/control"):
            self._send(json.dumps(write_control(data.get("state"))).encode(), "application/json")
        elif self.path.startswith("/run-all"):
            self._send(json.dumps(launch_all(data.get("model"))).encode(), "application/json")
        elif self.path.startswith("/stop"):
            self._send(json.dumps(stop_run()).encode(), "application/json")
        elif self.path.startswith("/run"):
            self._send(json.dumps(launch_run(data.get("rung"), data.get("model"))).encode(), "application/json")
        else:
            self._send(b'{"error":"not found"}', "application/json")


if __name__ == "__main__":
    port = int(os.environ.get("DASH_PORT", "8787"))
    print(f"ladder dashboard: http://127.0.0.1:{port}   (reading {OUT})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
