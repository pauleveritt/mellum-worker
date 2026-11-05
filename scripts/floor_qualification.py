"""Uncounted qualification of the portable rig's native path on the Mac (LC.39, plan Task 11).

Each case drives the real driver path (`floor_cohort.run_one`: budget proxy, pinned Pi,
native session, sweep, reconciliation, grading) against a scripted fake llama-server that
writes llama-server-format timing lines, so reconciliation sees what a real server logs.

    uv run python scripts/floor_qualification.py BATCH --prefix ~/.mellum-rig

No model runs and nothing is counted. The batch must be fresh.
"""
import argparse
import importlib.util
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "learn/code"))
import rig

spec = importlib.util.spec_from_file_location("floor_cohort", REPO / "scripts/floor_cohort.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

LISTENER = ("import os,socket,time; os.setsid(); s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); "
            "open('listener.port','w').write(str(s.getsockname()[1])); time.sleep(300)")


class Fake(BaseHTTPRequestHandler):
    """A scripted llama-server: replies by case, and logs each generation as llama-server does."""

    def log_message(self, *_):
        pass

    def do_GET(self):
        body = b'{"status":"ok"}'
        self.send_response(200); self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def generation(self, completion: int):
        server = self.server
        with server.lock:
            server.task += 1
            task = server.task
            with server.log.open("a") as log:
                log.write(f"slot operator(): id  0 | task {task} | new prompt, task.n_tokens = 100\n"
                          f"slot print_timing: id  0 | task {task} | prompt eval time =       1.00 ms /   100 tokens\n"
                          f"slot print_timing: id  0 | task {task} |        eval time =       1.00 ms / {completion:5d} tokens\n")
        return task

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("content-length", "0"))))
        server = self.server
        with server.lock:
            server.requests += 1
            number = server.requests
        if not data.get("stream"):                       # a direct call from the session, not Pi via the proxy
            self.generation(1)
            body = json.dumps({"choices": [{"message": {"role": "assistant", "content": "direct"},
                               "finish_reason": "stop"}], "usage": {"completion_tokens": 1}}).encode()
            self.send_response(200); self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body))); self.end_headers(); self.wfile.write(body)
            return
        call, completion = server.script(number)
        self.generation(completion)
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        delta = ({"role": "assistant", "tool_calls": [{"index": 0, "id": f"call-{number}", "type": "function",
                  "function": {"name": "bash", "arguments": json.dumps({"command": call})}}]}
                 if call else {"role": "assistant", "content": "Done."})
        first = {"id": "q", "object": "chat.completion.chunk", "created": 0, "model": "Mellum2.1-12B-A2.5B-Thinking",
                 "choices": [{"index": 0, "delta": delta, "finish_reason": None}]}
        self.wfile.write(b"data: " + json.dumps(first).encode() + b"\n\n"); self.wfile.flush()
        if server.case == "reset" and number == 1:
            time.sleep(0.2)
            self.connection.shutdown(2)                   # reset mid-stream: no usage chunk ever arrives
            return
        final = {**first, "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if call else "stop"}],
                 "usage": {"prompt_tokens": 100, "completion_tokens": completion, "total_tokens": 100 + completion}}
        self.wfile.write(b"data: " + json.dumps(final).encode() + b"\n\ndata: [DONE]\n\n")
        self.close_connection = True


def script_for(case: str, port: int):
    if case == "budget":                                   # every reply is a large tool-call turn
        return lambda n: ("echo working", 30000)
    if case == "reset":
        return lambda n: (None, 10)
    if case == "bypass":
        direct = (f"curl -s -X POST http://127.0.0.1:{port}/v1/chat/completions -H 'content-type: application/json' "
                  "-d '{\"messages\":[{\"role\":\"user\",\"content\":\"x\"}],\"stream\":false}'")
        return lambda n: (direct, 10) if n == 1 else (None, 10)
    if case == "listener":
        return lambda n: (f"nohup python3 -c \"{LISTENER}\" >/dev/null 2>&1 & sleep 1", 10) if n == 1 else (None, 10)
    raise ValueError(case)


def expect(case: str, event: dict) -> tuple[bool, str]:
    run = Path(event["run"])
    rows = [json.loads(line) for line in (run / "proxy.jsonl").read_text().splitlines() if line.strip()]
    if case == "budget":
        ok = event["record"]["completion"] == "budget" and any(r["boundary"] == "budget_exhausted" for r in rows)
        return ok, f"completion {event['record']['completion']}, state {event['state']}"
    if case == "reset":
        unknown = [r for r in rows if r["boundary"] == "usage" and r["outputTokens"] is None]
        ok = bool(unknown) and unknown[0]["charged"] == 16384
        return ok, f"unknown-usage rows {len(unknown)}, charged {[r['charged'] for r in unknown]}"
    if case == "bypass":
        ok = event["state"] == "invalid" and "reconcile" in event["reason"]
        return ok, f"state {event['state']}: {event['reason']}"
    if case == "listener":
        port_file = run / "workspace/listener.port"
        port = int(port_file.read_text()) if port_file.is_file() else None
        leaked = json.loads((run / "leaked.json").read_text())
        still = port is not None and driver.isolation.preflight_mac([port])["ok"] is False
        ok = port is not None and bool(leaked) and not still
        return ok, f"listener port {port}, swept {len(leaked)}, still listening {still}"
    raise ValueError(case)


def qualify(batch: Path, prefix: str) -> dict:
    if batch.exists():
        raise SystemExit(f"{batch} exists; qualification needs a fresh batch")
    batch.mkdir(parents=True)
    pins = rig.load_pins()
    results = []
    for index, case in enumerate(("budget", "reset", "bypass", "listener"), 1):
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        httpd.case, httpd.lock, httpd.task, httpd.requests = case, threading.Lock(), 0, 0
        httpd.log = batch / f"{case}-server.log"
        httpd.log.touch()
        httpd.script = script_for(case, httpd.server_address[1])
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        config = {"pod": False, "prefix": prefix, "rental_id": f"qualification-{case}",
                  "endpoint": f"http://127.0.0.1:{httpd.server_address[1]}", "server_log": str(httpd.log)}
        started = time.monotonic()
        try:
            event = driver.run_one(batch, "M", config, {"rental_id": config["rental_id"]}, pins, index)
            passed, detail = expect(case, event)
        except Exception as error:      # a qualification records its own failure rather than hiding it
            event, passed, detail = None, False, f"{type(error).__name__}: {error}"
        finally:
            httpd.shutdown()
        results.append({"case": case, "qualified": passed, "detail": detail, "seconds": round(time.monotonic() - started, 1),
                        "fake_requests": httpd.requests, "run": event and event["run"],
                        "state": event and event["state"], "reason": event and event["reason"]})
        print(json.dumps(results[-1]), flush=True)
    proof = {"qualified": all(r["qualified"] for r in results), "cases": results,
             "pins_digest": rig.pins_digest(pins), "tools": rig.tool_versions(prefix),
             "commit": driver.subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()}
    driver.write_json(batch / "qualification.json", proof)
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--prefix", required=True)
    arguments = parser.parse_args()
    raise SystemExit(0 if qualify(arguments.batch, arguments.prefix)["qualified"] else 1)
