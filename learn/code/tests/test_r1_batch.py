"""R.1's batch runner: interleaved sessions through the real harness, resumable, and a report that
applies the preregistration's counting (docs/superpowers/research/2026-11-07-r1-preregistration.md)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import r1_batch  # noqa: E402

ARMS = {"vanilla": ["--arm", "vanilla"], "bounded": ["--arm", "worker", "--remedy", "tool/bounded-commands"]}


def test_sessions_are_interleaved_round_robin():
    assert r1_batch.plan_sessions(ARMS, 2) == [(1, "vanilla"), (1, "bounded"), (2, "vanilla"), (2, "bounded")]


def test_a_session_runs_the_real_harness_with_the_counted_flags(tmp_path):
    argv = r1_batch.harness_argv(ARMS["bounded"], tmp_path / "bounded-r01", host_card=Path("/c.json"),
                                 pi_binary="/pi")
    assert argv[:4] == ["uv", "run", "python", str(r1_batch.HARNESS)]
    for flag in (["--suite", "easy"], ["--grade"], ["--stall", "180"], ["--host-card", "/c.json"],
                 ["--pi-binary", "/pi"], ["--runs-dir", str(tmp_path / "bounded-r01")],
                 ["--arm", "worker"], ["--remedy", "tool/bounded-commands"]):
        assert any(argv[i:i + len(flag)] == flag for i in range(len(argv))), flag


def test_a_finished_session_is_not_run_again(tmp_path):
    done = tmp_path / "vanilla-r01" / "2026-x-easy-abc"
    done.mkdir(parents=True)
    (done / "run.json").write_text("{}")
    ran = []
    r1_batch.run_batch(r1_batch.plan_sessions(ARMS, 1), tmp_path,
                       argv_for=lambda arm, out: ["sh", "-c", f"echo {arm} >> {tmp_path / 'ran.txt'}"])
    ran = (tmp_path / "ran.txt").read_text().split()
    assert ran == ["bounded"]


def _record(root: Path, name: str, *, failed=0, ran=True, completion="settled", requests=10, output=1000, missing=()):
    run = root / name / "2026-x-easy-abc"
    run.mkdir(parents=True)
    (run / "run.json").write_text(json.dumps({
        "checks_ran": ran, "failed_checks": failed, "completion": completion,
        "censored": completion == "wall_safety", "missing_checks": list(missing),
        "budget": {"spent": {"requests": requests, "output_tokens": output}}}))


def test_the_report_leaves_stalled_and_censored_sessions_out_of_the_budget_medians(tmp_path):
    _record(tmp_path, "vanilla-r01", failed=0, requests=10, output=1000)
    _record(tmp_path, "vanilla-r02", failed=2, requests=20, output=3000)
    _record(tmp_path, "vanilla-r03", failed=5, completion="stalled", requests=2, output=100)
    _record(tmp_path, "vanilla-r04", ran=False, completion="wall_safety", requests=90, output=60000)
    _record(tmp_path, "vanilla-r05", failed=1, completion="budget", requests=64, output=5000)
    stats = r1_batch.summarize(tmp_path, checks=13)["vanilla"]
    assert stats["n"] == 5
    assert stats["full_passes"] == 1
    assert stats["mean_checks"] == (13 + 11 + 8 + 0 + 12) / 5     # every session, graded as it stands
    assert (stats["stalled"], stats["censored"], stats["budget_endings"]) == (1, 1, 1)
    assert stats["median_requests"] == 20      # of 10, 20, 64: stalled and censored left out
    assert stats["median_output_tokens"] == 3000


def test_the_report_writes_a_table_row_per_arm(tmp_path):
    _record(tmp_path, "vanilla-r01")
    _record(tmp_path, "bounded-r01", failed=1)
    table = r1_batch.table(r1_batch.summarize(tmp_path, checks=13))
    assert "| vanilla | 1 |" in table and "| bounded | 1 |" in table


TITLE = "grader_tests/test_phase1_acceptance.py::test_title"
LAUNCH = "grader_tests/test_phase1_acceptance.py::test_launch"


def test_the_report_counts_each_checks_misses_over_the_sessions_that_were_graded(tmp_path):
    _record(tmp_path, "vanilla-r01", failed=2, missing=[TITLE, LAUNCH])
    _record(tmp_path, "vanilla-r02", failed=1, missing=[TITLE])
    # A session whose checks never ran says nothing about any one check.
    _record(tmp_path, "vanilla-r03", ran=False, missing=[TITLE, LAUNCH])
    stats = r1_batch.summarize(tmp_path, checks=13)["vanilla"]
    assert stats["graded"] == 2
    assert stats["misses"] == {"test_title": 2, "test_launch": 1}


def test_the_per_check_table_has_a_row_per_missed_check_most_missed_first(tmp_path):
    _record(tmp_path, "vanilla-r01", failed=1, missing=[TITLE])
    _record(tmp_path, "vanilla-r02", failed=1, missing=[TITLE])
    _record(tmp_path, "unit-r01", failed=1, missing=[LAUNCH])
    table = r1_batch.check_table(r1_batch.summarize(tmp_path, checks=13))
    assert "| Check | unit (of 1) | vanilla (of 2) |" in table
    # "launch" sorts before "title" by name, so this order can only come from the miss counts.
    assert table.index("test_title") < table.index("test_launch")
    assert "| test_title | 0 | 2 |" in table
    assert "| test_launch | 1 | 0 |" in table


def test_report_writes_both_tables(tmp_path):
    _record(tmp_path, "vanilla-r01", failed=1, missing=[TITLE])
    assert r1_batch.main(["report", str(tmp_path)]) == 0
    written = (tmp_path / "table.md").read_text()
    assert "| vanilla | 1 |" in written and "| test_title | 1 |" in written
