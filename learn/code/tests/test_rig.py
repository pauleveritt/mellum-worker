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


def joined(commands):
    return "\n".join(commands)


def test_checkout_is_exact_commit():
    commands = rig.checkout_commands("https://example.test/repo.git", "abc123", "/root/mellum-worker")
    assert any("checkout --detach abc123" in c for c in commands)
    assert "rev-parse HEAD" in commands[-1] and "abc123" in commands[-1]


def test_bootstrap_checks_node_hash_before_extracting():
    commands = rig.bootstrap_commands(rig.load_pins(), prefix="/opt/rig", repo="/root/mellum-worker")
    check = next(i for i, c in enumerate(commands) if "sha256sum --check" in c and "node-v24.22.1" in c)
    extract = next(i for i, c in enumerate(commands) if c.startswith("tar -x") and "node-v24.22.1" in c)
    assert check < extract
    assert "6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6" in commands[check]


def test_bootstrap_installs_exact_versions():
    text = joined(rig.bootstrap_commands(rig.load_pins(), prefix="/opt/rig", repo="/root/mellum-worker"))
    assert "@earendil-works/pi-coding-agent@1.4.0" in text
    assert "uv/0.11.6/install.sh" in text and "python install 3.14.2" in text
    assert "sync --frozen" in text and "/root/mellum-worker/learn/code/suites/easy/base" in text
    for pinned in ("ruff@0.16.3", "complexipy@8.3.0", "pyrefly@1.2.0", "pytest@8.3.4"):
        assert pinned in text


def test_build_commands_pin_commit_and_native_off():
    text = joined(rig.build_commands(rig.load_pins(), prefix="/opt/rig"))
    assert "620d2225cc436ab0b001e3200e590e3b286ef9ab" in text and "-DGGML_NATIVE=OFF" in text
    assert "-DCMAKE_CUDA_ARCHITECTURES='80;86;89;90;100;120'" in text
    assert "llama-server" in text and "llama-perplexity" in text
    assert "build 11669" in text  # the built binary must report the pinned build


def test_fetch_weights_checks_hash():
    commands = rig.fetch_weights_commands(rig.load_pins(), dest="/root/models")
    assert "/resolve/4159d684ffdb09ba89dc2a58feb3e75c54eef036/" in commands[-2]
    assert "sha256sum --check" in commands[-1]
    assert "ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755" in commands[-1]


def test_serve_commands_use_server_argv():
    pins = rig.load_pins()
    argv = rig.server_argv(pins, binary="/opt/rig/bin/llama-server", model="/m.gguf", port=18001, threads=8, log="/l")
    command = joined(rig.serve_commands(pins, binary="/opt/rig/bin/llama-server", model="/m.gguf",
                                        port=18001, threads=8, log="/l"))
    assert shlex.join(argv) in command and "tmux new-session -d -s mellum-rig" in command
    assert rig.stop_server_commands() == ["tmux kill-session -t mellum-rig"]


def test_user_commands_create_both_users_without_sudo():
    text = joined(rig.user_commands())
    for user in ("mellum-session", "mellum-grade"):
        assert f"useradd --create-home --shell /bin/bash {user}" in text
        assert f"passwd --lock {user}" in text
    assert "sudo" not in text


def test_tool_versions_reads_each_tool(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    outputs = {"node": "v24.22.1", "pi": "1.4.0", "uv": "uv 0.11.6 (abc 2026-01-01)",
               "python3.14": "Python 3.14.2"}
    for name, text in outputs.items():
        script = bin_dir / name
        script.write_text(f"#!/bin/sh\necho '{text}'\n")
        script.chmod(0o755)
    versions = rig.tool_versions(str(tmp_path))
    assert versions["node"] == "24.22.1" and versions["pi"] == "1.4.0"
    assert versions["uv"] == "0.11.6" and versions["python"] == "3.14.2"


def test_tool_versions_reports_missing_tool(tmp_path):
    (tmp_path / "bin").mkdir()
    assert rig.tool_versions(str(tmp_path))["node"] is None
