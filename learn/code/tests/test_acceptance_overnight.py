"""Overnight collection policy is bounded independently of model behavior."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "learn/code"))
spec = importlib.util.spec_from_file_location("acceptance_overnight", ROOT / "scripts/acceptance_overnight.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_fixed_cohort_and_no_start_without_full_allowance():
    assert module.ORDER == ["selective", "gated"] * 20
    assert module.may_start(661) and not module.may_start(659)


def test_changed_frozen_input_is_rejected(tmp_path):
    path = tmp_path / "source"; path.write_text("original")
    freeze = module.freeze_files([path]); path.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        module.verify_files(freeze)


def test_identity_mismatch_never_stops_unrelated_process(monkeypatch):
    monkeypatch.setattr(module.baseline, "process_identity", lambda pid: {"pid": pid, "start": "other"})
    monkeypatch.setattr(module.os, "kill", lambda *a: pytest.fail("unrelated process signalled"))
    assert not module.stop_owned({"pid": 9999, "start": "expected"})


def test_refuse_occupied_inference_port(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="other listener"))
    with pytest.raises(ValueError, match="occupied"):
        module.require_free_port()


def test_recovery_includes_control_arm_audits_without_scanning_artifacts(tmp_path, monkeypatch):
    audit = tmp_path / "selective/audit-vanilla-easy-test"
    audit.mkdir(parents=True)
    visited = []
    monkeypatch.setattr(module.containment, "recover", lambda path: visited.append(path))
    module.recover_owned(tmp_path)
    assert audit in visited


def test_candidate_requires_full_cohort_and_known_budgets():
    def summary(n=20, usable=18, budget=100):
        return {"n": n, "usable": usable, "output_per_usable": budget, "reconciled": True}
    assert module.decide({"selective": summary(usable=17), "gated": summary()}) == "candidate"
    assert module.decide({"selective": summary(), "gated": summary(n=19)}) == "no_decision"
    assert module.decide({"selective": summary(), "gated": summary(budget=None)}) == "no_decision"
    assert module.decide({"selective": summary(usable=19), "gated": summary()}) == "not_candidate"
    assert module.decide({"selective": summary(), "gated": summary(budget=101)}) == "not_candidate"
