"""Control input is untrusted; paths and counters are selected by the host."""
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import containment
import harness
from acceptance_containment import parse_request, snapshot_digest
from test_acceptance import package


def request(**changes):
    return json.dumps({"task_id": "task", "request_id": "a" * 32, "sequence": 1, **changes})


@pytest.mark.parametrize("raw", ["[]", "bad", "x" * 20000,
    request(task_id="other"), request(sequence=True), request(sequence=2),
    request(request_id="../escape"), request(workspace="/tmp/selected-by-model")])
def test_invalid_mailbox_is_rejected(raw):
    with pytest.raises(ValueError):
        parse_request(raw, task_id="task", sequence=1)


def test_valid_mailbox_contains_no_executable_or_path_selection():
    assert parse_request(request(), task_id="task", sequence=1)["request_id"] == "a" * 32


def test_exec_requires_explicit_stdin_forwarding_for_probe_and_reply(tmp_path):
    container = containment.Container("image", tmp_path)
    container.cid = "id"
    assert "-i" in container.exec_argv("node", interactive=True)
    assert "-i" not in container.exec_argv("node")


def test_model_image_source_allowlist_never_contains_task_checkers_or_fixtures():
    paths = containment.image_instrument_sources()
    assert containment.REPO / "learn/code/harness.py" in paths
    assert not any("qualification" in p.name or p.parent.name == "easy-phase1" for p in paths)


def test_snapshot_always_unpauses_even_when_extraction_fails(tmp_path, monkeypatch):
    events = []
    instance = containment.Container("image", tmp_path)
    instance.cid = "id"
    def export(*args):
        events.append("export")
        raise ValueError("unsafe export")
    monkeypatch.setattr(instance, "export", export)
    monkeypatch.setattr(containment, "docker", lambda *a, **k: events.append(a[0]))
    with pytest.raises(ValueError):
        instance.snapshot("/attempt/workspace", tmp_path / "snapshot")
    assert events == ["export", "unpause"]


def test_snapshot_digest_covers_paths_and_contents(tmp_path):
    (tmp_path / "a").write_text("first")
    first = snapshot_digest(tmp_path)
    (tmp_path / "a").write_text("second")
    assert snapshot_digest(tmp_path) != first
    (tmp_path / "a").rename(tmp_path / "b")
    assert snapshot_digest(tmp_path) != first


def test_native_run_cannot_silently_load_unprotected_gate(tmp_path):
    suite = harness.load_suite(harness.SUITES, "easy")
    with pytest.raises(ValueError, match="controller"):
        harness.run_suite(suite, runs_dir=tmp_path, arm="vanilla", pi_binary="must-not-start",
                          extras=[containment.REPO / "remedies/check/external-acceptance.ts"])


def test_host_bounds_a_hung_trusted_checker_before_candidate_creation(tmp_path):
    import hashlib
    from acceptance import AcceptancePackage
    from acceptance_containment import check_snapshot
    oracle = package(tmp_path)
    source = oracle.root / "checker.py"
    source.write_text("import time\ntime.sleep(10)\n")
    manifest = json.loads((oracle.root / "manifest.json").read_text())
    manifest["files"]["checker.py"] = hashlib.sha256(source.read_bytes()).hexdigest()
    (oracle.root / "manifest.json").write_text(json.dumps(manifest))
    oracle = AcceptancePackage.load(oracle.root)
    started = time.monotonic()
    result = check_snapshot(tmp_path, oracle, "must-not-create", tmp_path / "control", .2)
    assert result["status"] == "timeout"
    assert time.monotonic() - started < 3
