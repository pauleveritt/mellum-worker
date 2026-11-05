"""Pinned native Pi integration over a fake provider; no GPU or counted inference."""
import argparse
import hashlib
import json
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import harness
from baseline import write_json
from containment import run_contained


class Provider(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'{}')

    def do_POST(self):
        if self.headers.get("transfer-encoding") == "chunked":
            chunks = []
            while size := int(self.rfile.readline().strip(), 16):
                chunks.append(self.rfile.read(size)); self.rfile.read(2)
            self.rfile.readline(); raw = b"".join(chunks)
        else:
            raw = self.rfile.read(int(self.headers.get("content-length", "0")))
        data = json.loads(raw)
        self.server.payloads.append(data)
        if self.server.kind == "tamper" and len(self.server.payloads) > 1:
            time.sleep(2)
        call = (self.server.kind == "repair" and len(self.server.payloads) == 2
                or self.server.kind == "tamper" and len(self.server.payloads) == 1)
        path, content = ("/attempt/gate/request.json", '{"task_id":"other"}') if self.server.kind == "tamper" else ("ready.flag", "ready")
        delta = ({"role": "assistant", "tool_calls": [{"index": 0, "id": "repair-write", "type": "function",
            "function": {"name": "write", "arguments": json.dumps({"path": path, "content": content})}}]}
            if call else {"role": "assistant", "content": "Qualification complete."})
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
        first = {"id": "qualification", "object": "chat.completion.chunk", "created": 0,
                 "model": "Mellum2.1-12B-A2.5B-Thinking", "choices": [{"index": 0, "delta": delta, "finish_reason": None}]}
        final = {**first, "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if call else "stop"}],
                 "usage": {"prompt_tokens": 42, "completion_tokens": 1, "total_tokens": 43}}
        for value in (first, final):
            self.wfile.write(b'data: ' + json.dumps(value).encode() + b'\n\n')
        self.wfile.write(b'data: [DONE]\n\n'); self.close_connection = True


def qualify(image: str, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    package = output / "package"; package.mkdir()
    (package / "checker.py").write_text('''def evaluate(snapshot, probe, remaining):
    passed = (snapshot / "ready.flag").is_file()
    return {"status":"pass" if passed else "fail", "checks":{
      "ready":{"passed":passed,"observation":"Create ready.flag to meet the qualification contract"}}}
''')
    (package / "spec.md").write_text("Fixture: create ready.flag. Not a coding measurement.\n")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package.iterdir()}
    write_json(package / "manifest.json", {"schema": 1, "timeout": 30, "checker": "checker.py",
        "requirements": {"ready": "Fixture artifact exists"}, "files": files, "spec_hashes": {"spec.md": files["spec.md"]}})
    profile = output / "profile"; profile.mkdir()
    for name in ("models.json", "settings.json"):
        shutil.copy2(harness.PROFILE / name, profile / name)
    models = json.loads((profile / "models.json").read_text())
    models["providers"]["llamacpp"]["baseUrl"] = "http://127.0.0.1:8002/v1"
    write_json(profile / "models.json", models)
    names, extras = harness.resolve_extras("prompt/name-the-layout,prompt/verify-the-spec,check/external-acceptance", [])
    results = {}
    for kind in ("pass", "repair", "exhaust", "tamper"):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Provider)
        server.kind, server.payloads = kind, []
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        start = output / kind / "start"; start.mkdir(parents=True)
        if kind == "pass": (start / "ready.flag").write_text("ready")
        suite = harness.Suite(name="gate-qualification", prompts=["Complete this qualification task."],
            tests=output / "absent-grader", start=start)
        try:
            run = run_contained(suite, image=image, runs_dir=output / kind / "runs", profile=profile,
                inference_target=f"http://127.0.0.1:{server.server_port}", arm="vanilla", deadline=90,
                stall=30, extras=extras, gate_package=package)
            receipt = json.loads((run / "acceptance.json").read_text())
            journal = json.loads((run / "acceptance-journal.json").read_text())
            write_json(output / kind / "provider-payloads.json", server.payloads)
            expected_repairs = {"pass": 0, "repair": 1, "exhaust": 2, "tamper": 0}[kind]
            expected_status = {"exhaust": "repair_exhausted", "tamper": "integrity_error"}.get(kind, "accepted")
            injected = all(sum("[Injected remedy: prompt/name-the-layout]" in str(m.get("content", ""))
                for m in p["messages"]) == 1 and sum("[Injected remedy: prompt/verify-the-spec]" in str(m.get("content", ""))
                for m in p["messages"]) == 1 for p in server.payloads)
            okay = (receipt["status"] == expected_status and receipt["repairs"] == expected_repairs
                and len(journal) == (1 if kind == "tamper" else expected_repairs + 2) and injected
                and (kind == "tamper" or harness.execution_outcome(run)["completion"] == "settled"))
            results[kind] = {"qualified": okay, "run": str(run), "status": receipt["status"],
                             "repairs": receipt["repairs"], "injections_once": injected, "requests": len(server.payloads)}
            print(json.dumps(results[kind]), flush=True)
            if not okay: break
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)
    proof = {"qualified": len(results) == 4 and all(r["qualified"] for r in results.values()),
             "image": image, "cases": results}
    write_json(output / "qualification.json", proof)
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if qualify(args.image, args.output)["qualified"] else 1)
