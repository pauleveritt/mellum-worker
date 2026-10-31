import json
import time
from datetime import datetime
import re
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
SUITES = FIX / "suites"
PROFILE = HERE.parent / "profile"


def run(tmp_path, binary="fake-pi.sh", task="add"):
    return harness.run_suite(
        harness.load_suite(SUITES, task),
        runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / binary),
    )


def test_load_task_reads_prompt_and_tests():
    task = harness.load_suite(SUITES, "add")
    assert "add(a, b)" in task.prompt
    assert (task.tests / "test_add.py").exists()


def test_a_task_can_hold_prompts_in_order():
    task = harness.load_suite(SUITES, "steps")
    assert task.prompts == [
        "First: write a file named one.txt.",
        "Second: write a file named two.txt.",
    ]
    assert task.prompt == task.prompts[0]


def test_an_empty_prompt_is_named(tmp_path):
    task_dir = tmp_path / "tasks" / "blank"
    task_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("   \n")
    with pytest.raises(SystemExit) as exc:
        harness.load_suite(tmp_path / "tasks", "blank")
    assert "blank" in str(exc.value)


def test_pi_argv_isolates_the_child():
    task = harness.load_suite(SUITES, "add")
    argv = harness.pi_argv("pi", PROFILE, Path("rec.mjs"), "llamacpp", "model-x",
                           task.prompt)
    for flag in ("-p", "--no-approve", "--no-context-files",
                 "--no-extensions", "--no-skills"):
        assert flag in argv
    assert "--no-session" not in argv
    assert str(Path("rec.mjs")) in argv
    assert argv[argv.index("--provider") + 1] == "llamacpp"
    assert argv[-1] == task.prompt


def test_arms_select_the_extension_and_guards():
    worker = harness.arm_settings("worker")
    assert worker["extension"].name == "mellum-worker.ts"
    no_prompt = harness.arm_settings("no-prompt")
    assert no_prompt["env"]["MELLUM_WORKER_PROMPT"] == "pi"
    no_nudge = harness.arm_settings("no-nudge")
    assert json.loads(no_nudge["env"]["MELLUM_GUARDS"]) == {"loopBreaker": True}
    no_loop = harness.arm_settings("no-loop")
    assert json.loads(no_loop["env"]["MELLUM_GUARDS"]) == {"emptyFinalNudge": 3}
    assert harness.arm_settings("bare")["extension"] is None


def test_the_strip_thinking_arm_opens_exactly_one_seam():
    env = harness.arm_settings("strip-thinking")["env"]
    assert env == {"MELLUM_MODE": "1", "MELLUM_STRIP_THINKING": "1"}, "one seam, not three"
    assert harness.arm_settings("worker")["env"].get("MELLUM_STRIP_THINKING") is None


def test_the_record_says_whether_reasoning_was_stripped(tmp_path):
    suite = harness.load_suite(SUITES, "add")
    for arm, expected in (("worker", False), ("strip-thinking", True)):
        results = harness._run_sessions(
            suite, runs_dir=tmp_path / arm, pi_binary=str(FIX / "fake-pi.sh"),
            repeat=1, grade_run=False, deadline=None, arm=arm,
        )
        record = json.loads((results[0][0] / "run.json").read_text())
        assert record["strip_thinking"] is expected, arm
        assert record["arm"] == arm


def test_the_server_guard_arm_keeps_the_other_guards_on():
    env = harness.arm_settings("server-guard")["env"]
    # MELLUM_GUARDS replaces ENABLED, so the arm must carry the whole set or it
    # would change three things and be no arm at all.
    assert json.loads(env["MELLUM_GUARDS"]) == harness.GUARDS_WITH_SERVER
    assert harness.GUARDS_WITH_SERVER == {"emptyFinalNudge": 3, "loopBreaker": True,
                                          "blockForegroundServer": True}
    assert "MELLUM_MODE_FACTS" not in env
    alone = harness.arm_settings("no-facts-guard")["env"]
    assert alone["MELLUM_MODE_FACTS"] == "0"
    assert json.loads(alone["MELLUM_GUARDS"]) == harness.GUARDS_WITH_SERVER


def test_two_prompts_share_one_session(tmp_path):
    task = harness.load_suite(SUITES, "steps")
    run_dir = harness.run_suite(
        task, runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi-session.sh"),
    )
    lines = [line.split("|") for line in
             (run_dir / "workspace" / "session-log.txt").read_text().splitlines()]
    assert [line[2] for line in lines] == task.prompts
    assert lines[0][0] == lines[1][0] and lines[0][0]
    assert lines[0][1] == lines[1][1]
    assert str(run_dir) in lines[0][1]
    assert (run_dir / "workspace" / "one.txt").exists()
    assert (run_dir / "workspace" / "two.txt").exists()
    assert not (run_dir / "workspace" / "tests").exists()
    rows = [json.loads(row) for row in
            (run_dir / "trace.jsonl").read_text().splitlines()]
    assert sum(row["type"] == "instance_start" for row in rows) == 2


def test_runs_are_fresh_and_tests_are_hidden(tmp_path):
    first = run(tmp_path)
    assert (first / "workspace" / "add.py").exists()
    assert not (first / "workspace" / "tests").exists()
    assert (first / "profile" / "models.json").exists()
    assert (first / "trace.jsonl").exists()
    assert (first / "workspace" / "profile-path.txt").read_text().strip() \
        == str(first / "profile")
    (first / "workspace" / "stray.txt").write_text("x")
    second = run(tmp_path)
    assert second != first
    assert not (second / "workspace" / "stray.txt").exists()


def test_run_suite_copies_the_base_project(tmp_path):
    suite_dir = tmp_path / "suites" / "seeded"
    (suite_dir / "base").mkdir(parents=True)
    (suite_dir / "base" / "seed.txt").write_text("from the base\n")
    (suite_dir / "prompts").mkdir()
    (suite_dir / "prompts" / "01.md").write_text("Write add.py.\n")
    (suite_dir / "tests").mkdir()
    (suite_dir / "tests" / "test_add.py").write_text(
        "from add import add\n\ndef test_add():\n    assert add(2, 3) == 5\n")
    suite = harness.load_suite(tmp_path / "suites", "seeded")
    run_dir = harness.run_suite(
        suite, runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi.sh"),
    )
    assert (run_dir / "workspace" / "seed.txt").read_text() == "from the base\n"


def test_missing_pi_is_a_message(tmp_path):
    task = harness.load_suite(SUITES, "add")
    with pytest.raises(SystemExit) as exc:
        harness.run_suite(task, runs_dir=tmp_path / "runs", profile=PROFILE,
                         pi_binary="/nonexistent/pi")
    assert "pi" in str(exc.value)


def _scored(tmp_path, binary):
    run_dir = run(tmp_path, binary)
    return harness.score(run_dir, harness.load_suite(SUITES, "add"))


def test_score_passes_a_working_workspace(tmp_path):
    passed, tail = _scored(tmp_path, "fake-pi.sh")
    assert passed, tail


def test_score_keeps_the_run_and_copies_the_tests(tmp_path):
    run_dir = run(tmp_path, "fake-pi-empty.sh")
    passed, tail = harness.score(run_dir, harness.load_suite(SUITES, "add"))
    assert not passed
    assert (run_dir / "workspace" / "grader_tests" / "test_add.py").exists()
    assert tail


def test_score_fails_a_wrong_solution(tmp_path):
    passed, _ = _scored(tmp_path, "fake-pi-wrong.sh")
    assert not passed


EASY = HERE.parent / "suites" / "easy"


def _task_tests_pass(cwd, tests):
    result = subprocess.run(
        ["uvx", "pytest", "-q", str(tests)], cwd=cwd, capture_output=True,
        text=True, env={**os.environ, "PYTHONPATH": str(cwd)},
        check=False,
    )
    return result.returncode == 0


def _write_trace(run, rows):
    (run / "trace.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_report_counts_the_trace(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [
        {"type": "instance_start", "timestamp": "2026-10-21T00:00:00+00:00"},
        {"type": "provider_request", "request": 1},
        {"type": "tool_call", "toolName": "bash"},
        {"type": "tool_result", "isError": True},
        {"type": "message_end", "timestamp": "2026-10-21T00:00:01+00:00",
         "message": {"role": "assistant",
                     "usage": {"input": 1000, "output": 10},
                     "content": [{"type": "text", "text": "ok"}]}},
        {"type": "provider_request", "request": 2},
        {"type": "message_end", "timestamp": "2026-10-21T00:00:02+00:00",
         "message": {"role": "assistant",
                     "usage": {"input": 1500, "output": 20},
                     "content": [{"type": "text", "text": "done"}]}},
        {"type": "agent_settled", "timestamp": "2026-10-21T00:00:02+00:00"},
    ])
    assert harness.report(run_dir) == {
        "requests": 2, "turns": 2, "tool_calls": 1, "tool_errors": 1,
        "final_reply": "done", "context": 1500, "output_tokens": 30,
        "wall": 2.0, "nudges": 0, "empty_finals": 0, "guard_blocks": 0,
        "reasoning_as_text": 0, "compactions": 0,
    }


def test_report_counts_turns_whose_reasoning_reached_the_model_as_text(tmp_path):
    # A serving stack that misparses reasoning returns it as <think> text, and
    # Pi feeds it back as things the model said (research note
    # 2026-10-29-lan-reasoning-leak). The record counts it from the history the
    # model was sent, so a repaired turn counts 0.
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    history = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": None, "reasoning": "fine"},
        {"role": "tool", "content": "ok"},
        {"role": "assistant", "content": "<think>\nleaked\n</think>\n\nnext"},
        {"role": "tool", "content": "ok"},
        {"role": "assistant", "content": "<think>\nagain</think>"},
    ]
    _write_trace(run_dir, [
        {"type": "provider_request", "payload": {"messages": history[:4]}},
        {"type": "provider_request", "payload": {"messages": history}},
    ])
    assert harness.report(run_dir)["reasoning_as_text"] == 2


def test_a_challenge_can_require_the_record_to_be_clean(tmp_path):
    # Some failures live in the record, not the workspace: a challenge's
    # record.json caps run.json fields, and a run over a cap fails.
    suite_dir = tmp_path / "suites" / "plumbing"
    (suite_dir / "grader").mkdir(parents=True)
    (suite_dir / "task.md").write_text("Do it.")
    (suite_dir / "record.json").write_text('{"reasoning_as_text": 0}')
    suite = harness.load_suite(tmp_path / "suites", "plumbing")
    assert suite.record == {"reasoning_as_text": 0}
    assert harness.record_failures({"reasoning_as_text": 10}, suite.record) == [
        "reasoning_as_text is 10 (at most 0)"]
    assert harness.record_failures({"reasoning_as_text": 0}, suite.record) == []
    assert harness.record_failures({}, None) == []


def test_report_counts_the_compactions_a_full_context_forced(tmp_path):
    # Pi compacts when the context nears its window: the model summarises its
    # own history and loses detail. The record counts each one.
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [
        {"type": "provider_request"},
        {"type": "before_compact", "reason": "threshold"},
        {"type": "provider_request"},
        {"type": "before_compact", "reason": "overflow"},
    ])
    assert harness.report(run_dir)["compactions"] == 2


def test_report_without_text(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [{"type": "instance_start"}])
    assert harness.report(run_dir) == {
        "requests": 0, "turns": 0, "tool_calls": 0, "tool_errors": 0,
        "final_reply": "", "context": None, "output_tokens": None, "wall": None,
        "nudges": 0, "empty_finals": 0, "guard_blocks": 0, "reasoning_as_text": 0,
        "compactions": 0,
    }


def test_report_separates_a_nudge_from_an_empty_final(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    empty = {"role": "assistant", "stopReason": "stop", "content": []}
    _write_trace(run_dir, [
        {"type": "instance_start"},
        {"type": "provider_request", "request": 1},
        {"type": "message_end", "message": empty},
        {"type": "provider_request", "request": 2},
        {"type": "message_end", "message": {"role": "assistant",
                                            "content": [{"type": "text", "text": "ok"}]}},
        {"type": "provider_request", "request": 3},
        {"type": "message_end", "message": dict(empty, stopReason="length")},
    ])
    report = harness.report(run_dir)
    assert report["nudges"] == 1
    assert report["empty_finals"] == 1


def test_report_counts_a_guard_refusal_the_model_was_told_about(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    rows = [
        {"type": "instance_start", "timestamp": "2026-10-27T01:00:00Z"},
        {"type": "provider_request", "timestamp": "2026-10-27T01:00:01Z"},
        {"type": "tool_call", "toolName": "bash", "input": {"command": "uvicorn app:app"},
         "timestamp": "2026-10-27T01:00:02Z"},
        {"type": "message_end", "timestamp": "2026-10-27T01:00:03Z",
         "message": {"role": "toolResult", "content": [
             {"type": "text", "text": "That starts a server in the foreground; it blocks forever."}]}},
        {"type": "message_end", "timestamp": "2026-10-27T01:00:05Z",
         "message": {"role": "assistant", "content": [
             {"type": "text", "text": "Using TestClient instead."}]}},
    ]
    (run_dir / "trace.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    counts = harness.report(run_dir)
    assert counts["guard_blocks"] == 1
    assert counts["nudges"] == 0


def test_score_details_counts_expected_failures(tmp_path):
    suite_dir = tmp_path / "suites" / "failcheck"
    (suite_dir / "tests").mkdir(parents=True)
    (suite_dir / "tests" / "test_add.py").write_text(
        "from add import add\n\ndef test_add():\n    assert add(2, 3) == 5\n")
    (suite_dir / "expected.json").write_text(
        json.dumps(["grader_tests/test_add.py::test_add"]))
    (suite_dir / "task.md").write_text("Write add.py.\n")
    suite = harness.load_suite(tmp_path / "suites", "failcheck")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "add.py").write_text("def add(a, b):\n    return 0\n")
    passed, tail, missing, checks_ran = harness.score_workspace_details(workspace, suite)
    assert not passed
    assert checks_ran
    assert missing == ["grader_tests/test_add.py::test_add"]
    assert "test_add" in tail


def test_check_groups_counts_each_module_both_ways(tmp_path):
    suite_dir = tmp_path / "suites" / "twophase"
    (suite_dir / "tests").mkdir(parents=True)
    (suite_dir / "tests" / "test_phase1_home.py").write_text(
        "def test_home():\n    assert True\n")
    (suite_dir / "tests" / "test_phase2_board.py").write_text(
        "def test_board():\n    assert False\n")
    (suite_dir / "expected.json").write_text(json.dumps([
        "grader_tests/test_phase1_home.py::test_home",
        "grader_tests/test_phase2_board.py::test_board",
    ]))
    (suite_dir / "task.md").write_text("Build it.\n")
    suite = harness.load_suite(tmp_path / "suites", "twophase")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _passed, _tail, missing, _ran = harness.score_workspace_details(workspace, suite)
    assert missing == ["grader_tests/test_phase2_board.py::test_board"]
    assert harness.check_groups(suite.expected, missing) == {
        "test_phase1_home.py": {"missing": 0, "total": 1},
        "test_phase2_board.py": {"missing": 1, "total": 1},
    }


def _phased_suite(tmp_path):
    suite_dir = tmp_path / "suites" / "phased"
    (suite_dir / "base" / "specs").mkdir(parents=True)
    (suite_dir / "base" / "specs" / "roadmap.md").write_text("all phases, one file\n")
    (suite_dir / "base" / "AGENTS.md").write_text("the phases are in specs/roadmap.md\n")
    (suite_dir / "prompts").mkdir()
    (suite_dir / "prompts" / "01.md").write_text("default prompt\n")
    (suite_dir / "tests").mkdir()
    (suite_dir / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    joined = suite_dir / "spec-variants" / "joined" / "prompts"
    joined.mkdir(parents=True)
    (joined / "01.md").write_text("joined prompt\n")
    split = suite_dir / "spec-variants" / "split"
    (split / "prompts").mkdir(parents=True)
    (split / "specs").mkdir()
    (split / "prompts" / "01.md").write_text("split prompt\n")
    (split / "AGENTS.md").write_text("one file per phase in specs/\n")
    (split / "specs" / "phase-1.md").write_text("phase one\n")
    (split / "delete.json").write_text(json.dumps(["specs/roadmap.md"]))
    return harness.load_suite(tmp_path / "suites", "phased")


def _variant_run(tmp_path, suite, specs):
    return harness.run_suite(
        suite, runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi.sh"), specs=specs,
    )


def test_checks_that_never_ran_are_recorded_as_such(tmp_path):
    suite_dir = tmp_path / "suites" / "broken"
    (suite_dir / "tests").mkdir(parents=True)
    (suite_dir / "tests" / "test_board.py").write_text(
        "import models\n\ndef test_board():\n    assert models.complaints\n")
    (suite_dir / "expected.json").write_text(json.dumps([
        "grader_tests/test_board.py::test_board"]))
    (suite_dir / "task.md").write_text("Build it.\n")
    suite = harness.load_suite(tmp_path / "suites", "broken")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    passed, tail, missing, checks_ran = harness.score_workspace_details(workspace, suite)
    assert not passed
    assert not checks_ran, "a collection error is not the same finding as a failing check"
    assert missing == ["grader_tests/test_board.py::test_board"]
    assert "ModuleNotFoundError" in tail


def test_the_record_says_when_the_checks_never_ran(tmp_path):
    suite_dir = tmp_path / "suites" / "broken"
    (suite_dir / "tests").mkdir(parents=True)
    (suite_dir / "tests" / "test_board.py").write_text(
        "import models\n\ndef test_board():\n    assert models.complaints\n")
    (suite_dir / "expected.json").write_text(json.dumps([
        "grader_tests/test_board.py::test_board"]))
    (suite_dir / "task.md").write_text("Build add.py with add(a, b).\n")
    suite = harness.load_suite(tmp_path / "suites", "broken")
    results = harness._run_sessions(
        suite, runs_dir=tmp_path / "runs", pi_binary=str(FIX / "fake-pi.sh"),
        repeat=1, grade_run=False, deadline=None,
    )
    record = json.loads((results[0][0] / "run.json").read_text())
    assert record["checks_ran"] is False


def test_a_suite_without_a_variant_is_unchanged(tmp_path):
    suite = _phased_suite(tmp_path)
    run_dir = _variant_run(tmp_path, suite, None)
    assert (Path(run_dir) / "prompt.txt").read_text().strip() == "default prompt"
    workspace = Path(run_dir) / "workspace"
    assert (workspace / "specs" / "roadmap.md").is_file()
    assert (workspace / "AGENTS.md").read_text().strip() == (
        "the phases are in specs/roadmap.md")


def test_specs_joined_takes_the_variants_prompts(tmp_path):
    suite = _phased_suite(tmp_path)
    run_dir = _variant_run(tmp_path, suite, "joined")
    assert (Path(run_dir) / "prompt.txt").read_text().strip() == "joined prompt"
    assert (Path(run_dir) / "workspace" / "specs" / "roadmap.md").is_file()


def test_specs_split_overlays_the_project_and_deletes_the_roadmap(tmp_path):
    suite = _phased_suite(tmp_path)
    run_dir = _variant_run(tmp_path, suite, "split")
    workspace = Path(run_dir) / "workspace"
    assert (Path(run_dir) / "prompt.txt").read_text().strip() == "split prompt"
    assert (workspace / "specs" / "phase-1.md").is_file()
    assert not (workspace / "specs" / "roadmap.md").exists()
    assert (workspace / "AGENTS.md").read_text().strip() == (
        "one file per phase in specs/")


def test_unknown_specs_variant_names_the_ones_available(tmp_path):
    suite = _phased_suite(tmp_path)
    with pytest.raises(SystemExit) as error:
        _variant_run(tmp_path, suite, "stepwise")
    assert "joined" in str(error.value) and "split" in str(error.value)


def test_medium_ships_both_spec_variants():
    suite = harness.load_suite(harness.SUITES, "medium")
    joined = harness.load_variant(suite, "joined")
    split = harness.load_variant(suite, "split")
    assert (split / "specs" / "phase-4.md").is_file()
    assert json.loads((split / "delete.json").read_text()) == ["specs/roadmap.md"]
    joined_prompts = sorted((joined / "prompts").glob("*.md"))
    split_prompts = sorted((split / "prompts").glob("*.md"))
    assert len(joined_prompts) == len(split_prompts) == 4
    for index, (left, right) in enumerate(zip(joined_prompts, split_prompts), 1):
        # the arms differ in one thing only: the file the pointer names
        assert left.read_text().replace("specs/roadmap.md", "SPEC") == \
            right.read_text().replace(f"specs/phase-{index}.md", "SPEC")


def test_the_split_keeps_the_roadmaps_phases():
    suite = harness.load_suite(harness.SUITES, "medium")
    roadmap = (suite.root / "base" / "specs" / "roadmap.md").read_text()
    blocks, current = {}, None
    for line in roadmap.splitlines():
        if line.startswith("## Phase"):
            current = line.removeprefix("## ").split(" \u2014 ")[0].lower().replace(" ", "-")
            blocks[current] = [line.removeprefix("## ")]
        elif line.startswith("## "):
            current = None
        elif current is not None and line.strip():
            blocks[current].append(line.strip())
    assert sorted(blocks) == ["phase-1", "phase-2", "phase-3", "phase-4"]
    split = harness.load_variant(suite, "split")
    for name, lines in blocks.items():
        text = (split / "specs" / f"{name}.md").read_text()
        for line in lines:
            assert line in text, f"{name} lost: {line}"


def test_the_thin_briefs_name_the_verification_loop():
    suite = harness.load_suite(harness.SUITES, "medium")
    for arm in ("joined", "split"):
        prompts = sorted((harness.load_variant(suite, arm) / "prompts").glob("*.md"))
        assert len(prompts) == 4
        for prompt in prompts:
            text = " ".join(prompt.read_text().split())
            assert "python -m pytest tests" in text, f"{arm}/{prompt.name} names no test command"
            assert "do not check it by starting a server" in text, (
                f"{arm}/{prompt.name} does not rule out a server as the check")


def test_medium_base_ships_a_phase1_smoke_test():
    suite = harness.load_suite(harness.SUITES, "medium")
    test = suite.root / "base" / "tests" / "test_home.py"
    assert test.is_file(), "the base project ships no test, so its test command has nothing to run"
    text = test.read_text()
    assert "TestClient" in text
    assert "Come in. Sit down." in text


def test_medium_asks_for_the_home_page_in_process():
    suite = harness.load_suite(harness.SUITES, "medium")
    roadmap = (suite.root / "base" / "specs" / "roadmap.md").read_text()
    assert "TestClient" in roadmap, "the roadmap never asks for an in-process check"
    split = (harness.load_variant(suite, "split") / "specs" / "phase-1.md").read_text()
    assert "TestClient" in split


def test_run_sessions_records_the_variant(tmp_path):
    suite = _phased_suite(tmp_path)
    results = harness._run_sessions(
        suite, runs_dir=tmp_path / "runs", pi_binary=str(FIX / "fake-pi.sh"),
        repeat=1, grade_run=False, deadline=None, specs="split",
    )
    record = json.loads((results[0][0] / "run.json").read_text())
    assert record["specs"] == "split"


def test_run_sessions_writes_metrics(tmp_path):
    suite = harness.load_suite(SUITES, "add")
    results = harness._run_sessions(
        suite, runs_dir=tmp_path / "runs", pi_binary=str(FIX / "fake-pi.sh"),
        repeat=1, grade_run=False, deadline=None,
    )
    run_dir = results[0][0]
    record = json.loads((run_dir / "run.json").read_text())
    assert record["suite"] == "add"
    assert record["passed"] is True
    assert record["failed_checks"] == 0
    assert record["missing_checks"] == []
    # the fixture suite declares no expected.json, so there are no groups to report
    assert record["checks_ran"] is True
    assert record["check_groups"] == {}
    assert record["turns"] == 0
    assert record["context"] is None
    assert record["wall"] is None


def test_grade_ignores_the_workspace_venv(tmp_path):
    workspace = _workspace(
        tmp_path, "def fizz(n: int) -> str:\n    return str(n)\n")
    venv = workspace / ".venv"
    venv.mkdir()
    (venv / "bad.py").write_text("def broken():\n    return missing\n")
    grades = {name: ok for name, ok, _ in harness.grade(workspace)}
    assert grades["ruff"] is True


def test_run_suites_orders_easy_medium_hard(tmp_path, capsys):
    for name in ("hard", "easy", "medium"):
        suite = tmp_path / "suites" / name
        (suite / "tests").mkdir(parents=True)
        (suite / "task.md").write_text("Write add.py with add(a, b).\n")
        (suite / "tests" / "test_add.py").write_text(
            "from add import add\n\ndef test_add():\n    assert add(2, 3) == 5\n")
    harness.run_suites(
        ["all"], suites_dir=tmp_path / "suites", runs_dir=tmp_path / "runs",
        pi_binary=str(FIX / "fake-pi.sh"),
    )
    out = capsys.readouterr().out
    assert out.index("easy") < out.index("medium") < out.index("hard")


def test_suite_runs_every_named_task(tmp_path):
    passed, total = harness.run_suites(
        ["all"], suites_dir=SUITES, runs_dir=tmp_path / "runs",
        pi_binary=str(FIX / "fake-pi.sh"),
    )
    assert (passed, total) == (2, 2)


def test_suite_counts_a_failure(tmp_path):
    passed, total = harness.run_suites(
        ["add"], suites_dir=SUITES, runs_dir=tmp_path / "runs",
        pi_binary=str(FIX / "fake-pi-empty.sh"),
    )
    assert (passed, total) == (0, 1)


def test_suite_rejects_an_unknown_name(tmp_path):
    with pytest.raises(SystemExit) as exc:
        harness.run_suites(["nope"], suites_dir=SUITES, runs_dir=tmp_path / "runs")
    assert "nope" in str(exc.value)


def _workspace(tmp_path, source):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "solution.py").write_text(textwrap.dedent(source))
    return workspace


def _grades(tmp_path, source):
    return {name: ok for name, ok, _ in harness.grade(_workspace(tmp_path, source))}


def test_grade_passes_a_clean_solution(tmp_path):
    assert _grades(tmp_path, "def fizz(n: int) -> str:\n    return str(n)\n") == {
        "ruff": True, "pyrefly": True, "complexipy": True,
    }


def test_grade_fails_ruff_on_an_unused_import(tmp_path):
    workspace = _workspace(
        tmp_path, "import os\n\n\ndef fizz(n: int) -> str:\n    return str(n)\n")
    results = {name: (ok, detail) for name, ok, detail in harness.grade(workspace)}
    assert results["ruff"][0] is False
    assert "F401" in results["ruff"][1], results["ruff"][1]
    assert results["pyrefly"][0] is True
    assert results["complexipy"][0] is True


def test_grade_fails_pyrefly_on_a_type_error(tmp_path):
    grades = _grades(tmp_path, "def f(x: int) -> str:\n    return x\n")
    assert grades["pyrefly"] is False
    assert grades["ruff"] is True


def test_grade_fails_complexipy_above_ten(tmp_path):
    branches = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(12))
    grades = _grades(tmp_path, "def f(x: int) -> int:\n" + branches + "    return -1\n")
    assert grades["complexipy"] is False
    assert grades["ruff"] is True


def test_grade_ignores_a_copied_tests_dir(tmp_path):
    workspace = _workspace(tmp_path, "def fizz(n: int) -> str:\n    return str(n)\n")
    (workspace / "tests").mkdir()
    (workspace / "tests" / "test_x.py").write_text("import pytest\n")
    results = {name: ok for name, ok, _ in harness.grade(workspace)}
    assert results["ruff"] is True


def test_grade_ignores_a_dot_venv(tmp_path):
    # The worker runs `uv` during its task, so a .venv exists at grade time.
    # ruff's --exclude REPLACES its built-in excludes (which include .venv), so
    # grade() was linting installed packages (F403 in PyYAML) and failing every
    # working solution. It must lint the worker's code, not site-packages.
    workspace = _workspace(tmp_path, "def fizz(n: int) -> str:\n    return str(n)\n")
    pkg = workspace / ".venv" / "lib" / "site-packages" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("from os import *\n")  # F403, must not fail the worker
    results = {name: ok for name, ok, _ in harness.grade(workspace)}
    assert results["ruff"] is True


def test_grade_tolerates_style_not_real_errors(tmp_path):
    # An unused `# noqa` is RUF100 — a style nit, not a real error. The grader
    # is meant to gate on real errors only (ruff --select F,E9), so it must
    # tolerate this. The shadowed, stricter grade() (default ruff) reports
    # RUF100 and wrongly fails a working solution — the exact trap that failed
    # working lesson solutions (easy was 4/4 on the hidden grader yet FAILED).
    grades = _grades(
        tmp_path,
        "def fizz(x: int) -> str:\n"
        "    return str(x)  # noqa: D415\n",
    )
    assert grades["ruff"] is True


def test_harness_has_no_shadowed_top_level_definitions():
    # A second `def`/`class` of the same name at module scope silently replaces
    # the first (pyflakes F811) — how the lenient grade() got shadowed by an
    # older strict copy. Pin the grading harness itself against that bug class.
    import ast
    from collections import Counter

    tree = ast.parse(Path(harness.__file__).read_text())
    defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    names = [node.name for node in tree.body if isinstance(node, defs)]
    shadowed = sorted(name for name, count in Counter(names).items() if count > 1)
    assert not shadowed, f"redefined at module scope (later shadows earlier): {shadowed}"


@pytest.mark.parametrize("name", ["easy"])
def test_each_solution_passes_the_graders(tmp_path, name):
    solved = tmp_path / name
    solved.mkdir()
    source = (HERE.parent / "suites" / name / "fixtures" / "known-good"
              if name == "easy"
              else HERE.parent / "suites" / name / "solution")
    shutil.copytree(source, solved, dirs_exist_ok=True)
    results = harness.grade(solved)
    assert all(ok for name, ok, _ in results if name in {"ruff", "complexipy"}), results


def test_a_session_can_be_bounded(tmp_path):
    import time as clock

    task = harness.load_suite(SUITES, "add")
    started = clock.monotonic()
    run_dir = harness.run_suite(
        task, runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi-slow.sh"), deadline=1,
    )
    assert clock.monotonic() - started < 5
    assert (run_dir / "deadline").exists()


def test_runs_default_outside_the_repo():
    import tempfile

    assert str(harness.RUNS).startswith(tempfile.gettempdir())
    assert not str(harness.RUNS).startswith(str(harness.CODE))


def test_a_canary_in_the_trace_marks_the_run(tmp_path):
    suite = harness.Suite(
        name="x", prompts=["p"], tests=tmp_path / "g", start=None,
        canary="CANARY-TOKEN")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "trace.jsonl").write_text('{"type":"tool_call","input":"CANARY-TOKEN"}')
    assert harness.grader_touched(run_dir, suite) is True
    (run_dir / "trace.jsonl").write_text('{"type":"tool_call","input":"ls"}')
    assert harness.grader_touched(run_dir, suite) is False


def test_a_missing_expected_test_fails(tmp_path):
    base = harness.load_suite(SUITES, "add")
    suite = harness.Suite(
        name=base.name, prompts=base.prompts, tests=base.tests,
        start=base.start, expected=("tests/test_add.py::test_nope",))
    run_dir = harness.run_suite(
        suite, runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi.sh"))
    passed, tail = harness.score(run_dir, suite)
    assert not passed
    assert "missing expected tests" in tail


def test_qualify_proves_both_directions():
    suite = harness.load_suite(FIX, "qualify")
    ok, results = harness.qualify(suite)
    assert ok
    assert results == {"known-good": True, "known-broken": False}


def test_the_arm_owns_the_facts_knob(tmp_path, monkeypatch):
    task = harness.load_suite(SUITES, "add")
    monkeypatch.setenv("MELLUM_MODE_FACTS", "1")

    def seen(arm):
        run_dir = harness.run_suite(
            task, runs_dir=tmp_path / arm, profile=PROFILE,
            pi_binary=str(FIX / "fake-pi-env.sh"), arm=arm,
        )
        return (run_dir / "workspace" / "env.txt").read_text().strip()

    assert seen("no-facts") == "MELLUM_MODE_FACTS=0"
    assert seen("worker") == "MELLUM_MODE_FACTS="


def test_the_recorder_loads_after_the_worker_extension():
    # Pi runs before_provider_request handlers in extension load order and each
    # may replace the payload, so a recorder placed first sees the messages
    # before the worker appends its facts block.
    argv = harness.pi_argv(
        "pi", PROFILE, Path("rec.mjs"), "llamacpp", "model", "task",
        extension=harness.arm_settings("worker")["extension"],
    )
    assert argv.index(str(harness.arm_settings("worker")["extension"])) < argv.index("rec.mjs")


def _trace(*rows):
    return "".join(json.dumps(dict(traceSchema=1, timestamp="2026-10-24T00:00:0%dZ" % i, **r)) + "\n"
                   for i, r in enumerate(rows))


def test_an_empty_final_at_a_prompt_boundary_is_not_a_nudge(tmp_path):
    # Medium and hard run one Pi process per prompt. An empty turn that ends one
    # prompt is followed by the next prompt's request, which is not a nudge.
    run = tmp_path / "run"
    run.mkdir()
    (run / "trace.jsonl").write_text(_trace(
        {"type": "instance_start"},
        {"type": "provider_request", "request": 1},
        {"type": "message_end", "message": {"role": "assistant", "content": []}},
        {"type": "agent_settled", "aborted": False},
        {"type": "instance_start"},
        {"type": "provider_request", "request": 1},
        {"type": "message_end", "message": {"role": "assistant",
         "content": [{"type": "text", "text": "done"}]}},
        {"type": "agent_settled", "aborted": False},
    ))
    counts = harness.report(run)
    assert counts["nudges"] == 0
    assert counts["empty_finals"] == 1


def test_an_empty_turn_inside_one_prompt_is_a_nudge(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "trace.jsonl").write_text(_trace(
        {"type": "instance_start"},
        {"type": "provider_request", "request": 1},
        {"type": "message_end", "message": {"role": "assistant", "content": []}},
        {"type": "provider_request", "request": 2},
        {"type": "message_end", "message": {"role": "assistant",
         "content": [{"type": "text", "text": "done"}]}},
        {"type": "agent_settled", "aborted": False},
    ))
    counts = harness.report(run)
    assert counts["nudges"] == 1
    assert counts["empty_finals"] == 0


def _write(root, rel, text="x\n"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_layout_report_names_created_and_modified_files_outside_it(tmp_path):
    root = tmp_path / "workspace"
    _write(root, "app.py", "one\n")
    _write(root, "tests/test_home.py", "pass\n")
    pristine = harness.file_hashes(root)
    _write(root, "app.py", "two\n")            # modified, allowed
    _write(root, "templates/home.html")        # created, allowed
    _write(root, "notes.txt")                  # created, outside the layout
    _write(root, "tests/test_extra.py")        # created, allowed by tests/**
    _write(root, ".venv/lib/python3.14/x.py")  # ignored
    _write(root, "app.log")                    # ignored
    layout = {"allow": ["app.py", "templates/**", "tests/**"],
              "ignore": [".venv/**", "*.log"]}
    report = harness.layout_report(root, pristine, layout)
    assert report["modified"] == ["app.py"]
    assert "templates/home.html" in report["created"]
    assert "tests/test_extra.py" in report["created"]
    assert report["out_of_layout"] == ["notes.txt"]


def test_a_clean_workspace_has_nothing_outside_its_layout(tmp_path):
    root = tmp_path / "workspace"
    _write(root, "app.py", "one\n")
    pristine = harness.file_hashes(root)
    _write(root, "app.py", "two\n")
    report = harness.layout_report(root, pristine, {"allow": ["app.py"], "ignore": []})
    assert report["out_of_layout"] == []
    assert report["modified"] == ["app.py"]


def test_loading_a_suite_reads_its_layout(tmp_path):
    suite_dir = tmp_path / "suites" / "demo"
    (suite_dir / "prompts").mkdir(parents=True)
    (suite_dir / "prompts" / "01.md").write_text("do it")
    (suite_dir / "layout.json").write_text(json.dumps({"allow": ["a.py"], "ignore": []}))
    suite = harness.load_suite(tmp_path / "suites", "demo")
    assert suite.layout == {"allow": ["a.py"], "ignore": []}


def test_a_suite_can_run_all_its_prompts_as_one(tmp_path):
    # "One prose brief" against "the same brief as steps" has to be one change,
    # so the flag concatenates the suite's own prompts instead of copying it.
    task = harness.load_suite(SUITES, "steps")
    assert len(task.prompts) > 1
    run_dir = harness.run_suite(
        task, runs_dir=tmp_path / "one", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi-session.sh"), single_prompt=True,
    )
    # The brief carries newlines, so the log is not one line per invocation.
    log = (run_dir / "workspace" / "session-log.txt").read_text()
    invocations = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\|", log)
    assert len(invocations) == 1, f"expected one invocation, saw {len(invocations)}"
    for text in task.prompts:
        assert text in log, f"brief lost {text}"


def test_a_record_says_which_machine_and_deadline_it_ran_on(tmp_path):
    # An M1 Pro and an M5 Max produce very different walls; a record that does
    # not name the machine invites the wrong comparison.
    task = harness.load_suite(SUITES, "add")
    harness._run_sessions(task, runs_dir=tmp_path / "runs",
                          pi_binary=str(FIX / "fake-pi.sh"), repeat=1,
                          grade_run=False, deadline=600, arm="worker")
    record = json.loads((next((tmp_path / "runs").iterdir()) / "run.json").read_text())
    assert record["deadline"] == 600
    assert record["machine"] == harness.machine_label()
    assert record["machine"], "machine label is empty"


def test_a_run_sweeps_the_processes_it_leaves_behind():
    # A worker that backgrounds `python app.py &` and then settles leaves a
    # server holding a port. The sweep finds it and ends it, and the run record
    # names what it found.
    child = subprocess.Popen(["sleep", "30"], start_new_session=True)
    try:
        time.sleep(0.2)
        found = harness.sweep_group(child.pid)
        assert any("sleep 30" in command for _, command in found), found
        child.wait(timeout=5)  # killed by the sweep, not by us
    finally:
        if child.poll() is None:
            child.kill()


def test_a_run_sweeps_a_server_started_in_its_own_session(tmp_path):
    # Pi's bash tool starts each command detached (a new session and process
    # group), so a server the model starts is outside Pi's group and survives
    # killpg. On 2026-10-29 a stalled session's `uvicorn` held port 8000 after
    # the run. The workspace sweep finds it by its working directory.
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    child = subprocess.Popen(["sleep", "31"], cwd=workspace, start_new_session=True)
    other = subprocess.Popen(["sleep", "32"], cwd=tmp_path, start_new_session=True)
    try:
        time.sleep(0.3)
        found = harness.sweep_workspace(workspace)
        assert any("sleep 31" in command for _, command in found), found
        assert not any("sleep 32" in command for _, command in found), found
        child.wait(timeout=5)  # killed by the sweep, not by us
        assert other.poll() is None, "a process outside the workspace was ended"
    finally:
        for p in (child, other):
            if p.poll() is None:
                p.kill()


def test_a_session_never_reads_the_callers_stdin(tmp_path):
    # Pi with -p appends piped stdin to its prompt. On 2026-10-29 a script fed
    # the harness its run lines on stdin, and the first session received the
    # next arm's command as part of its task and ran it. Sessions get no stdin.
    runs = tmp_path / "runs"
    result = subprocess.run(
        [sys.executable, str(HERE.parent / "harness.py"), "run", "--suites-dir", str(SUITES),
         "--suite", "add", "--pi-binary", str(FIX / "fake-pi-stdin.sh"), "--repeat", "1",
         "--runs-dir", str(runs)],
        input="the next arm's command\n", capture_output=True, text=True, timeout=120)
    assert result.returncode in (0, 1), result.stderr
    seen = next(runs.iterdir()) / "workspace" / "stdin.txt"
    assert seen.read_text() == ""


def test_a_stopped_run_still_sweeps_its_workspace(tmp_path):
    # /lesson stops a run it no longer shows (the learner pressed p mid-run).
    # On 2026-10-29 the stopped run's server kept port 8000: SIGTERM ended the
    # harness before its sweep. A stopped run must still end what it started.
    runs = tmp_path / "runs"
    harness_run = subprocess.Popen(
        [sys.executable, str(HERE.parent / "harness.py"), "run", "--suites-dir", str(SUITES),
         "--suite", "add", "--pi-binary", str(FIX / "fake-pi-server.sh"), "--repeat", "1",
         "--runs-dir", str(runs)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 30
        while not list(runs.glob("*/workspace/server.txt")) and time.monotonic() < deadline:
            time.sleep(0.2)
        workspace = next(runs.glob("*/workspace"))
        assert harness.workspace_members(workspace), "the fake server never started"
        harness_run.terminate()
        harness_run.wait(timeout=30)
        assert harness.workspace_members(workspace) == []
    finally:
        if harness_run.poll() is None:
            harness_run.kill()
        for w in runs.glob("*/workspace"):
            harness.sweep_workspace(w)


def test_the_think_tag_repair_is_a_unit_not_a_default():
    # The repair is context/repair-think-tags: a lesson shows the failure
    # without it, and every later line lists it (spec correction 2026-10-29).
    argv = harness.pi_argv("pi", PROFILE, harness.RECORDER, "p", "m", "go",
                           extension=harness.EXTENSION, extras=[Path("/x/unit.ts")])
    loaded = [argv[i + 1] for i, a in enumerate(argv) if a == "-e"]
    assert loaded == [str(harness.EXTENSION), "/x/unit.ts", str(harness.RECORDER)]


def test_a_group_with_nothing_left_reports_nothing(tmp_path):
    child = subprocess.Popen(["sh", "-c", "true"], start_new_session=True)
    child.wait(timeout=5)
    assert harness.sweep_group(child.pid) == []


def test_run_profile_flag_points_the_bare_arm_at_another_server(tmp_path, capsys):
    """--profile swaps the Pi profile (provider, model, sampling) without touching the arm."""
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "models.json").write_text(json.dumps({"providers": {"vllm": {
        "baseUrl": "http://127.0.0.1:8000/v1", "api": "openai-completions",
        "models": [{"id": "Mellum2.1-12B-A2.5B-Thinking"}]}}}))
    assert harness.main(["run", "--suite", "easy", "--dry-run", "--profile", str(profile)]) == 0
    argv = capsys.readouterr().out.split()
    assert argv[argv.index("--provider") + 1] == "vllm"
    assert argv[argv.index("--model") + 1] == "Mellum2.1-12B-A2.5B-Thinking"
    assert "--no-extensions" in argv


def test_run_suites_hand_run_suite_the_profile_they_are_given(tmp_path, monkeypatch):
    """--suite all threads the profile through to run_suite, which copies it into the run."""
    class Seen(Exception):
        pass

    def capture(suite, **kw):
        raise Seen(kw["profile"])

    monkeypatch.setattr(harness, "run_suite", capture)
    with pytest.raises(Seen) as seen:
        harness.run_suites(["easy"], runs_dir=tmp_path, profile=tmp_path / "p")
    assert seen.value.args == (tmp_path / "p",)


def _rows(*rows):
    return [json.dumps(r) for r in rows]


def test_open_tool_call_finds_a_call_with_no_result():
    t0 = "2026-10-28T18:11:25.000Z"
    trace = _rows({"type": "tool_call", "timestamp": t0, "toolName": "bash", "input": {"command": "uvicorn main:app"}})
    now = datetime.fromisoformat("2026-10-28T18:13:25+00:00").timestamp()
    assert harness.open_tool_call(trace, now) == (120.0, "uvicorn main:app")


def test_open_tool_call_ignores_a_call_that_returned():
    trace = _rows(
        {"type": "tool_call", "timestamp": "2026-10-28T18:11:20.000Z", "toolName": "bash", "input": {"command": "pytest"}},
        {"type": "tool_result", "timestamp": "2026-10-28T18:11:22.000Z", "toolName": "bash"},
    )
    assert harness.open_tool_call(trace, datetime.fromisoformat("2026-10-28T19:00:00+00:00").timestamp()) is None


def test_a_stalled_command_ends_the_session_and_is_recorded(tmp_path):
    started = time.monotonic()
    run_dir = harness.run_suite(
        harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs", profile=PROFILE,
        pi_binary=str(FIX / "fake-pi-stall.sh"), deadline=None, stall=2,
    )
    assert time.monotonic() - started < 20, "the stall cutoff did not end the session"
    stalled = json.loads((run_dir / "stalled").read_text())
    assert stalled["command"] == "uvicorn main:app" and stalled["seconds"] >= 2
    assert not (run_dir / "deadline").exists()


def test_the_stall_limit_reaches_the_record_and_the_summary(tmp_path, capsys):
    results = harness._run_sessions(
        harness.load_suite(SUITES, "add"), runs_dir=tmp_path, pi_binary=str(FIX / "fake-pi-stall.sh"),
        repeat=1, grade_run=False, deadline=None, profile=PROFILE, stall=2,
    )
    run_dir = results[0][0]
    record = json.loads((run_dir / "run.json").read_text())
    assert record["stall"] == 2 and record["stalled"]["command"] == "uvicorn main:app"
    assert harness.build_parser().parse_args(["run", "--suite", "easy", "--stall", "120"]).stall == 120


# --remedy and --extension: remedy units and a learner's own extensions, loaded on top of the arm.

def test_resolve_extras_maps_unit_names_and_expands_a_preset():
    names, paths = harness.resolve_extras("guard/break-repeat-loops,nudge/nudge-empty-turn", [])
    assert names == ["guard/break-repeat-loops", "nudge/nudge-empty-turn"]
    assert paths == [harness.REMEDIES / "guard" / "break-repeat-loops.ts",
                     harness.REMEDIES / "nudge" / "nudge-empty-turn.ts"]
    names, paths = harness.resolve_extras("preset:baseline-worker", [])
    preset = json.loads((harness.REMEDIES / "presets" / "baseline-worker.json").read_text())
    assert names == preset and len(paths) == len(preset) and all(p.is_file() for p in paths)


def test_resolve_extras_refuses_an_unknown_unit_and_lists_the_known_ones():
    with pytest.raises(SystemExit, match="guard/break-repeat-loops"):
        harness.resolve_extras("guard/no-such-unit", [])


def test_resolve_extras_refuses_a_missing_extension_file(tmp_path):
    with pytest.raises(SystemExit, match="no extension file"):
        harness.resolve_extras(None, [tmp_path / "missing.ts"])


def test_pi_argv_loads_extras_after_the_arm_and_before_the_recorder():
    argv = harness.pi_argv("pi", PROFILE, Path("rec.mjs"), "p", "m", "task",
                           extension=Path("worker.ts"), extras=[Path("a.ts"), Path("b.ts")])
    loads = [argv[i + 1] for i, a in enumerate(argv) if a == "-e"]
    assert loads == ["worker.ts", "a.ts", "b.ts", "rec.mjs"]


def test_the_parser_takes_remedy_and_repeatable_extension():
    args = harness.build_parser().parse_args(
        ["run", "--suite", "add", "--remedy", "preset:baseline-worker",
         "--extension", "a.ts", "--extension", "b.ts"])
    assert args.remedy == "preset:baseline-worker"
    assert args.extension == [Path("a.ts"), Path("b.ts")]


def test_a_session_loads_the_extras_and_records_them(tmp_path):
    own = tmp_path / "my-unit.ts"
    own.write_text("export default () => {};\n")
    names, paths = harness.resolve_extras("guard/break-repeat-loops", [own])
    results = harness._run_sessions(
        harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
        pi_binary=str(FIX / "fake-pi-argv.sh"), repeat=1, grade_run=False,
        deadline=None, remedies=names, extras=paths,
    )
    run_dir = results[0][0]
    argv = (run_dir / "workspace" / "argv.txt").read_text().splitlines()
    assert str(paths[0]) in argv and str(own) in argv
    record = json.loads((run_dir / "run.json").read_text())
    assert record["remedies"] == ["guard/break-repeat-loops"]
    assert [e["path"] for e in record["extensions"]] == [str(p) for p in paths]
    assert all(len(e["sha256"]) == 64 for e in record["extensions"])


def test_every_preset_resolves_and_each_tier_builds_on_the_last():
    presets = {p.stem: json.loads(p.read_text()) for p in (harness.REMEDIES / "presets").glob("*.json")}
    for name in presets:
        names, paths = harness.resolve_extras(f"preset:{name}", [])
        assert all(p.is_file() for p in paths), name
    assert presets["medium"][:len(presets["easy"])] == presets["easy"]


def test_a_relative_pi_binary_path_is_resolved_from_where_the_harness_runs(tmp_path, monkeypatch):
    # Pi runs with the workspace as its cwd, so a relative --pi-binary path must be made
    # absolute first; a bare command name (pi) is left for PATH lookup.
    monkeypatch.chdir(HERE.parent)
    rel = "tests/fixtures/fake-pi.sh"
    assert harness.resolve_pi_binary(rel) == str((HERE.parent / rel).resolve())
    assert harness.resolve_pi_binary("pi") == "pi"
    results = harness._run_sessions(
        harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
        pi_binary=harness.resolve_pi_binary(rel), repeat=1, grade_run=False, deadline=None)
    assert json.loads((results[0][0] / "run.json").read_text())["passed"] is True


def test_relative_runs_dir_and_profile_are_made_absolute_before_pi_runs(tmp_path, monkeypatch):
    # Pi runs with the workspace as its cwd: relative --runs-dir and --profile paths would
    # resolve the recorder and the profile inside the workspace, where they do not exist.
    monkeypatch.chdir(tmp_path)
    shutil.copytree(PROFILE, tmp_path / "prof")
    seen = {}
    monkeypatch.setattr(harness, "_run_sessions", lambda suite, **kw: seen.update(kw) or [])
    monkeypatch.setattr(harness, "_print_task", lambda *a, **k: None)
    harness.main(["run", "--suites-dir", str(SUITES), "--suite", "add", "--runs-dir", "runs/x", "--profile", "prof"])
    assert seen["runs_dir"] == tmp_path / "runs" / "x"
    assert seen["profile"] == tmp_path / "prof"
