"""The floor cohort driver (LC.39), driven with fakes: no model, no server, no rental."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "learn/code"))
spec = importlib.util.spec_from_file_location("floor_cohort", ROOT / "scripts/floor_cohort.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
import rig


@pytest.fixture
def batch(tmp_path):
    root = tmp_path / "batch"
    root.mkdir()
    (root / "prepared.json").write_text(json.dumps({"pins_digest": rig.pins_digest(rig.load_pins()), "freeze": {}}))
    return root


def add_host(batch: Path, name: str, *, passed=True, digest=None, rental="r1"):
    card = {"passed": passed, "pins_digest": digest or rig.pins_digest(rig.load_pins()), "rental_id": rental,
            "provider": "runpod", "post_check": None, "stopped": None}
    folder = batch / "hosts" / name / rental
    folder.mkdir(parents=True)
    (folder / "host-card.json").write_text(json.dumps(card))
    (folder / "host.json").write_text(json.dumps({"name": name, "rental_id": rental}))


def scripted(outcomes, calls):
    """A fake session runner that returns preset validity states, and checks it is never re-entered."""
    state = {"active": False}
    def run_one(batch, name, config, card, pins, index):
        assert not state["active"], "two sessions overlapped on one host"
        state["active"] = True
        try:
            valid, reason = outcomes.pop(0)
            calls.append(index)
            return {"type": "session", "host": name, "rental_id": card["rental_id"], "run": f"run-{index}",
                    "state": valid, "reason": reason, "record": {"usable": False, "completion": "settled",
                    "hidden_all_pass": True, "acceptance_checks": {"startup": True}}}
        finally:
            state["active"] = False
    return run_one


def test_run_refuses_a_host_without_a_usable_card(batch, monkeypatch):
    add_host(batch, "A", passed=False)
    monkeypatch.setattr(driver, "run_one", scripted([], []))
    with pytest.raises(SystemExit, match="conformance"):
        driver.run(batch, "A")
    add_host(batch, "B", digest="0" * 64)
    with pytest.raises(SystemExit, match="pin card"):
        driver.run(batch, "B")


def test_run_collects_the_planned_count_sequentially(batch, monkeypatch):
    add_host(batch, "M")
    calls = []
    monkeypatch.setattr(driver, "run_one", scripted([("counted", "")] * 3, calls))
    driver.run(batch, "M")
    assert calls == [1, 2, 3]
    assert sum(e["state"] == "counted" for e in driver.events(batch) if e["type"] == "session") == 3


def test_run_replaces_only_invalid_sessions_at_most_twice(batch, monkeypatch):
    add_host(batch, "A")
    outcomes = [("counted", ""), ("invalid", "sweep or preflight failed"), ("counted", ""),
                ("invalid", "reached the wall safety net"), ("invalid", "unrecovered transport error")]
    calls = []
    monkeypatch.setattr(driver, "run_one", scripted(outcomes, calls))
    driver.run(batch, "A")
    kinds = [e["type"] for e in driver.events(batch)]
    assert kinds.count("session") == 5 and kinds[-1] == "host_stopped"
    assert sum(e.get("state") == "counted" for e in driver.events(batch)) == 2


def test_resumed_run_does_not_recount(batch, monkeypatch):
    add_host(batch, "M")
    calls = []
    monkeypatch.setattr(driver, "run_one", scripted([("counted", "")] * 2, calls))
    with pytest.raises(IndexError):           # the runner "dies" after two sessions
        driver.run(batch, "M")
    monkeypatch.setattr(driver, "run_one", scripted([("counted", "")], calls))
    driver.run(batch, "M")
    assert calls == [1, 2, 3]


def test_report_puts_per_host_tables_before_pooled(batch, monkeypatch):
    for name in ("A", "B", "M"):
        add_host(batch, name)
        monkeypatch.setattr(driver, "run_one", scripted([("counted", "")] * driver.floor.PLAN[name], []))
        driver.run(batch, name)
    driver.report(batch)
    summary = json.loads((batch / "summary.json").read_text())
    assert list(summary) == ["per_host", "pooled_cuda", "pooled_all"]
    assert summary["pooled_all"]["n"] == 15
    portability = json.loads((batch / "portability.json").read_text())
    assert portability["portable"] is True
    scorecard = (batch / "scorecard.md").read_text()
    assert scorecard.index("Host A") < scorecard.index("Pooled")


def test_report_marks_sessions_without_a_post_check_unavailable(batch, monkeypatch):
    add_host(batch, "M")
    monkeypatch.setattr(driver, "run_one", scripted([("counted", "")] * 3, []))
    driver.run(batch, "M")
    driver.report(batch)
    records = json.loads((batch / "records.json").read_text())
    assert {r["validity_reason"] for r in records} == {"post-check unavailable"}


def test_report_invalidates_a_rental_that_failed_its_post_check(batch, monkeypatch):
    add_host(batch, "M")
    monkeypatch.setattr(driver, "run_one", scripted([("counted", "")] * 3, []))
    driver.run(batch, "M")
    card_path = batch / "hosts/M/r1/host-card.json"
    card = json.loads(card_path.read_text()); card["post_check"] = "failed"; card_path.write_text(json.dumps(card))
    driver.report(batch)
    assert json.loads((batch / "records.json").read_text()) == []


def test_record_stop_writes_the_read_back_state(batch):
    add_host(batch, "A")
    driver.record_stop(batch, "A", "r1", state="EXITED", storage_billing=True)
    card = json.loads((batch / "hosts/A/r1/host-card.json").read_text())
    assert card["stopped"]["state"] == "EXITED" and card["stopped"]["storage_billing"] is True


# --- final-review fixes ---

def test_latest_rental_is_the_newest_check_not_the_newest_write(batch):
    add_host(batch, "A", rental="old")
    old = batch / "hosts/A/old/host-card.json"
    card = json.loads(old.read_text()); card["checked_at"] = "2026-11-05T01:00:00+00:00"; old.write_text(json.dumps(card))
    add_host(batch, "A", rental="new")
    new = batch / "hosts/A/new/host-card.json"
    card = json.loads(new.read_text()); card["checked_at"] = "2026-11-05T02:00:00+00:00"; new.write_text(json.dumps(card))
    driver.record_stop(batch, "A", "old", state="EXITED", storage_billing=False)   # rewrites the old card last
    assert driver.latest_rental(batch, "A")[0].name == "new"


def test_mac_preflight_failure_stops_before_any_session(batch, monkeypatch):
    add_host(batch, "M")
    monkeypatch.setattr(driver.isolation, "preflight_mac", lambda ports: {"ok": False, "listeners": [{"port": 8000}]})
    config = {"pod": False, "prefix": None, "rental_id": "r1"}
    with pytest.raises(SystemExit, match="preflight"):
        driver.run_one(batch, "M", config, {}, rig.load_pins(), 1)
    assert driver.events(batch) == []


def test_report_retains_invalid_sessions_and_budget_endings(batch, monkeypatch):
    add_host(batch, "M")
    calls = []
    run_one = scripted([("invalid", "sweep or preflight failed"), ("counted", ""), ("counted", ""), ("counted", "")], calls)
    def with_budget(*args):
        event = run_one(*args)
        if args[-1] == 2:
            event["record"] = {**event["record"], "completion": "budget"}
        return event
    monkeypatch.setattr(driver, "run_one", with_budget)
    driver.run(batch, "M")
    driver.report(batch)
    excluded = json.loads((batch / "excluded.json").read_text())
    assert [(e["host"], e["index"], e["reason"]) for e in excluded] == [("M", 1, "sweep or preflight failed")]
    scorecard = (batch / "scorecard.md").read_text()
    assert "Invalid sessions" in scorecard and "Budget endings" in scorecard and "run-2" in scorecard


def test_traversable(tmp_path):
    import tempfile
    root = Path(tempfile.mkdtemp(dir="/tmp", prefix="traverse-"))
    try:
        root.chmod(0o755); (root / "batch").mkdir(); (root / "batch").chmod(0o755)
        assert driver.traversable(root / "batch") is True
        root.chmod(0o700)
        assert driver.traversable(root / "batch") is False
    finally:
        root.chmod(0o755); (root / "batch").rmdir(); root.rmdir()


def test_grade_runs_acceptance_on_the_pristine_tree_before_hidden_grading(tmp_path, monkeypatch):
    order = []
    monkeypatch.setattr(driver, "_acceptance", lambda run, uncontained, **k: order.append(("acceptance", uncontained)))
    monkeypatch.setattr(driver.harness, "grade_and_record", lambda run, suite, **k: order.append(("hidden", None)))
    driver.grade(tmp_path, uncontained=False)
    assert order == [("acceptance", False), ("hidden", None)]


def test_collect_grades_refuses_symlinks_and_keeps_root_completion(tmp_path):
    run, copy = tmp_path / "run", tmp_path / "copy"
    run.mkdir(); copy.mkdir()
    (run / "execution.json").write_text(json.dumps({"termination_reason": "budget", "cleanup_ok": True,
                                                    "exit_code": None, "elapsed_seconds": 1.0}))
    (run / "trace.jsonl").write_text("")
    (copy / "run.json").write_text(json.dumps({"completion": "settled", "checks_ran": True}))
    (copy / "acceptance.json").write_text(json.dumps({"status": "control", "result": {"status": "pass"}}))
    (copy / "grade.json").symlink_to("/etc/hosts")
    problems = driver.collect_grades(copy, run)
    assert problems == ["grade.json is a symlink"]
    assert not (run / "grade.json").exists()
    assert json.loads((run / "run.json").read_text())["completion"] == "budget"   # root's execution, not the copy's
    assert json.loads((run / "acceptance.json").read_text())["result"]["status"] == "pass"


def test_freeze_names_only_files_that_exist():
    frozen = driver.freeze()
    assert frozen and all((ROOT / path).is_file() for path in frozen)
    assert str(driver.harness.RECORDER.relative_to(ROOT)) in frozen   # the recorder every session loads


def test_run_one_hands_pi_absolute_paths(batch, monkeypatch):
    """Pi runs with cwd = the workspace, so a relative run or profile path resolves under it and breaks."""
    seen = {}
    class Stop(Exception):
        pass
    def capture(suite, **options):
        seen.update(options)
        raise Stop()
    monkeypatch.chdir(batch.parent)
    monkeypatch.setattr(driver.isolation, "preflight_mac", lambda ports: {"ok": True, "listeners": []})
    monkeypatch.setattr(driver, "start_proxy", lambda config, pins, log: (type("P", (), {
        "terminate": lambda self: None, "wait": lambda self, timeout=None: 0, "kill": lambda self: None})(), 1))
    monkeypatch.setattr(driver.harness, "run_suite", capture)
    config = {"pod": False, "prefix": None, "rental_id": "r1", "endpoint": "http://127.0.0.1:1",
              "server_log": str(batch / "server.log")}
    with pytest.raises(Stop):
        driver.run_one(Path(batch.name), "M", config, {}, rig.load_pins(), 1)
    assert seen["runs_dir"].is_absolute() and seen["profile"].is_absolute() and seen["budget_log"].is_absolute()
