"""F.8: the boundary verdict of one phase run, on fake sessions and real grading."""
import json
import shutil
from pathlib import Path

import pytest

import harness
import phase_boundary
from test_harness import FIX, PROFILE, _Upstream

# Apart from the fixture suites, so `--suite all` over those is unchanged.
SUITES = FIX / "phase-suites"

SETTLE_UNIT = harness.REMEDIES / "check" / "mediated-test-settle.ts"
GOOD = "ONE = 1\nONE_LABEL = \"one\"\n"


def phased(phase=1):
    return phase_boundary.phase_scope(harness.load_suite(SUITES, "phased"), phase)


def phase_run(tmp_path, monkeypatch, app=GOOD, *, phase=1, gate=None, trace_line=None, budget=None,
              extras=(SETTLE_UNIT,)):
    source = tmp_path / "app-source.py"
    source.write_text(app)
    monkeypatch.setenv("FAKE_APP", str(source))
    for name, value in (("FAKE_GATE", gate), ("FAKE_TRACE_LINE", trace_line)):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    profile, upstream = PROFILE, None
    if budget is not None:
        monkeypatch.setenv("FAKE_SPEND", "1")
        upstream = _Upstream(10)
        profile = tmp_path / "profile"
        shutil.copytree(PROFILE, profile)
        models = json.loads((profile / "models.json").read_text())
        for provider in models["providers"].values():
            provider["baseUrl"] = f"http://127.0.0.1:{upstream.port}/v1"
        (profile / "models.json").write_text(json.dumps(models))
    else:
        monkeypatch.delenv("FAKE_SPEND", raising=False)
    try:
        [result] = harness._run_sessions(phased(phase), runs_dir=tmp_path / "runs", pi_binary=str(FIX / "fake-pi-phase.mjs"),
                                         repeat=1, grade_run=True, deadline=None, profile=profile, extras=list(extras),
                                         budget=budget, phase=phase)
    finally:
        if upstream is not None:
            upstream.close()
    return result[0], json.loads((result[0] / "run.json").read_text())


def test_a_budget_ending_is_graded_on_the_stopped_snapshot_and_can_be_accepted(tmp_path, monkeypatch):
    budget = {"max_requests": 3, "max_output_tokens": 100000, "unknown_usage_charge": 16384, "wall_safety_seconds": 60}
    _, record = phase_run(tmp_path, monkeypatch, budget=budget)
    assert record["completion"] == "budget"
    boundary = record["boundary"]
    assert boundary["ending"] == "budget" and boundary["gate"]["verified"] is False
    assert boundary["accepted"] is True, boundary["reasons"]


def test_green_in_session_with_a_failing_trusted_grade_is_rejected(tmp_path, monkeypatch):
    _, record = phase_run(tmp_path, monkeypatch, app="ONE = 2\nONE_LABEL = \"one\"\n", gate='{"status": "green"}\n')
    boundary = record["boundary"]
    assert boundary["gate"]["last"] == "green" and boundary["gate"]["verified"] is True
    assert boundary["accepted"] is False and boundary["hidden_passed"] is False
    assert any("hidden" in reason for reason in boundary["reasons"])


def test_a_passing_hidden_grade_with_a_failing_mediated_test_is_rejected_and_recorded_apart(tmp_path, monkeypatch):
    _, record = phase_run(tmp_path, monkeypatch, app="ONE = 1\n")
    boundary = record["boundary"]
    assert boundary["strict"] is True and boundary["hidden_passed"] is True
    assert boundary["mediated"]["passed"] is False
    assert boundary["mediated"]["missing"] == ["test_01_one.py::test_one_has_its_label"]
    assert boundary["accepted"] is False and any("mediated" in reason for reason in boundary["reasons"])


def test_a_lint_failure_rejects(tmp_path, monkeypatch):
    _, record = phase_run(tmp_path, monkeypatch, app="import os\n" + GOOD)
    assert record["boundary"]["quality_ok"] is False and record["boundary"]["accepted"] is False


def test_contamination_rejects(tmp_path, monkeypatch):
    _, record = phase_run(tmp_path, monkeypatch, trace_line='{"read": "suites/phased/grader/test_phase1_one.py"}')
    assert record["boundary"]["contaminated"] is True and record["boundary"]["accepted"] is False


def test_no_gate_log_reads_as_unverified_but_the_snapshot_is_still_graded(tmp_path, monkeypatch):
    _, record = phase_run(tmp_path, monkeypatch)
    gate = record["boundary"]["gate"]
    assert gate == {"armed": True, "last": None, "verdicts": 0, "verified": False}
    assert record["boundary"]["accepted"] is True


def test_a_truncated_gate_log_does_not_crash(tmp_path, monkeypatch):
    run_dir, record = phase_run(tmp_path, monkeypatch, gate='{"status": "red"}\n{"status": "green"}\n{"status": "ex')
    assert record["boundary"]["gate"]["last"] == "green" and record["boundary"]["gate"]["verdicts"] == 2
    assert [v["status"] for v in phase_boundary.gate_verdicts(run_dir)] == ["red", "green"]


def test_without_a_settle_unit_no_gate_log_is_exported(tmp_path, monkeypatch):
    run_dir, record = phase_run(tmp_path, monkeypatch, gate='{"status": "green"}\n', extras=())
    assert not (run_dir / "gate.jsonl").exists()
    assert record["boundary"]["gate"]["armed"] is False


def test_phase_two_sends_only_its_own_prompt_and_grades_phases_one_and_two(tmp_path, monkeypatch):
    run_dir, record = phase_run(tmp_path, monkeypatch, app=GOOD + "TWO = 2\n", phase=2)
    assert json.loads((run_dir / "workspace" / "prompts-seen.txt").read_text()) == "Phase 2: define TWO."
    assert record["grader"]["phase"] == 2 and record["boundary"]["phase"] == 2
    assert record["boundary"]["accepted"] is True, record["boundary"]["reasons"]
    assert sorted(record["boundary"]["mediated"]["expected"]) == [
        "test_01_one.py::test_one_has_its_label", "test_01_one.py::test_one_is_one", "test_02_two.py::test_two_is_two"]


def test_the_cli_refuses_a_phase_with_a_single_prompt(capsys):
    with pytest.raises(SystemExit):
        harness.main(["run", "--suite", "easy", "--phase", "2", "--single-prompt", "--dry-run"])
    err = capsys.readouterr().err
    assert "--phase" in err and "--single-prompt" in err and "unrecognized" not in err


# F.8: a multi-prompt run does not move to the next prompt on an unverified exit.

def multi_prompt_run(tmp_path, monkeypatch, gate, extras=(SETTLE_UNIT,)):
    from test_harness import _mediated_suite
    source = tmp_path / "app-source.py"
    source.write_text(GOOD)
    monkeypatch.setenv("FAKE_APP", str(source))
    monkeypatch.setenv("FAKE_GATE", gate)
    monkeypatch.delenv("FAKE_SPEND", raising=False)
    suite = _mediated_suite(tmp_path)
    run_dir = harness.run_suite(suite, runs_dir=tmp_path / "runs", profile=PROFILE,
                                pi_binary=str(FIX / "fake-pi-phase.mjs"), extras=list(extras))
    prompts = (run_dir / "workspace" / "prompts-seen.txt").read_text().splitlines()
    return run_dir, prompts


def test_an_unverified_exit_stops_the_run_before_the_next_prompt(tmp_path, monkeypatch):
    run_dir, prompts = multi_prompt_run(tmp_path, monkeypatch, '{"status": "exhausted"}\n')
    assert len(prompts) == 1
    assert json.loads((run_dir / "execution.json").read_text())["termination_reason"] == "unverified_exit"
    assert harness.execution_outcome(run_dir)["completion"] == "unverified_exit"


def test_a_green_exit_moves_to_the_next_prompt(tmp_path, monkeypatch):
    run_dir, prompts = multi_prompt_run(tmp_path, monkeypatch, '{"status": "green"}\n')
    assert len(prompts) == 2
    assert harness.execution_outcome(run_dir)["completion"] == "settled"


def test_a_run_with_no_settle_gate_is_unchanged(tmp_path, monkeypatch):
    run_dir, prompts = multi_prompt_run(tmp_path, monkeypatch, '{"status": "exhausted"}\n', extras=())
    assert len(prompts) == 2
