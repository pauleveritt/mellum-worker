"""The host a run measured on: the serving process and the GPU, read live, not typed in."""

import json
import os
import stat
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ladder.host_record import gpu_identity, server_identity


class _Handler(BaseHTTPRequestHandler):
    routes: dict = {}

    def do_GET(self):
        body = self.routes.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    def start(routes):
        handler = type("H", (_Handler,), {"routes": routes})
        httpd = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        started.append(httpd)
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    started = []
    yield start
    for httpd in started:
        httpd.shutdown()


def test_server_identity_reads_version_and_served_models(server):
    base = server({
        "/version": {"version": "0.32.0"},
        "/v1/models": {"data": [{
            "id": "JetBrains/Mellum2.1-12B-A2.5B-Thinking",
            "root": "/models/mellum", "max_model_len": 131072, "owned_by": "vllm",
        }]},
    })
    assert server_identity(f"{base}/v1") == {
        "version": "0.32.0",
        "models": [{
            "id": "JetBrains/Mellum2.1-12B-A2.5B-Thinking",
            "root": "/models/mellum", "max_model_len": 131072,
        }],
    }


def test_server_identity_without_a_version_route_keeps_the_models(server):
    """llama.cpp and mlx_lm.server have no /version; the record says so rather than guessing."""
    base = server({"/v1/models": {"data": [{"id": "m"}]}})
    assert server_identity(f"{base}/v1") == {"version": None, "models": [{"id": "m"}]}


def test_server_identity_on_a_dead_server_records_the_error():
    record = server_identity("http://127.0.0.1:9/v1", timeout=1)
    assert record["models"] is None
    assert record["error"]


def _fake_nvidia_smi(tmp_path, output, code=0):
    script = tmp_path / "nvidia-smi"
    script.write_text(f"#!/bin/sh\nprintf '{output}'\nexit {code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return {**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}"}


def test_gpu_identity_reads_every_gpu(tmp_path):
    env = _fake_nvidia_smi(
        tmp_path,
        "NVIDIA H100 80GB HBM3, 81559, 570.86.15\\nNVIDIA H100 80GB HBM3, 81559, 570.86.15\\n",
    )
    assert gpu_identity(env=env) == [
        {"name": "NVIDIA H100 80GB HBM3", "memory_mib": 81559, "driver": "570.86.15"},
    ] * 2


def test_gpu_identity_without_nvidia_smi_is_none(tmp_path):
    assert gpu_identity(env={"PATH": str(tmp_path)}) is None


def test_gpu_identity_when_nvidia_smi_fails_is_none(tmp_path):
    assert gpu_identity(env=_fake_nvidia_smi(tmp_path, "no devices", code=9)) is None
