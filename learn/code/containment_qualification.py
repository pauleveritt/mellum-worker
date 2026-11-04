"""Uncounted real-boundary checks, using a local fake provider only."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from containment import Container, image_info, recover, docker


def qualify_grader(suite, image):
    from containment import grade_contained
    observed = {}
    with tempfile.TemporaryDirectory(prefix="mellum-contained-grader-") as temporary:
        for name in ("known-good", "known-broken"):
            run = Path(temporary) / name
            shutil.copytree(suite.root / "base", run / "workspace")
            shutil.copytree(suite.root / "fixtures" / name, run / "workspace", dirs_exist_ok=True)
            _, scored = grade_contained(run, suite, image, None)
            observed[name] = scored[0] and scored[3]
    return observed["known-good"] and not observed["known-broken"], observed


class FakeProvider(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"sentinel")

    def do_POST(self):
        payload = self.rfile.read(int(self.headers.get("content-length", "0")))
        # Node streams request chunks; consume chunked transfer as a real server would.
        if self.headers.get("transfer-encoding") == "chunked":
            chunks = []
            while True:
                length = int(self.rfile.readline().strip(), 16)
                if not length:
                    self.rfile.readline()
                    break
                chunks.append(self.rfile.read(length))
                self.rfile.read(2)
            payload = b"".join(chunks)
        mode = json.loads(payload).get("mode", "valid")
        if mode == "reset":
            self.connection.close()
            self.close_connection = True
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        if mode == "truncate":
            self.send_header("Content-Length", "99999")
        self.end_headers()
        first = {"id":"qualification", "object":"chat.completion.chunk", "created":0,
                 "model":"Mellum2.1-12B-A2.5B-Thinking", "choices":[{"index":0,
                    "delta":{"role":"assistant", "content":"qualification"}, "finish_reason":None}]}
        self.wfile.write(b'data: ' + json.dumps(first).encode() + b'\n\n')
        self.wfile.flush()
        if mode != "truncate":
            final = {**first, "choices":[{"index":0,"delta":{},"finish_reason":"stop"}],
                     "usage":{"prompt_tokens":42,"completion_tokens":1,"total_tokens":43}}
            self.wfile.write(b'data: ' + json.dumps(final).encode() + b'\n\n')
            self.wfile.write(b'data: [DONE]\n\n')
        self.close_connection = True


def qualify(image: str, output: Path | None):
    from baseline import write_json
    import harness
    if output is None:
        raise ValueError("--output is required to retain qualification evidence")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    material = image_info(image)
    profile = output / "profile"
    profile.mkdir()
    models = json.loads((harness.PROFILE / "models.json").read_text())
    models["providers"]["llamacpp"]["baseUrl"] = "http://127.0.0.1:8002/v1"
    write_json(profile / "models.json", models)
    shutil.copy2(harness.PROFILE / "settings.json", profile / "settings.json")
    results = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeProvider)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    sentinel_process = subprocess.Popen(["sleep", "300"])
    sentinel_file = output / "host-sentinel"
    sentinel_file.write_bytes(os.urandom(64))
    original = hashlib.sha256(sentinel_file.read_bytes()).hexdigest()
    previous_secret = os.environ.get("CONTAINMENT_SENTINEL_SECRET")
    os.environ["CONTAINMENT_SENTINEL_SECRET"] = "host-only"
    try:
        with Container(image, output / "sibling") as sibling, Container(image, output / "agent") as agent:
            sibling.execute("sh", "-c", "printf private > /attempt/sibling-secret")
            docker("exec", "-d", sibling.cid, "node", "-e",
                   "require('node:http').createServer((q,s)=>s.end('sibling')).listen(18765,'127.0.0.1')")
            # The host injects paths/PID/port as explicit attack targets, never file contents.
            probe = r'''
import os, json, socket, signal, subprocess
from pathlib import Path
host, pid, port = __import__('sys').argv[1:]
r = {}
for operation in ['read', 'write']:
    try:
        p = Path(host)
        p.read_bytes() if operation == 'read' else p.write_text('changed')
        r['host_file_' + operation] = False
    except OSError: r['host_file_' + operation] = True
try:
    os.kill(int(pid), signal.SIGTERM)
    r['host_process'] = False
except OSError: r['host_process'] = True
try:
    socket.create_connection(('127.0.0.1', int(port)), timeout=1).close()
    r['host_network'] = False
except OSError: r['host_network'] = True
r['sibling_file'] = not Path('/attempt/sibling-secret').exists()
try:
    socket.create_connection(('127.0.0.1', 18765), timeout=1).close()
    r['sibling_network'] = False
except OSError: r['sibling_network'] = True
r['host_secret_env'] = os.getenv('CONTAINMENT_SENTINEL_SECRET') is None
Path('/attempt/own').write_text('own')
r['workspace_write'] = Path('/attempt/own').read_text() == 'own'
r['subprocess'] = subprocess.check_output(['sh','-c','printf child']) == b'child'
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0)); listener.listen()
    with socket.create_connection(listener.getsockname(), timeout=1):
        connection, _ = listener.accept(); connection.close()
r['private_loopback'] = True
print(json.dumps(r))
'''
            response = agent.execute("uv", "run", "--no-project", "--python", "3.14.2", "python", "-c", probe,
                str(sentinel_file.resolve()), str(sentinel_process.pid), str(server.server_port), capture_output=True, text=True)
            results.update(json.loads(response.stdout))
            sibling_check = sibling.execute("node", "-e",
                "fetch('http://127.0.0.1:18765').then(r=>r.text()).then(t=>console.log(t))",
                capture_output=True, text=True)
            results["sibling_service_alive"] = sibling_check.stdout.strip() == "sibling"
            agent.start_relay(f"http://127.0.0.1:{server.server_port}")
            client = '''
import {installTransportObserver} from '/opt/instrument/extensions/mellum-recorder.ts';
const rows=[]; let current='qualification';
const stop=installTransportObserver({write:r=>rows.push(r),requestId:()=>current});
const observations=[];
for (const mode of ['valid','reset','truncate']) {
 current=mode;
 try { const r=await fetch('http://127.0.0.1:8002/v1/chat/completions',
   {method:'POST',body:JSON.stringify({mode})});
   const text=await r.text(); observations.push({mode,status:r.status,done:text.includes('[DONE]')}); }
 catch { observations.push({mode,error:true}); }
}
stop(); console.log(JSON.stringify({rows,observations}));
'''
            observed = json.loads(agent.execute("node", "--input-type=module", "-e", client,
                capture_output=True, text=True).stdout)
            write_json(output / "native-transport.json", observed)
            relay_rows = [json.loads(line) for line in (output / "agent/relay.jsonl").read_text().splitlines()]
            observations = observed["observations"]
            results["streaming_bytes"] = observations[0] == {"mode":"valid", "status":200, "done":True}
            results["reset_boundary"] = any(r["boundary"] == "request_error" for r in relay_rows)
            results["truncation_boundary"] = any(r["boundary"] == "stream_error" for r in relay_rows) and observations[2].get("error") is True
            results["client_correlation"] = any(r.get("relayId") for r in observed["rows"])
            results["native_cause_code"] = any(r.get("causes") for r in observed["rows"] if r["boundary"] == "error")
            from containment import run_contained
            native = {}
            for arm in ("vanilla", "worker"):
                run = run_contained(harness.load_suite(harness.SUITES, "easy"), image=image,
                    runs_dir=output / f"native-{arm}", profile=profile,
                    inference_target=f"http://127.0.0.1:{server.server_port}", arm=arm, deadline=60, stall=10)
                rows = [json.loads(line) for line in (run / "trace.jsonl").read_text().splitlines()]
                native[arm] = any(r["type"] == "agent_settled" and r.get("aborted") is False for r in rows)
            results["native_pi_vanilla"] = native["vanilla"]
            results["native_pi_worker"] = native["worker"]
            # Stop the fake upstream, then prove connection refusal is retained at the host boundary.
            server.shutdown(); server.server_close()
            refused = "const r=await fetch('http://127.0.0.1:8002/v1/chat/completions',{method:'POST',body:'{}'}); console.log(r.status)"
            status = agent.execute("node", "--input-type=module", "-e", refused, capture_output=True, text=True).stdout.strip()
            results["refusal_boundary"] = status == "502" and "ECONNREFUSED" in (output / "agent/relay.jsonl").read_text()
        results["host_file_intact"] = hashlib.sha256(sentinel_file.read_bytes()).hexdigest() == original
        results["host_process_alive"] = sentinel_process.poll() is None
        ok, graders = qualify_grader(harness.load_suite(harness.SUITES, "easy"), image)
        results["isolated_grader"] = ok
        write_json(output / "grader-qualification.json", graders)
        # A stopped inner harness and a hanging grader must both be bounded
        # by the host, followed by removal of all owned processes and storage.
        for name, code in (("stopped_inner_watchdog", "import os,signal; os.kill(os.getpid(),signal.SIGSTOP)"),
                           ("hanging_grader_watchdog", "import time; time.sleep(300)")):
            timed_out = False
            with Container(image, output / name) as stalled:
                try:
                    stalled.execute("uv", "run", "--no-project", "--python", "3.14.2", "python", "-c", code, timeout=1)
                except subprocess.TimeoutExpired:
                    timed_out = True
                owner = stalled.owner
            remaining = docker("ps", "--all", "--quiet", "--filter", f"label=mellum.measurement.owner={owner}",
                               capture_output=True, text=True).stdout.strip()
            volumes = docker("volume", "ls", "--quiet", "--filter", f"label=mellum.measurement.owner={owner}",
                             capture_output=True, text=True).stdout.strip()
            results[name] = timed_out and not remaining and not volumes
        # Abrupt host exit must leave a durable label that recovery removes.
        recovery_root = output / "recovery"
        recovery_control = recovery_root / (".container-" + __import__('uuid').uuid4().hex)
        script = "import time; from pathlib import Path; from containment import Container; c=Container(%r,Path(%r)); c.__enter__(); print('ready',flush=True); time.sleep(300)" % (image, str(recovery_control))
        child = subprocess.Popen([sys.executable, "-c", script], cwd=harness.CODE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            if child.stdout.readline().strip() != "ready":
                raise RuntimeError("recovery sentinel failed to start: " + child.stderr.read())
            child.kill(); child.wait(timeout=10)
            identity = json.loads((recovery_control / "container.json").read_text())
            recover(recovery_root)
            remaining = docker("ps", "--all", "--quiet", "--filter",
                "label=mellum.measurement.owner=" + identity["owner"], capture_output=True, text=True).stdout.strip()
            volumes = docker("volume", "ls", "--quiet", "--filter",
                "label=mellum.measurement.owner=" + identity["owner"], capture_output=True, text=True).stdout.strip()
            results["interrupted_recovery"] = not remaining and not volumes
        finally:
            if child.poll() is None: child.kill(); child.wait()
    except BaseException as error:
        write_json(output / "qualification.json", {"qualified":False, "material":material,
                   "checks":results, "failure":type(error).__name__, "scope":"Uncounted fake-provider qualification"})
        raise
    finally:
        server.shutdown(); server.server_close()
        sentinel_process.terminate(); sentinel_process.wait()
        if previous_secret is None: os.environ.pop("CONTAINMENT_SENTINEL_SECRET", None)
        else: os.environ["CONTAINMENT_SENTINEL_SECRET"] = previous_secret
    proof = {"qualified": all(results.values()), "material": material, "checks": results,
             "scope": "Uncounted local fake backend; no Runpod inference"}
    write_json(output / "qualification.json", proof)
    return proof
