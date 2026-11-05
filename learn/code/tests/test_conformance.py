"""Per-rental conformance check (LC.39): a host card says whether a host may count."""
import hashlib
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conformance
import rig


class FakeLlama(BaseHTTPRequestHandler):
    """Just enough of llama-server's API for the conformance check."""
    build_info = "b11669-620d2225c"
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
            self.reply({"build_info": self.build_info, "model_path": "/models/Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf",
                        "chat_template": "{{ messages }}", "total_slots": self.slots})
        elif self.path == "/slots":
            self.reply([{"id": i, "n_ctx": self.n_ctx, "is_processing": False} for i in range(self.slots)])
        elif self.path == "/health":
            self.reply({"status": "ok"})
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
        self.reply({"choices": [{"message": message, "finish_reason": "length" if tokens == body.get("max_tokens") else "stop"}],
                    "usage": {"prompt_tokens": words, "completion_tokens": tokens},
                    "timings": {"prompt_per_second": 900.0, "predicted_per_second": 80.0}}, self.status)


@pytest.fixture
def server():
    handler = type("Handler", (FakeLlama,), {})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield handler, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture
def host(tmp_path):
    model = tmp_path / "Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf"
    model.write_bytes(b"weights")
    pins = rig.load_pins()
    pins["weights"]["sha256"] = hashlib.sha256(b"weights").hexdigest()
    perplexity = tmp_path / "llama-perplexity"
    perplexity.write_text("#!/bin/sh\necho 'Final estimate: PPL = 7.1234 +/- 0.05123'\n")
    perplexity.chmod(0o755)
    prefix = tmp_path / "rig"
    (prefix / "bin").mkdir(parents=True)
    for name, text in {"node": "v24.22.1", "pi": "1.4.0", "uv": "uv 0.11.6", "python3.14": "Python 3.14.2"}.items():
        stub = prefix / "bin" / name
        stub.write_text(f"#!/bin/sh\necho '{text}'\n"); stub.chmod(0o755)
    return {"pins": pins, "model": model, "perplexity": perplexity, "out": tmp_path / "card/host-card.json",
            "prefix": str(prefix),
            "host": {"provider": "local", "region": "here", "rental_id": "mac", "price_per_hour": 0, "threads": 16,
                     "gpu": "metal"}}


def run_check(server, host, **options):
    handler, endpoint = server
    return conformance.check(host["pins"], endpoint, perplexity_binary=host["perplexity"], model=host["model"],
                             reference_ppl=options.pop("reference_ppl", None), tolerance=0.01, host=host["host"],
                             out=host["out"], prefix=host["prefix"], **options)


def test_parse_perplexity():
    assert conformance.parse_perplexity("...\nFinal estimate: PPL = 7.1234 +/- 0.05123\n") == 7.1234
    with pytest.raises(ValueError):
        conformance.parse_perplexity("no estimate here")


def test_identity_problems():
    pins = rig.load_pins()
    props = {"build_info": "b11669-620d2225c", "model_path": "/m/Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf"}
    slots = [{"id": 0, "n_ctx": 50176}, {"id": 1, "n_ctx": 50176}]
    assert conformance.identity_problems(props, slots, pins) == []
    assert len(conformance.identity_problems({**props, "build_info": "b9999-x"}, slots, pins)) == 1
    assert len(conformance.identity_problems(props, [{"id": 0, "n_ctx": 40000}, slots[1]], pins)) == 1
    assert len(conformance.identity_problems(props, slots[:1], pins)) == 1


def test_check_against_fake_server(server, host):
    card = run_check(server, host)
    assert card["passed"] is True, card["items"]
    assert set(card["items"]) == {"identity", "capacity", "protocol", "numerics", "throughput", "stability",
                                  "tooling", "isolation"}
    assert card["items"]["numerics"]["detail"]["perplexity"] == 7.1234
    assert card["items"]["numerics"]["detail"]["role"] == "reference"
    assert card["pins_digest"] == rig.pins_digest(host["pins"])
    assert card["post_check"] is None and card["stopped"] is None
    assert json.loads(host["out"].read_text()) == card


def test_check_fails_when_max_tokens_ignored(server, host):
    server[0].ignore_max_tokens = True
    card = run_check(server, host)
    assert card["items"]["protocol"]["passed"] is False and card["passed"] is False


def test_numerics_out_of_tolerance_fails(server, host):
    card = run_check(server, host, reference_ppl=6.5)
    assert card["items"]["numerics"]["passed"] is False and card["passed"] is False
    assert run_check(server, host, reference_ppl=7.13)["items"]["numerics"]["passed"] is True


def test_wrong_weights_fail_identity(server, host):
    host["model"].write_bytes(b"other weights")
    card = run_check(server, host)
    assert card["items"]["identity"]["passed"] is False


def test_unpinned_tools_fail_tooling(server, host):
    (Path(host["prefix"]) / "bin/pi").write_text("#!/bin/sh\necho 1.1.0\n")
    assert run_check(server, host)["items"]["tooling"]["passed"] is False


def test_unstable_server_fails_stability(server, host):
    server[0].status = 503
    assert run_check(server, host)["items"]["stability"]["passed"] is False
