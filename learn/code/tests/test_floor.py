"""The floor's preregistered rules (LC.39): validity, replacement, usability, portability."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import floor
import rig

CHECKS = ["fastapi_app", "home_response", "title_override", "startup", "project_tests"]
SETTLED = {"termination_reason": "exited", "cleanup_ok": True}
RECONCILED = {"requests": 20, "output_tokens": 9000, "reconciled": True, "issues": []}
SWEPT = {"ok": True}


def card(**changes):
    return {"passed": True, "pins_digest": rig.pins_digest(rig.load_pins()), "rental_id": "pod-1", **changes}


def test_stale_card_refused():
    pins = rig.load_pins()
    assert floor.card_usable(card(), pins) == (True, "")
    usable, reason = floor.card_usable(card(pins_digest="0" * 64), pins)
    assert not usable and "pin card" in reason
    assert floor.card_usable(card(passed=False), pins)[0] is False


def test_proxy_bypass_is_invalid():
    bypassed = {**RECONCILED, "reconciled": False,
                "issues": ["server generations do not reconcile with relay-created inference requests"]}
    state, reason = floor.validity(SETTLED, bypassed, SWEPT, recovered=True, post_check="passed")
    assert state == "invalid" and "reconcile" in reason


def test_failed_sweep_is_invalid():
    assert floor.validity(SETTLED, RECONCILED, {"ok": False}, recovered=True, post_check="passed")[0] == "invalid"


def test_wall_safety_and_unrecovered_transport_are_invalid():
    assert floor.validity({**SETTLED, "termination_reason": "wall_safety"}, RECONCILED, SWEPT, True, "passed")[0] == "invalid"
    assert floor.validity(SETTLED, RECONCILED, SWEPT, recovered=False, post_check="passed")[0] == "invalid"


def test_model_outcomes_are_counted():
    for reason in ("exited", "stalled", "budget"):
        assert floor.validity({**SETTLED, "termination_reason": reason}, RECONCILED, SWEPT, True, "passed") == ("counted", "")


def test_lost_rental_sessions_count_flagged():
    assert floor.validity(SETTLED, RECONCILED, SWEPT, recovered=True, post_check="unavailable") == (
        "counted", "post-check unavailable")
    assert floor.validity(SETTLED, RECONCILED, SWEPT, recovered=True, post_check="failed")[0] == "invalid"


def test_transport_recovered():
    errors = [{"boundary": "stream_error"}]
    assert floor.transport_recovered([], "error") is True
    assert floor.transport_recovered(errors, "settled") is True
    assert floor.transport_recovered(errors, "error") is False


def test_replacement_cap():
    assert floor.may_replace({"replacements": 0}) and floor.may_replace({"replacements": 1})
    assert not floor.may_replace({"replacements": 2})


def write_run(root: Path, *, acceptance_failed=(), completion="settled", hidden=(4, 4), health="pass",
              out_of_layout=False, max_tokens=16384) -> Path:
    root.mkdir(parents=True)
    (root / "run.json").write_text(json.dumps({"completion": completion, "checks_ran": True,
        "checks_passed": hidden[0], "checks_total": hidden[1], "code_health": health,
        "missing_checks": [], "cleanup_ok": True}))
    checks = {name: {"passed": name not in acceptance_failed, "observation": ""} for name in CHECKS}
    status = "fail" if acceptance_failed else "pass"
    (root / "acceptance.json").write_text(json.dumps({"status": "control", "result": {"status": status, "checks": checks}}))
    (root / "layout.json").write_text(json.dumps({"out_of_layout": ["x.py"] if out_of_layout else []}))
    (root / "budget.json").write_text(json.dumps(RECONCILED))
    (root / "proxy.jsonl").write_text(json.dumps({"boundary": "rewritten", "max_tokens": max_tokens}) + "\n")
    return root


def test_usable_follows_lc34_rule(tmp_path):
    assert floor.session_record(write_run(tmp_path / "good"), card())["usable"] is True
    record = floor.session_record(write_run(tmp_path / "title", acceptance_failed=("title_override",)), card())
    assert record["usable"] is False and record["acceptance_checks"]["title_override"] is False
    assert floor.session_record(write_run(tmp_path / "budget", completion="budget"), card())["usable"] is False
    assert floor.session_record(write_run(tmp_path / "layout", out_of_layout=True), card())["usable"] is False
    assert floor.session_record(write_run(tmp_path / "hidden", hidden=(3, 4)), card())["usable"] is False


def test_session_record_reports_max_tokens_sent(tmp_path):
    record = floor.session_record(write_run(tmp_path / "clamped", max_tokens=8192), card())
    assert record["max_tokens_sent"] == [8192] and record["max_tokens_as_pinned"] is False


def rows(*, hidden=0, startup=0, settled=6, budget=0, n=6):
    return [{"hidden_all_pass": i < hidden, "acceptance_checks": {"startup": i < startup},
             "completion": "budget" if i < budget else ("settled" if i < settled else "stalled")}
            for i in range(n)]


def test_portability_rule():
    assert not floor.portability(rows(hidden=0), rows(hidden=4))["portable"]   # 0/6 vs 4/6
    assert floor.portability(rows(hidden=1), rows(hidden=4))["portable"]       # gap of 3
    assert not floor.portability(rows(startup=5), rows(startup=1))["portable"]
    assert not floor.portability(rows(budget=3), rows(budget=0))["portable"]
    assert floor.portability(rows(budget=3), rows(budget=1))["portable"]


def test_summarize_floor_reports_per_host_then_pooled():
    records = ([{"host": "A", "usable": False, "uncontained": False}] * 6
               + [{"host": "B", "usable": True, "uncontained": False}] + [{"host": "B", "usable": False, "uncontained": False}] * 5
               + [{"host": "M", "usable": False, "uncontained": True}] * 3)
    summary = floor.summarize_floor(records)
    assert list(summary) == ["per_host", "pooled_cuda", "pooled_all"]
    assert summary["per_host"]["B"]["usable"] == 1 and summary["per_host"]["B"]["n"] == 6
    assert summary["pooled_cuda"]["n"] == 12 and summary["pooled_all"]["n"] == 15
    assert summary["per_host"]["M"]["uncontained"] is True
