"""The host, not a model-side counter or acknowledgement, owns acceptance."""
import hashlib
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from acceptance import AcceptancePackage, Gate


def package(tmp_path):
    root = tmp_path / "oracle"
    root.mkdir()
    (root / "checker.py").write_text("# trusted\n")
    (root / "spec.md").write_text("Public requirements\n")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
    data = {"schema": 1, "checker": "checker.py", "timeout": 30,
            "requirements": {"home": "home responds", "tests": "tests run"},
            "files": files, "spec_hashes": {"spec.md": files["spec.md"]}}
    (root / "manifest.json").write_text(json.dumps(data))
    return AcceptancePackage.load(root)


def verdict(passed=True):
    return {"status": "pass" if passed else "fail", "checks": {
        "home": {"passed": passed, "observation": "observed response"},
        "tests": {"passed": True, "observation": "one test passed"}}}


def test_initial_pass_is_provisional_until_final_snapshot(tmp_path):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    first = gate.apply(verdict(), "a" * 64)
    assert first["status"] == "verified"
    assert not first["continue"]
    assert gate.apply(verdict(), "b" * 64, final=True)["status"] == "accepted"
    assert len(gate.journal) == 2
    assert gate.journal[-1]["snapshot_sha256"] == "b" * 64


def test_two_repairs_and_last_failure_are_retained(tmp_path):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    assert gate.apply(verdict(False), "a" * 64)["continue"]
    assert gate.apply(verdict(False), "b" * 64)["continue"]
    third = gate.apply(verdict(False), "c" * 64)
    assert third["status"] == "repair_exhausted" and not third["continue"]
    assert gate.repairs == 2 and len(gate.journal) == 3
    assert gate.apply(verdict(False), "c" * 64, final=True)["status"] == "repair_exhausted"
    assert not gate.apply(verdict(), "d" * 64)["continue"]


def test_final_recheck_cannot_repair_or_ignore_mutation(tmp_path):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    gate.apply(verdict(), "a" * 64)
    final = gate.apply(verdict(False), "b" * 64, final=True)
    assert final["status"] == "repair_exhausted" and not final["continue"]
    assert gate.repairs == 0


def test_shared_deadline_is_not_reset(tmp_path):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    gate.apply(verdict(False), "a" * 64)
    gate.deadline_at = time.monotonic() - 1
    decision = gate.apply(verdict(), "a" * 64, final=True)
    assert decision["status"] == "deadline" and not decision["continue"]
    assert gate.remaining() == 0


@pytest.mark.parametrize("bad", [
    {}, {"status": "pass", "checks": {}},
    {"status": "pass", "checks": {"home": {"passed": True}}},
    {"status": "pass", "checks": {**verdict()["checks"], "extra": {"passed": True}}},
    {"status": "pass", "checks": {"home": {"passed": 1}, "tests": {"passed": True}}},
    {"status": "pass", "checks": verdict(False)["checks"]},
    {"status": "unknown"}, {"status": []}, {"status": {}},
])
def test_invalid_result_is_terminal_and_never_accepted(tmp_path, bad):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    assert gate.apply(bad, "a" * 64)["status"] == "checker_error"
    assert gate.apply(verdict(), "a" * 64, final=True)["status"] == "checker_error"
    assert gate.repairs == 0


@pytest.mark.parametrize("status", ["checker_error", "timeout", "integrity_error"])
def test_checker_errors_do_not_request_repairs(tmp_path, status):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    result = gate.apply({"status": status}, "a" * 64)
    assert result["status"] == status and not result["continue"]


def test_changed_package_cannot_pass(tmp_path):
    oracle = package(tmp_path)
    (oracle.root / "checker.py").write_text("# weakened\n")
    gate = Gate("task", oracle, time.monotonic() + 600)
    assert gate.apply(verdict(), "a" * 64)["status"] == "integrity_error"


@pytest.mark.parametrize("field,value", [("timeout", True), ("timeout", float("nan")),
    ("timeout", 0), ("timeout", 31), ("requirements", {}), ("schema", True)])
def test_invalid_package_is_rejected(tmp_path, field, value):
    oracle = package(tmp_path)
    path = oracle.root / "manifest.json"
    data = json.loads(path.read_text()); data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        AcceptancePackage.load(oracle.root)


@pytest.mark.parametrize("name", ["../escape.py", "/tmp/checker.py", "linked.py"])
def test_package_rejects_escaping_and_symlink_files(tmp_path, name):
    oracle = package(tmp_path)
    (oracle.root / "linked.py").symlink_to(oracle.root / "checker.py")
    path = oracle.root / "manifest.json"; data = json.loads(path.read_text())
    data["files"][name] = "a" * 64; path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        AcceptancePackage.load(oracle.root)


def test_feedback_is_bounded_and_only_failed_requirements(tmp_path):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    result = verdict(False); result["checks"]["home"]["observation"] = "x" * 20000
    decision = gate.apply(result, "a" * 64)
    assert len(decision["feedback"]) <= 8000
    assert "home" in decision["feedback"] and "one test passed" not in decision["feedback"]


def test_duplicate_final_receipt_cannot_reaffirm_acceptance(tmp_path):
    gate = Gate("task", package(tmp_path), time.monotonic() + 600)
    assert gate.apply(verdict(), "a" * 64, final=True)["status"] == "accepted"
    assert gate.apply(verdict(), "a" * 64, final=True)["status"] == "integrity_error"


@pytest.mark.parametrize("repairs", [True, -1, 3, 1.5])
def test_invalid_repair_allowance_is_rejected(tmp_path, repairs):
    with pytest.raises(ValueError):
        Gate("task", package(tmp_path), time.monotonic() + 600, max_repairs=repairs)


def test_repair_feedback_requires_agnostic_cleanup_and_current_task_scope(tmp_path):
    gate = Gate('task', package(tmp_path), time.monotonic() + 600)
    feedback = gate.apply(verdict(False), 'a' * 64)['feedback'].lower()
    for instruction in ('current task', 'remove', 'out-of-scope', 'revert', 'protected', 'later', 'untrusted'):
        assert instruction in feedback
    for answer in ('app.py', 'models.py', '/complaints', 'uvicorn', 'phase 1', 'one test passed'):
        assert answer not in feedback
    assert len(feedback) <= 8000
