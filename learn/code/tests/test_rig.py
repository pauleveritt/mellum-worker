"""The portable rig's pin card: one source for what every host serves and bootstraps."""
import json
import shlex
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rig


def test_pins_carry_frozen_identity():
    pins = rig.load_pins()
    assert pins["weights"]["sha256"] == "ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755"
    assert pins["weights"]["revision"] == "4159d684ffdb09ba89dc2a58feb3e75c54eef036"
    assert pins["build"]["build_info"] == "b11669-620d2225c"
    assert pins["acceptance_package_sha256"] == "af4122164322e6446b5cb12728693ca32749fdaec2606aa35e1bcaf9e41e3dd9"
    assert pins["session"] == {"max_requests": 120, "max_output_tokens": 64000, "max_tokens_per_request": 16384,
                               "unknown_usage_charge": 16384, "open_tool_seconds": 180, "wall_safety_seconds": 3600}
    boot = pins["bootstrap"]
    assert (boot["node"]["version"], boot["uv"], boot["python"], boot["pi"]) == (
        "24.22.1", "0.11.6", "3.14.2", "@earendil-works/pi-coding-agent@1.4.0")
    assert boot["checkers"] == {"ruff": "0.16.3", "complexipy": "8.3.0", "pyrefly": "1.2.0", "pytest": "8.3.4"}
    assert pins["client"]["max_tokens"] == 16384 and pins["client"]["temperature"] == 1.0


def test_load_pins_refuses_auto_flash_attention(tmp_path):
    pins = json.loads(rig.PINS.read_text())
    pins["server"]["flash_attention"] = "auto"
    path = tmp_path / "pins.json"
    path.write_text(json.dumps(pins))
    with pytest.raises(ValueError, match="flash_attention"):
        rig.load_pins(path)


def test_load_pins_names_missing_key(tmp_path):
    pins = json.loads(rig.PINS.read_text())
    del pins["session"]
    path = tmp_path / "pins.json"
    path.write_text(json.dumps(pins))
    with pytest.raises(ValueError, match="session"):
        rig.load_pins(path)


def test_server_argv_matches_frozen_set():
    argv = rig.server_argv(rig.load_pins(), binary="llama-server", model="/m.gguf", port=18001, threads=16, log="/l")
    assert argv[argv.index("-fa") + 1] == "on" and argv[argv.index("-np") + 1] == "2"
    assert argv[argv.index("-c") + 1] == "100000" and "--no-kv-unified" in argv and "auto" not in argv
    assert argv[:3] == ["llama-server", "-m", "/m.gguf"]
    assert argv[argv.index("--port") + 1] == "18001" and argv[argv.index("-t") + 1] == "16"
    assert argv[argv.index("--host") + 1] == "127.0.0.1"


def test_pins_digest_changes_with_any_value():
    pins = rig.load_pins()
    changed = json.loads(json.dumps(pins))
    changed["session"]["max_requests"] = 121
    assert rig.pins_digest(pins) != rig.pins_digest(changed)
    assert rig.pins_digest(pins) == rig.pins_digest(json.loads(json.dumps(pins)))
