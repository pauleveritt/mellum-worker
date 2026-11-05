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
