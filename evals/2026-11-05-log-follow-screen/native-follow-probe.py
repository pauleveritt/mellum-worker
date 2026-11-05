"""Host-only, uncounted native Pi guard qualification over a fake provider."""
import hashlib
import json
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'learn/code'))
import harness
from baseline import write_json
from containment import run_contained


class Provider(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'{}')
    def do_POST(self):
        if self.headers.get('transfer-encoding') == 'chunked':
            chunks = []
            while size := int(self.rfile.readline().strip(), 16):
                chunks.append(self.rfile.read(size)); self.rfile.read(2)
            self.rfile.readline(); raw = b''.join(chunks)
        else:
            raw = self.rfile.read(int(self.headers.get('content-length', '0')))
        self.server.payloads.append(json.loads(raw))
        call = len(self.server.payloads) == 1
        delta = ({'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'follow-probe', 'type': 'function',
                 'function': {'name': 'bash', 'arguments': json.dumps({'command':
                     'printf ready > follow-probe.log; tail -f follow-probe.log'})}}]}
                 if call else {'role': 'assistant', 'content': 'Qualification complete.'})
        first = {'id': 'qualification', 'object': 'chat.completion.chunk', 'created': 0,
                 'model': 'Mellum2.1-12B-A2.5B-Thinking', 'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]}
        final = {**first, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'tool_calls' if call else 'stop'}],
                 'usage': {'prompt_tokens': 42, 'completion_tokens': 1, 'total_tokens': 43}}
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
        for value in (first, final): self.wfile.write(b'data: ' + json.dumps(value).encode() + b'\n\n')
        self.wfile.write(b'data: [DONE]\n\n'); self.close_connection = True


def probe(image, output, unit):
    output.mkdir(parents=True, exist_ok=False)
    profile = output / 'profile'; profile.mkdir()
    for name in ('models.json', 'settings.json'): shutil.copy2(harness.PROFILE / name, profile / name)
    models = json.loads((profile / 'models.json').read_text())
    models['providers']['llamacpp']['baseUrl'] = 'http://127.0.0.1:8002/v1'
    write_json(profile / 'models.json', models)
    start = output / 'start'; start.mkdir()
    names, extras = harness.resolve_extras(unit, [])
    server = ThreadingHTTPServer(('127.0.0.1', 0), Provider); server.payloads = []
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        suite = harness.Suite(name='follow-qualification', prompts=['Complete the fixture task.'],
                              tests=output / 'absent-grader', start=start)
        run = run_contained(suite, image=image, runs_dir=output / 'runs', profile=profile, arm='vanilla',
                            inference_target=f'http://127.0.0.1:{server.server_port}', deadline=30,
                            stall=5, extras=extras)
        report = harness.report(run); outcome = harness.execution_outcome(run)
        trace = [json.loads(s) for s in (run / 'trace.jsonl').read_text().splitlines()]
        refusal = any(x.get('type') == 'tool_execution_end' and x.get('isError') and
                      'Blocked before execution: this foreground log-follow command' in str(x.get('result')) for x in trace)
        created = (run / 'workspace/follow-probe.log').exists()
        okay = refusal and not created and report['guard_blocks'] == 1 and len(server.payloads) == 2 and outcome['completion'] == 'settled'
        result = {'qualified': okay, 'image': image, 'units': names, 'run': str(run),
                  'guard_blocks': report['guard_blocks'], 'requests': len(server.payloads),
                  'execution': outcome, 'fixture_created': created, 'blocked_before_execution': refusal,
                  'trace_sha256': hashlib.sha256((run / 'trace.jsonl').read_bytes()).hexdigest(),
                  'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        write_json(output / 'provider-payloads.json', server.payloads)
        write_json(output / 'qualification.json', result); print(json.dumps(result))
        return okay
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == '__main__':
    raise SystemExit(0 if probe(sys.argv[1], Path(sys.argv[2]), sys.argv[3]) else 1)
