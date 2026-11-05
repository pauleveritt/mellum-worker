"""Native session isolation (LC.39): sweep a session user and probe what it can reach."""
import getpass
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import isolation

LISTENER = ("import socket,time; s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); "
            "print(s.getsockname()[1], flush=True); time.sleep(60)")


def start_listener():
    child = subprocess.Popen([sys.executable, "-c", LISTENER], stdout=subprocess.PIPE, text=True,
                             start_new_session=True)
    port = int(child.stdout.readline())
    return child, port


def listening(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


def test_sweep_kills_setsid_listener():
    child, port = start_listener()
    try:
        assert listening(port)
        result = isolation.sweep_user(getpass.getuser(), roots={child.pid}, grace=0.5)
        child.wait(timeout=5)
        assert result["ok"] and child.pid in [pid for pid, _ in result["killed"]]
        assert not listening(port) and result["listeners_after"] == []
        assert result["home_reset"] is False  # never resets a home that is not a rig user's
    finally:
        if child.poll() is None:
            child.kill()


def test_sweep_reports_failure_when_listener_survives(monkeypatch):
    child, port = start_listener()
    try:
        monkeypatch.setattr(isolation, "_signal", lambda pid, number: None)
        result = isolation.sweep_user(getpass.getuser(), roots={child.pid}, grace=0.2)
        assert result["ok"] is False
        assert any(entry["port"] == port for entry in result["listeners_after"])
    finally:
        child.kill(); child.wait()


LSOF = """p4242
cuvicorn
u501
f7
n127.0.0.1:8000
p77
cllama-server
u0
f3
n*:18001
"""


def test_listeners_parse():
    rows = isolation.parse_lsof(LSOF)
    assert rows == [{"pid": 4242, "command": "uvicorn", "uid": 501, "address": "127.0.0.1:8000", "port": 8000},
                    {"pid": 77, "command": "llama-server", "uid": 0, "address": "*:18001", "port": 18001}]


def test_isolation_probe_flags_readable_secret(tmp_path):
    secret, private = tmp_path / "token", tmp_path / "key"
    secret.write_text("s"); secret.chmod(0o644)
    private.write_text("k"); private.chmod(0o600)
    result = isolation.isolation_probe("nobody", [secret, private], [os.getpid()])
    assert result["ok"] is False
    assert [f["path"] for f in result["findings"] if f["kind"] == "readable"] == [str(secret)]


def test_isolation_probe_flags_signalable_process(tmp_path):
    me = getpass.getuser()
    result = isolation.isolation_probe(me, [], [os.getpid()])
    assert any(f["kind"] == "signalable" and f["pid"] == os.getpid() for f in result["findings"])


def test_preflight_mac_fails_on_a_taken_port():
    child, port = start_listener()
    try:
        assert isolation.preflight_mac([port])["ok"] is False
    finally:
        child.kill(); child.wait()
    time.sleep(0.2)
    assert isolation.preflight_mac([port])["ok"] is True
