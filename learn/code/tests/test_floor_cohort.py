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
