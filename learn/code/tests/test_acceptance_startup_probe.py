"""Launch evidence survives probe cleanup without trusting candidate output."""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('startup_probe', ROOT / 'scripts/containment/probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_failed_launch_retains_runtime_warning_and_original_exit(tmp_path, monkeypatch):
    binary = tmp_path / 'uv'
    warning = 'WARNING: You must pass the application as an import string to enable reload or workers.'
    binary.write_text('#!/bin/sh\nprintf "%s\\n" "' + warning + '"\nexit 1\n')
    binary.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])
    monkeypatch.setattr(probe, 'Path', lambda _: tmp_path / 'launch.log')
    result = probe.startup()
    assert result['ready'] is False
    assert result['launch_exit_code'] == 1
    assert warning in result['log_tail']


def test_log_tail_reads_only_a_bounded_suffix(tmp_path):
    path = tmp_path / 'launch.log'
    path.write_bytes(b'prefix-' * 200000 + b'final failure\xff')
    text = probe.read_log_tail(path)
    assert 'final failure' in text
    assert len(text) <= 4096
    assert text.endswith('final failure\ufffd')


def test_ready_launch_preserves_live_status_then_reaps_process(tmp_path, monkeypatch):
    import sys
    import pytest
    binary = tmp_path / 'uv'; pidfile = tmp_path / 'child.pid'
    binary.write_text(f'#!{sys.executable}\n' +
        'import os\nfrom pathlib import Path\nfrom http.server import HTTPServer, BaseHTTPRequestHandler\n' +
        f'Path({str(pidfile)!r}).write_text(str(os.getpid()))\n' +
        'class Handler(BaseHTTPRequestHandler):\n' +
        '    def do_GET(self):\n        self.send_response(200); self.end_headers(); self.wfile.write(b"ready")\n' +
        'server=HTTPServer(("127.0.0.1",0),Handler)\n' +
        'print(f"http://127.0.0.1:{server.server_port}",flush=True)\nserver.serve_forever()\n')
    binary.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])
    monkeypatch.setattr(probe, 'Path', lambda _: tmp_path / 'launch.log')
    result = probe.startup()
    assert result['ready'] is True
    assert result['launch_exit_code'] is None
    pid = int(pidfile.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_first_launch_url_survives_later_urls_and_split_or_unterminated_lines(tmp_path, monkeypatch):
    import sys
    for mode in ('later-url', 'split-port', 'no-newline'):
        case = tmp_path / mode; case.mkdir()
        binary = case / 'uv'
        binary.write_text(f'#!{sys.executable}\n' + f'mode={mode!r}\n' + '''
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ready')
server=HTTPServer(('127.0.0.1',0),Handler,bind_and_activate=False)
server.server_bind()
url=f'http://127.0.0.1:{server.server_port}'
if mode=='later-url':
    print(url,flush=True)
    print('Startup configuration: '+'x'*300,flush=True)
    time.sleep(.15)
    print('Connecting to local dependency at http://127.0.0.1:1',flush=True)
    time.sleep(.5)
elif mode=='split-port':
    print('x'*(4096-len(url)+2)+url,flush=True)
else:
    print(url,end='',flush=True)
server.server_activate()
server.serve_forever()
''')
        binary.chmod(0o755)
        with monkeypatch.context() as patch:
            patch.setenv('PATH', str(case) + os.pathsep + os.environ['PATH'])
            patch.setattr(probe, 'Path', lambda _: case / 'launch.log')
            assert probe.startup()['ready'] is True, mode
