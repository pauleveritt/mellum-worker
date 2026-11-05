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


def test_recovery_includes_live_qualification_task(tmp_path, monkeypatch):
    live = tmp_path / "live-qualification"; live.mkdir()
    visited = []
    monkeypatch.setattr(module.containment, "recover", lambda path: visited.append(path))
    module.recover_owned(tmp_path)
    assert live in visited


def test_guardian_owns_launch_and_stops_server_if_ownership_write_fails(tmp_path, monkeypatch):
    from types import SimpleNamespace
    identity = {"pid": 9999, "start": "fixture"}
    (tmp_path / "server-launch.json").write_text(__import__("json").dumps({
        "controller": identity, "argv": ["fixture"], "cutoff_epoch": 1e15}))
    calls = []
    class Process:
        pid = 1234
        returncode = 0
        def poll(self): return None
        def terminate(self): calls.append("terminate")
        def wait(self, timeout=None): calls.append("wait"); return 0
        def kill(self): calls.append("kill")
    monkeypatch.setattr(module.baseline, "process_identity", lambda pid: identity)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *a, **k: Process())
    monkeypatch.setattr(module, "write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("write failed")))
    with pytest.raises(OSError, match="write failed"):
        module.watchdog(tmp_path)
    assert "terminate" in calls and "wait" in calls


def test_real_guardian_stops_owned_dummy_server_on_controller_death(tmp_path):
    import json
    import subprocess
    import time
    controller = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    guardian = None
    server_identity = None
    try:
        (tmp_path / "server-launch.json").write_text(json.dumps({
            "controller": module.baseline.process_identity(controller.pid),
            "argv": [sys.executable, "-c", "import time; time.sleep(60)"],
            "cutoff_epoch": time.time() + 30}))
        guardian = subprocess.Popen([sys.executable, str(ROOT / "scripts/acceptance_overnight.py"),
                                     "--watchdog", str(tmp_path)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        until = time.monotonic() + 5
        while not (tmp_path / "server-owner.json").exists():
            assert guardian.poll() is None
            assert time.monotonic() < until
            time.sleep(.02)
        server_identity = json.loads((tmp_path / "server-owner.json").read_text())["server"]
        controller.terminate(); controller.wait(timeout=5)
        guardian.wait(timeout=10)
        assert guardian.returncode == 0, guardian.stderr.read()
        assert module.baseline.process_identity(server_identity["pid"]) != server_identity
        assert (tmp_path / "watchdog-shutdown.json").is_file()
    finally:
        if controller.poll() is None: controller.kill(); controller.wait()
        if server_identity is not None: module.stop_owned(server_identity)
        if guardian is not None and guardian.poll() is None: guardian.kill(); guardian.wait()


def test_candidate_requires_full_cohort_and_known_budgets():
    def summary(n=20, usable=18, budget=100):
        return {"n": n, "usable": usable, "output_per_usable": budget, "reconciled": True}
    assert module.decide({"selective": summary(usable=17), "gated": summary()}) == "candidate"
    assert module.decide({"selective": summary(), "gated": summary(n=19)}) == "no_decision"
    assert module.decide({"selective": summary(), "gated": summary(budget=None)}) == "no_decision"
    assert module.decide({"selective": summary(usable=19), "gated": summary()}) == "not_candidate"
    assert module.decide({"selective": summary(), "gated": summary(budget=101)}) == "not_candidate"


@pytest.fixture(autouse=True)
def reset_cohort():
    # Module globals are also the CLI-selected cohort contract.
    yield
    if hasattr(module, "configure_mode"):
        module.configure_mode("--prepare")


@pytest.mark.parametrize("mode,kind,order,protocol", [
    ("--prepare", "comparison", ["selective", "gated"] * 20,
     "2026-11-05-actionable-acceptance-protocol.md"),
    ("--prepare-screen", "screen", ["gated"] * 6,
     "2026-11-05-runtime-repair-screen-protocol.md"),
])
def test_prepare_registers_actual_selected_cohort(tmp_path, monkeypatch, mode, kind, order, protocol):
    import json
    import acceptance_qualification
    import acceptance_runtime_qualification
    import containment_qualification
    def build(*args, **kwargs):
        kwargs["stdout"].write("sha256:" + "a" * 64 + "\n")
    monkeypatch.setattr(module.subprocess, "run", build)
    monkeypatch.setattr(module.containment, "image_info", lambda _: {})
    monkeypatch.setattr(containment_qualification, "qualify", lambda *a: {"qualified": True, "material": {}})
    monkeypatch.setattr(acceptance_qualification, "qualify", lambda *a: {"qualified": True})
    monkeypatch.setattr(acceptance_runtime_qualification, "qualify", lambda *a: {"qualified": True})
    monkeypatch.setattr(acceptance_runtime_qualification, "qualify_compaction", lambda *a: {"qualified": True})
    assert module.configure_mode(mode) == "--prepare"
    module.prepare(tmp_path)
    prepared = json.loads((tmp_path / "prepared.json").read_text())
    assert prepared["order"] == order
    assert prepared["collection"] == module.cohort_config()
    assert prepared["collection"]["kind"] == kind
    assert prepared["collection"]["counts"] == {arm: order.count(arm) for arm in ("selective", "gated")}
    assert prepared["collection"]["n_per_arm"] == (20 if kind == "comparison" else None)
    assert Path(prepared["protocol"]).name == protocol
    assert prepared["freeze"][prepared["protocol"]] == module.baseline.sha256(Path(prepared["protocol"]))
    assert module.collection_state(len(order)) == "complete"
    assert module.collection_state(len(order) - 1) == "incomplete"


def test_screen_never_promotes_even_favorable_full_comparison():
    module.configure_mode("--run-screen")
    row = {"n": 20, "usable": 20, "output_per_usable": 1, "reconciled": True}
    assert module.decide({"selective": row, "gated": row}) == "screen_only"


@pytest.mark.parametrize("changed", ["order", "collection", "protocol"])
def test_collect_rejects_wrong_cohort_before_start(tmp_path, changed):
    import json
    module.configure_mode("--run-screen")
    prepared = {"qualified": True, "freeze": {}, "order": list(module.ORDER),
                "collection": module.cohort_config(), "protocol": str(module.FOLLOWUP_PROTOCOL)}
    prepared[changed] = {"order": [], "collection": {"kind": "comparison"}, "protocol": "wrong"}[changed]
    (tmp_path / "prepared.json").write_text(json.dumps(prepared))
    with pytest.raises(ValueError, match="preparation"):
        module.collect(tmp_path)
    assert not (tmp_path / "server-launch.json").exists()
