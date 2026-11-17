"""The plan arm: run_ladder drives the ``/mellum`` plan-delegation loop over the
whole spec from base, points the spawned architect/workers at the same backend
(they inherit ``PI_CODING_AGENT_DIR``), and records the delegate profiler's
request split as the cost axis — the parent trace cannot see the children.

Test-first: these pin the plan-mode arg builder, the whole-spec rung, and the
profiler summary before the wiring exists.
"""
from __future__ import annotations


def test_build_pi_plan_args_run_the_mellum_command_with_worker_and_recorder():
    from ladder.run_ladder import MODE_EXT, MODEL, RECORD_EXT, build_pi_plan_args

    args = build_pi_plan_args("Implement specs/")
    assert args[:2] == ["pi", "-p"]
    assert args[args.index("--mode") + 1] == "json"
    assert "--no-session" in args
    assert args[args.index("--model") + 1] == MODEL
    exts = [args[i + 1] for i, a in enumerate(args) if a == "-e"]
    assert exts.index(str(MODE_EXT)) < exts.index(str(RECORD_EXT))
    # the command invokes the /mellum plan loop over the whole-spec sentence
    assert args[-1] == "/mellum Implement specs/"


def test_rung_13_builds_the_whole_four_phase_spec_from_base():
    from ladder.rungs import FIXTURES, RUNGS

    rung = RUNGS[13]
    assert rung.fixture == "agentclinic-plan"
    specs = sorted((FIXTURES / "agentclinic-plan" / "specs").glob("phase-*.md"))
    assert [p.name for p in specs] == [
        "phase-1-home.md",
        "phase-2-board.md",
        "phase-3-add.md",
        "phase-4-resolve-reopen.md",
    ]
    # the base ships no implementation — the plan loop builds it all
    assert not (FIXTURES / "agentclinic-plan" / "app.py").exists()
    assert "four" in rung.sentence.lower() or "phase 4" in rung.sentence.lower()


def test_delegate_profile_summary_splits_requests_by_role(tmp_path):
    from ladder.run_ladder import delegate_profile_summary

    prof = tmp_path / "delegate-profile.jsonl"
    prof.write_text(
        '{"role":"architect: splitting","seq":0}\n'
        '{"role":"architect: splitting","seq":1}\n'
        '{"role":"worker: implementing","seq":0}\n'
        '{"role":"worker: implementing","seq":1}\n'
        '{"role":"worker: implementing","seq":2}\n'
    )
    s = delegate_profile_summary(prof)
    assert s["total"] == 5
    assert s["architect"] == 2
    assert s["worker"] == 3


def test_delegate_profile_summary_missing_file_is_zeroes(tmp_path):
    from ladder.run_ladder import delegate_profile_summary

    s = delegate_profile_summary(tmp_path / "nope.jsonl")
    assert s == {"total": 0, "architect": 0, "worker": 0}
