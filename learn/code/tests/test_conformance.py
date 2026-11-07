"""The Mac's conformance check (F.5, from LC.39): a host card says whether a host's sessions may count."""
import hashlib
import json
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conformance

MODEL = "Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf"


class FakeLlama(BaseHTTPRequestHandler):
    """Just enough of llama-server's API for the conformance check."""
    build_info = "b12110-cd959bae9"
    model_path = f"/models/{MODEL}"
    n_ctx = 50176
    slots = 2
    ignore_max_tokens = False
    status = 200

    def log_message(self, *args):
        pass

    def reply(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status); self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path == "/props":
            self.reply({"build_info": self.build_info, "model_path": self.model_path,
                        "chat_template": "{{ messages }}", "total_slots": self.slots})
        elif self.path == "/slots":
            self.reply([{"id": i, "n_ctx": self.n_ctx, "is_processing": False} for i in range(self.slots)])
        else:
            self.reply({}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        words = sum(len(str(m.get("content", "")).split()) for m in body["messages"])
        tokens = 32 if self.ignore_max_tokens else min(body.get("max_tokens", 32), 32)
        message = {"role": "assistant", "content": "ok", "reasoning_content": "thinking"}
        if body.get("tools"):
            message["tool_calls"] = [{"id": "1", "type": "function",
                                      "function": {"name": body["tools"][0]["function"]["name"], "arguments": "{}"}}]
        self.reply({"choices": [{"message": message}], "usage": {"prompt_tokens": words, "completion_tokens": tokens},
                    "timings": {"prompt_per_second": 900.0, "predicted_per_second": 80.0}}, self.status)


@pytest.fixture
def server():
    handler = type("Handler", (FakeLlama,), {})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield handler, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def stub(path: Path, text: str) -> Path:
    path.write_text(text)
    path.chmod(0o755)
    return path


@pytest.fixture
def host(tmp_path):
    model = tmp_path / MODEL
    model.write_bytes(b"weights")
    pins = conformance.load_pins()
    pins["weights"]["sha256"] = hashlib.sha256(b"weights").hexdigest()
    pins["tooling"] = {"pi": "1.4.0", "node": "25.8.1", "uv": "0.11.6"}
    tools = tmp_path / "bin"
    tools.mkdir()
    stub(tools / "node", "#!/bin/sh\necho v25.8.1\n")
    stub(tools / "uv", "#!/bin/sh\necho 'uv 0.11.6 (abc 2026-04-09)'\n")
    pi = stub(tools / "pi", "#!/bin/sh\necho 1.4.0\n")
    # Metal and CPU agree within 0.57%, as measured on b12110.
    perplexity = stub(tmp_path / "llama-perplexity", '#!/bin/sh\ncase "$*" in\n'
                      '  --version) echo "version: 0.9.0 (build 12110, commit cd959bae9)" ;;\n'
                      '  *"-ngl 0"*) echo "Final estimate: PPL = 15.9176 +/- 0.86848" ;;\n'
                      '  *) echo "Final estimate: PPL = 16.0085 +/- 0.87578" ;;\nesac\n')
    command = conformance.server_argv(pins, binary="llama-server", model=str(model), port=8001, threads=16, log="/l")
    return {"pins": pins, "model": model, "perplexity": perplexity, "pi": pi, "tools": str(tools),
            "out": tmp_path / "card" / "host-card.json", "command": command}


def run_check(server, host, **options):
    _, endpoint = server
    return conformance.check(host["pins"], endpoint, model=host["model"], perplexity_binary=host["perplexity"],
                             server_command=options.pop("server_command", host["command"]),
                             pi_binary=str(host["pi"]), tool_path=host["tools"], out=host["out"], **options)


def test_parse_perplexity_and_its_chunks():
    assert conformance.parse_perplexity("...\nFinal estimate: PPL = 7.1234 +/- 0.05123\n") == 7.1234
    with pytest.raises(ValueError):
        conformance.parse_perplexity("[1]14.4634,[2]nan,")
    assert conformance.perplexity_chunks("[1]14.4634,[2]nan,[3]nan,") == [14.4634, None, None]


def test_identity_problems():
    pins = conformance.load_pins()
    props = {"build_info": "b12110-cd959bae9", "model_path": f"/m/{MODEL}"}
    slots = [{"id": 0, "n_ctx": 50176}, {"id": 1, "n_ctx": 50176}]
    assert conformance.identity_problems(props, slots, pins) == []
    assert len(conformance.identity_problems({**props, "build_info": "b11669-620d2225c"}, slots, pins)) == 1
    assert len(conformance.identity_problems(props, [{"id": 0, "n_ctx": 40000}, slots[1]], pins)) == 1
    assert len(conformance.identity_problems(props, slots[:1], pins)) == 1


def test_flags_problems():
    pins = conformance.load_pins()
    argv = conformance.server_argv(pins, binary="llama-server", model="/m.gguf", port=18001, threads=8, log="/l")
    assert conformance.flags_problems(argv, pins) == []
    assert any("-fa" in p for p in conformance.flags_problems([("auto" if a == "on" else a) for a in argv], pins))
    assert conformance.flags_problems([a for a in argv if a != "--no-kv-unified"], pins)


def test_numerics_compares_metal_with_cpu_on_the_same_build():
    ppl = "Final estimate: PPL = {} +/- 0.8"
    assert conformance.numerics_item(ppl.format(16.0085), ppl.format(15.9176), 0.01)["passed"] is True
    assert conformance.numerics_item(ppl.format(16.3), ppl.format(15.9176), 0.01)["passed"] is False
    nan = conformance.numerics_item("[1]14.4634,[2]nan,[3]nan,[4]nan,", ppl.format(15.9176), 0.01)
    assert nan["passed"] is False and nan["detail"]["metal"]["nan_chunks"] == 3


def test_check_against_a_fake_server_writes_a_passing_card(server, host):
    card = run_check(server, host)
    assert card["passed"] is True, card["items"]
    assert card["schema"] == "mellum-host-card/1"
    assert set(card["items"]) == {"identity", "capacity", "protocol", "throughput", "stability", "numerics", "tooling"}
    assert card["items"]["numerics"]["detail"]["relative_drift"] == pytest.approx(0.0057, abs=0.0001)
    assert card["pins_digest"] == conformance.pins_digest(host["pins"])
    assert card["server_command"] == host["command"]
    assert card["slots"] == [50176, 50176]
    assert json.loads(host["out"].read_text()) == card


def test_nan_on_metal_fails_the_card(server, host):
    stub(host["perplexity"], '#!/bin/sh\ncase "$*" in\n  *"-ngl 0"*) echo "Final estimate: PPL = 15.9" ;;\n'
         '  *) echo "[1]14.4634,[2]nan,[3]nan," ;;\nesac\n')
    card = run_check(server, host)
    assert card["items"]["numerics"]["passed"] is False and card["passed"] is False


def test_a_server_that_ignores_max_tokens_fails_protocol(server, host):
    server[0].ignore_max_tokens = True
    card = run_check(server, host)
    assert card["items"]["protocol"]["passed"] is False and card["passed"] is False


def test_wrong_weights_or_unpinned_flags_fail_identity(server, host):
    assert run_check(server, host, server_command=[("auto" if a == "on" else a) for a in host["command"]]
                     )["items"]["identity"]["passed"] is False
    host["model"].write_bytes(b"other weights")
    assert run_check(server, host)["items"]["identity"]["passed"] is False


def test_an_unpinned_pi_fails_tooling(server, host):
    stub(host["pi"], "#!/bin/sh\necho 1.1.0\n")
    assert run_check(server, host)["items"]["tooling"]["passed"] is False


def test_an_unstable_server_fails_stability(server, host):
    server[0].status = 503
    assert run_check(server, host)["items"]["stability"]["passed"] is False


def test_server_command_reads_the_argv_of_the_process_on_a_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    child = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            command = conformance.server_command(port)
            if command:
                break
            time.sleep(0.05)
        assert command[-4:] == ["http.server", str(port), "--bind", "127.0.0.1"]
    finally:
        child.terminate()
        child.wait()
    assert conformance.server_command(port) is None


def test_the_card_names_the_machine_like_run_json_and_not_its_network_name(server, host):
    import platform
    import harness
    card = run_check(server, host)
    assert card["machine"] == harness.machine_label()
    assert platform.node() not in card["machine"]


def test_flags_problems_refuses_unpinned_and_repeated_flags():
    # llama.cpp takes the last of a repeated flag, and an unpinned one changes what is served (final review).
    pins = conformance.load_pins()
    argv = conformance.server_argv(pins, binary="llama-server", model="/m.gguf", port=18001, threads=8, log="/l")
    assert any("--lora" in p for p in conformance.flags_problems([*argv, "--lora", "/x.gguf"], pins))
    assert any("--override-kv" in p for p in conformance.flags_problems([*argv, "--override-kv", "a=int:1"], pins))
    assert any("-ngl" in p for p in conformance.flags_problems([*argv, "-ngl", "0"], pins))


def test_numerics_needs_llama_perplexity_from_the_servers_build(server, host):
    # "Same build" is the point of comparing Metal with CPU (final review).
    text = host["perplexity"].read_text().replace("build 12110, commit cd959bae9", "build 11669, commit 620d2225c")
    stub(host["perplexity"], text)
    item = run_check(server, host)["items"]["numerics"]
    assert item["passed"] is False and "b11669-620d2225c" in item["detail"]["error"]
