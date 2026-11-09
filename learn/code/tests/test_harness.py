import hashlib
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


def test_context_files_switch_keeps_or_drops_agents_md():
    task = harness.load_suite(SUITES, "add")
    cold = harness.pi_argv("pi", PROFILE, Path("rec.mjs"), "p", "m", task.prompt)
    warm = harness.pi_argv("pi", PROFILE, Path("rec.mjs"), "p", "m", task.prompt,
                           context_files=True)
    # Cold is the default: the workspace's own AGENTS.md is stripped with everything else.
    assert "--no-context-files" in cold
    # Warm keeps it, and drops nothing else from the isolation bundle.
    assert "--no-context-files" not in warm
    for flag in ("--no-approve", "--no-extensions", "--no-skills",
                 "--no-prompt-templates", "--no-themes"):
        assert flag in warm


def test_arms_select_the_extension():
    worker = harness.arm_settings("worker")
    assert worker["extension"].name == "mellum-worker.ts"
    assert worker["env"] == {"MELLUM_MODE": "1"}
    # The worker is always loaded, even on the bare arm, but mode stays off (no MELLUM_MODE), so bare
    # still sends vanilla Pi's requests — the engagement is MELLUM_MODE=1, not the extension's presence.
    bare = harness.arm_settings("bare")
    assert bare["extension"].name == "mellum-worker.ts"
    assert "MELLUM_MODE" not in bare["env"]
    # vanilla is the true floor: no worker extension at all, only the recorder.
    assert harness.arm_settings("vanilla")["extension"] is None


def test_the_dead_ablation_arms_are_gone():
    # The decoupled worker reads only MELLUM_STRIP_THINKING; MELLUM_GUARDS,
    # MELLUM_WORKER_PROMPT and MELLUM_MODE_FACTS are read by nothing, so the arms
    # that set them were inert and have been removed. Ablation is a `--remedy` now.
    assert harness.ARMS == ("vanilla", "bare", "worker", "strip-thinking")
    for dead in ("no-prompt", "no-nudge", "no-loop", "no-facts", "server-guard", "no-facts-guard"):
        with pytest.raises(SystemExit):
            harness.arm_settings(dead)


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


def test_score_keeps_the_run_without_copying_hidden_tests(tmp_path):
    run_dir = run(tmp_path, "fake-pi-empty.sh")
    passed, tail = harness.score(run_dir, harness.load_suite(SUITES, "add"))
    assert not passed
    assert not (run_dir / "workspace" / "grader_tests").exists()
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
        "wall": None, "nudges": 0, "empty_finals": 0, "guard_blocks": 0,
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
    roadmap = (suite.root / "base" / "specs" / "roadmap.md").read_text(encoding="utf-8")
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
        text = (split / "specs" / f"{name}.md").read_text(encoding="utf-8")
        for line in lines:
            assert line in text, f"{name} lost: {line}"


def test_active_variant_notes_name_the_verification_loop():
    suite = harness.load_suite(harness.SUITES, "medium")
    for arm in ("joined", "split"):
        variant = harness.load_variant(suite, arm)
        assert len(list((variant / "prompts").glob("*.md"))) == 4
        notes = variant / "AGENTS.md"
        if not notes.is_file():
            notes = suite.root / "base/AGENTS.md"
        text = " ".join(notes.read_text().split())
        assert "python -m pytest tests" in text
        assert "Do not start a server to check your work; run the tests." in text


def test_medium_base_ships_a_phase1_smoke_test():
    suite = harness.load_suite(harness.SUITES, "medium")
    test = suite.root / "base" / "tests" / "test_home.py"
    assert test.is_file(), "the base project ships no test, so its test command has nothing to run"
    text = test.read_text()
    assert "TestClient" in text
    assert "Come in. Sit down." in text


def test_medium_asks_for_the_home_page_in_process():
    suite = harness.load_suite(harness.SUITES, "medium")
    roadmap = (suite.root / "base" / "specs" / "roadmap.md").read_text(encoding="utf-8")
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
    # No trace rows, but the process still ran: wall is its time, not the trace's span.
    assert record["wall"] > 0


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


def _one_record(tmp_path, binary, deadline=600):
    harness._run_sessions(harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
                          pi_binary=str(FIX / binary), repeat=1, grade_run=False,
                          deadline=deadline)
    run_dir = next((tmp_path / "runs").iterdir())
    return run_dir, json.loads((run_dir / "run.json").read_text())


def test_a_run_records_process_elapsed_time(tmp_path):
    # The budget is the time the Pi processes ran, not the span of trace rows:
    # F.1's 900 s hang read 59.8 s from the trace.
    run_dir = run(tmp_path)
    execution = json.loads((run_dir / "execution.json").read_text())
    assert execution["termination_reason"] == "exited"
    assert execution["exit_code"] == 0
    assert execution["elapsed_seconds"] > 0
    assert execution["cleanup_ok"] is True


def test_a_deadline_is_recorded_as_the_completion(tmp_path):
    _, record = _one_record(tmp_path, "fake-pi-slow.sh", deadline=1)
    assert record["completion"] == "deadline"
    assert record["wall"] >= 1


def test_a_settled_run_says_so(tmp_path):
    _, record = _one_record(tmp_path, "fake-pi.sh")
    assert record["completion"] == "settled"


def test_wall_is_the_process_time_not_the_trace_span(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [
        {"type": "instance_start", "timestamp": "2026-10-21T00:00:00+00:00"},
        {"type": "agent_settled", "timestamp": "2026-10-21T00:00:01+00:00"},
    ])
    assert harness.report(run_dir)["wall"] is None
    (run_dir / "execution.json").write_text(json.dumps({"elapsed_seconds": 900.0}))
    assert harness.report(run_dir)["wall"] == 900.0


def test_turns_count_completed_replies_not_requests(tmp_path):
    # A request whose reply errored (a retry, a dead backend) is a request, not a turn.
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    reply = lambda stop: {"type": "message_end", "message": {
        "role": "assistant", "stopReason": stop, "content": [{"type": "text", "text": "x"}]}}
    _write_trace(run_dir, [
        {"type": "provider_request"}, reply("error"),
        {"type": "provider_request"}, reply("toolUse"),
        {"type": "provider_request"}, reply("stop"),
    ])
    counts = harness.report(run_dir)
    assert counts["requests"] == 3
    assert counts["turns"] == 2


def test_context_counts_the_cached_prompt_too(tmp_path):
    # Pi's usage.input excludes the cached prefix; the F.3 smoke read 1,703 for an
    # 11,438-token prompt (870 uncached + 10,568 cache reads).
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [{"type": "message_end", "message": {
        "role": "assistant", "stopReason": "stop", "content": [{"type": "text", "text": "x"}],
        "usage": {"input": 870, "output": 5, "cacheRead": 10568, "cacheWrite": 0}}}])
    assert harness.report(run_dir)["context"] == 11438


def test_an_errored_last_reply_is_an_error_not_settled(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [{"type": "message_end", "message": {
        "role": "assistant", "stopReason": "error", "content": []}}])
    (run_dir / "execution.json").write_text(json.dumps({
        "elapsed_seconds": 3.0, "exit_code": 0, "termination_reason": "exited",
        "cleanup_ok": True}))
    assert harness.execution_outcome(run_dir)["completion"] == "error"


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


def test_a_record_names_the_environment_settings_a_run_used(tmp_path, monkeypatch):
    # Nothing else in a record says these were set, and each changes what a session did.
    monkeypatch.setenv("MELLUM_MEDIATED_MAX", "2")
    monkeypatch.delenv("MELLUM_BOUND_SECONDS", raising=False)
    monkeypatch.setenv("VERIFY_PYTEST", "pytest -x")
    harness._run_sessions(harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
                          pi_binary=str(FIX / "fake-pi.sh"), repeat=1, grade_run=False, deadline=60, arm="worker")
    record = json.loads((next((tmp_path / "runs").iterdir()) / "run.json").read_text())
    assert record["recorded_env"] == {"MELLUM_BOUND_SECONDS": None, "MELLUM_MEDIATED_MAX": "2",
                                      "VERIFY_PYTEST": "pytest -x"}


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


@pytest.mark.skipif(os.name == "nt", reason="finds the server by its cwd (lsof); Windows has no such "
                    "lookup and uses a job object instead: see the windows_ tests")
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


@pytest.mark.skipif(os.name == "nt", reason="a SIGTERM stop; Windows stops with a hard kill, covered by "
                    "test_a_killed_harness_takes_its_sessions_processes_with_it")
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
    assert loaded == [str(harness.EXTENSION), str(Path("/x/unit.ts")), str(harness.RECORDER)]


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
    names, paths = harness.resolve_extras("guard/repeat-loops,nudge/empty-turn", [])
    assert names == ["guard/repeat-loops", "nudge/empty-turn"]
    assert paths == [harness.REMEDIES / "guard" / "repeat-loops.ts",
                     harness.REMEDIES / "nudge" / "empty-turn.ts"]
    names, paths = harness.resolve_extras("preset:baseline-worker", [])
    preset = json.loads((harness.REMEDIES / "presets" / "baseline-worker.json").read_text())
    assert names == preset and len(paths) == len(preset) and all(p.is_file() for p in paths)


def test_resolve_extras_refuses_an_unknown_unit_and_lists_the_known_ones():
    with pytest.raises(SystemExit, match="guard/repeat-loops"):
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
    names, paths = harness.resolve_extras("guard/repeat-loops", [own])
    results = harness._run_sessions(
        harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
        pi_binary=str(FIX / "fake-pi-argv.sh"), repeat=1, grade_run=False,
        deadline=None, remedies=names, extras=paths,
    )
    run_dir = results[0][0]
    argv = (run_dir / "workspace" / "argv.txt").read_text().splitlines()
    assert str(paths[0]) in argv and str(own) in argv
    record = json.loads((run_dir / "run.json").read_text())
    assert record["remedies"] == ["guard/repeat-loops"]
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


# Windows: no ps, lsof, killpg or SIGKILL, and Pi is an npm .cmd shim.
windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows process handling")

SHIM = ('@ECHO off\r\nGOTO start\r\n:start\r\nendLocal & goto #_undefined_# 2>NUL || '
        r'title %COMSPEC% & "%_prog%"  "%dp0%\node_modules\pkg\dist\cli.js" %*' '\r\n')


@windows_only
def test_an_npm_shim_runs_its_script_with_node_directly(tmp_path, monkeypatch):
    # cmd.exe would mangle a multi-line prompt holding < > % and quotes.
    (tmp_path / "pi.cmd").write_text(SHIM)
    (tmp_path / "node.exe").write_text("")
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    argv = harness.native_argv(["pi", "--flag", "a <b>\n%c%"])
    assert argv == [str(tmp_path / "node.exe"),
                    str(tmp_path / "node_modules" / "pkg" / "dist" / "cli.js"),
                    "--flag", "a <b>\n%c%"]


def test_native_argv_leaves_other_platforms_alone(monkeypatch):
    monkeypatch.setattr(harness, "WINDOWS", False)
    assert harness.native_argv(["pi", "x"]) == ["pi", "x"]


def _alive(pid: int) -> bool:
    return any(row["ProcessId"] == pid for row in harness.windows_processes())


@windows_only
def test_a_windows_workspace_sweep_ends_a_process_left_inside_it(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    child = harness.start_child([sys.executable, "-c", "import time; time.sleep(120)",
                                 str(workspace / "app.py")], cwd=workspace)
    try:
        found = harness.sweep_workspace(workspace)
        assert child.pid in [pid for pid, _ in found]
        child.wait(timeout=10)
    finally:
        child.kill()


@windows_only
def test_a_windows_group_sweep_ends_a_child_its_parent_left_behind(tmp_path):
    marker = tmp_path / "orphan.pid"
    parent = harness.start_child([sys.executable, "-c", textwrap.dedent(f"""
        import subprocess, sys
        orphan = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
        open({str(marker)!r}, "w").write(str(orphan.pid))
        """)])
    parent.wait(timeout=30)
    orphan = int(marker.read_text())
    try:
        found = harness.sweep_group(parent.pid)
        assert orphan in [pid for pid, _ in found]
        assert not _alive(orphan)
    finally:
        harness.kill_tree(orphan)


def test_windows_relaunches_in_utf8_mode(monkeypatch):
    # Traces are UTF-8; Windows reads files in its ANSI code page by default.
    monkeypatch.setattr(harness, "WINDOWS", True)
    argv = harness.utf8_relaunch_argv(["harness.py", "run"], utf8_mode=0)
    assert argv == [sys.executable, "-X", "utf8", "harness.py", "run"]


def test_utf8_mode_or_other_platforms_need_no_relaunch(monkeypatch):
    monkeypatch.setattr(harness, "WINDOWS", False)
    assert harness.utf8_relaunch_argv(["harness.py"], utf8_mode=0) is None
    monkeypatch.setattr(harness, "WINDOWS", True)
    assert harness.utf8_relaunch_argv(["harness.py"], utf8_mode=1) is None


@windows_only
def test_a_shell_script_pi_runs_through_bash_on_windows(tmp_path):
    # Windows cannot start a .sh file itself; a --pi-binary script runs through bash.
    script = tmp_path / "fake-pi.sh"
    script.write_text("#!/bin/sh\necho hi\n")
    argv = harness.native_argv([str(script), "--flag"])
    assert Path(argv[0]).name.lower() in ("bash", "bash.exe")
    assert argv[1:] == [str(script), "--flag"]


@windows_only
def test_a_killed_harness_takes_its_sessions_processes_with_it(tmp_path):
    # Stopping a run on Windows is a hard kill: no SIGTERM, so no sweep runs.
    # The job object is set to end its processes when the harness that holds it dies.
    marker = tmp_path / "grandchild.pid"
    # The session: starts a grandchild, records its pid (path as argv[1]), then waits.
    session = tmp_path / "session.py"
    session.write_text(textwrap.dedent("""
        import subprocess, sys, time
        g = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
        open(sys.argv[1], "w").write(str(g.pid))
        time.sleep(120)
        """))
    # The harness stand-in: starts the session in a job, then waits to be killed.
    holder_py = tmp_path / "holder.py"
    holder_py.write_text(textwrap.dedent("""
        import sys, time
        sys.path.insert(0, sys.argv[1])
        import harness
        harness.start_child([sys.executable, sys.argv[2], sys.argv[3]])
        time.sleep(120)
        """))
    holder = subprocess.Popen([sys.executable, str(holder_py), str(HERE.parent),
                               str(session), str(marker)])
    try:
        deadline = time.monotonic() + 30
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        grandchild = int(marker.read_text())
        assert any(row["ProcessId"] == grandchild for row in harness.windows_processes())
        holder.kill()
        holder.wait(timeout=10)
        time.sleep(1)
        assert not any(row["ProcessId"] == grandchild for row in harness.windows_processes())
    finally:
        holder.kill()
        if marker.exists():
            harness.kill_tree(int(marker.read_text()))


def test_session_path_drops_the_harness_venv(tmp_path):
    venv = tmp_path / "harness-venv"
    path = os.pathsep.join([str(venv / "bin"), "/usr/local/bin", str(Path(sys.prefix) / "bin"), "/usr/bin"])
    entries = harness.session_path(path, str(venv)).split(os.pathsep)
    assert str(venv / "bin") not in entries
    assert str(Path(sys.prefix) / "bin") not in entries or sys.prefix == sys.base_prefix
    assert [e for e in entries if e in ("/usr/local/bin", "/usr/bin")] == ["/usr/local/bin", "/usr/bin"]


def test_a_session_does_not_inherit_the_harness_venv_on_path(tmp_path, monkeypatch):
    # `uv run` puts the harness venv first on PATH; a session that inherits it runs the
    # repository's python and uvicorn instead of the workspace's (LC.41).
    venv = tmp_path / "harness-venv"
    monkeypatch.setenv("VIRTUAL_ENV", str(venv))
    monkeypatch.setenv("PATH", os.pathsep.join([str(venv / "bin"), str(Path(sys.prefix) / "bin"),
                                                "/usr/bin", "/bin", "/usr/sbin", "/sbin"]))
    run_dir = run(tmp_path, binary="fake-pi-path.sh")
    entries = (run_dir / "workspace" / "path.txt").read_text().strip().split(os.pathsep)
    assert str(venv / "bin") not in entries
    assert str(Path(sys.prefix) / "bin") not in entries or sys.prefix == sys.base_prefix
    assert "/usr/bin" in entries and "/bin" in entries


def test_a_listener_on_a_guarded_port_refuses_the_session(tmp_path, monkeypatch):
    # A stray server on the suite app's port answered for the model for 13 hours (LC.41).
    import socket
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    monkeypatch.setattr(harness, "GUARDED_PORTS", (port,))
    try:
        with pytest.raises(SystemExit, match=str(port)):
            run(tmp_path)
    finally:
        listener.close()
    assert not list((tmp_path / "runs").rglob("execution.json"))


def test_a_free_guarded_port_lets_the_session_run(tmp_path, monkeypatch):
    import socket
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    monkeypatch.setattr(harness, "GUARDED_PORTS", (port,))
    assert harness.guarded_listeners((port,)) == []
    assert (run(tmp_path) / "execution.json").is_file()


def _dry_run(runs_dir, *extra):
    return harness.main(["run", "--suite", "add", "--suites-dir", str(SUITES), "--runs-dir", str(runs_dir),
                         "--pi-binary", str(FIX / "fake-pi.sh"), "--dry-run", *extra])


def test_a_runs_dir_inside_a_project_is_refused(tmp_path):
    # uv discovers a parent pyproject.toml; LC.41's session installed into the repository's .venv.
    project = tmp_path / "proj"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    with pytest.raises(SystemExit, match="pyproject.toml"):
        _dry_run(project / "runs" / "batch", "--host-card", str(tmp_path / "card.json"))


def test_an_uncounted_run_inside_a_project_warns_and_runs(tmp_path, capsys):
    # baseline.py, lesson-check.sh and improve.py write under the repository's runs/ (final review).
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    assert _dry_run(tmp_path / "repo" / "runs") == 0
    assert "inside a project" in capsys.readouterr().err


def test_a_runs_dir_in_a_git_checkout_is_refused(tmp_path):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    with pytest.raises(SystemExit, match=r"\.git"):
        _dry_run(tmp_path / "repo" / "runs", "--host-card", str(tmp_path / "card.json"))


def test_the_default_runs_dir_is_outside_any_project(tmp_path):
    assert harness.project_above(harness.RUNS) is None
    assert _dry_run(tmp_path / "runs") == 0


def test_run_json_names_the_pi_version_the_run_used(tmp_path):
    results = harness._run_sessions(
        harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
        pi_binary=str(FIX / "fake-pi-version.sh"), repeat=1, grade_run=False, deadline=None,
    )
    assert json.loads((results[0][0] / "run.json").read_text())["pi_version"] == "1.4.0"


def test_pi_version_is_none_when_pi_cannot_say(tmp_path):
    broken = tmp_path / "pi"
    broken.write_text("#!/bin/sh\nexit 1\n")
    broken.chmod(0o755)
    assert harness.pi_version(str(broken)) is None
    assert harness.pi_version(str(tmp_path / "missing")) is None


# --- F.5: the session budget, enforced at a proxy -------------------------------------------

def test_each_tier_carries_its_budget():
    easy, medium, hard = (harness.load_suite(harness.SUITES, name).budget for name in ("easy", "medium", "hard"))
    assert easy == {"max_requests": 128, "max_output_tokens": 64000, "unknown_usage_charge": 16384,
                    "wall_safety_seconds": 1200}
    assert medium == hard == {"max_requests": 400, "max_output_tokens": 300000, "unknown_usage_charge": 16384,
                              "wall_safety_seconds": 3600}
    assert harness.load_suite(SUITES, "add").budget is None


def test_proxy_target_splits_the_profile_base_url():
    assert harness.proxy_target("http://127.0.0.1:8001/v1") == ("http://127.0.0.1:8001/", "/v1")
    assert harness.proxy_target("http://127.0.0.1:8001/v1/") == ("http://127.0.0.1:8001/", "/v1")
    assert harness.proxy_target("http://127.0.0.1:8001") == ("http://127.0.0.1:8001/", "")


def test_a_budget_spent_before_pi_exits_on_its_own_still_ends_as_budget(tmp_path):
    # Pi can exit the moment it is refused, before a poll sees the log (review of the plan).
    log = tmp_path / "proxy.jsonl"
    log.write_text('{"boundary":"budget_exhausted","id":null}\n')
    child = subprocess.Popen(["true"])
    child.wait()
    assert harness.wait_or_stall(child, tmp_path, tmp_path / "trace.jsonl", None, None, budget_log=log) == "budget"


class _Upstream:
    """A llama-server stand-in: every completion streams `tokens` output tokens with usage."""

    def __init__(self, tokens=10):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        upstream = self
        self.hits = 0

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("content-length", 0)))
                upstream.hits += 1
                body = (f'data: {{"choices":[],"usage":{{"completion_tokens":{tokens}}}}}\n\n'
                        "data: [DONE]\n\n").encode()
                self.send_response(200)
                self.send_header("content-type", "text/event-stream")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.port = self.server.server_address[1]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def _budgeted(tmp_path, binary, budget, tokens=10):
    upstream = _Upstream(tokens)
    profile = tmp_path / "profile"
    shutil.copytree(PROFILE, profile)
    models = json.loads((profile / "models.json").read_text())
    for provider in models["providers"].values():
        provider["baseUrl"] = f"http://127.0.0.1:{upstream.port}/v1"     # the real profile's shape
    (profile / "models.json").write_text(json.dumps(models))
    try:
        run_dir = harness.run_suite(harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs",
                                    profile=profile, pi_binary=str(FIX / binary), budget=budget)
    finally:
        upstream.close()
    return run_dir, upstream


def _limits(requests=50, output=100000, wall=30):
    return {"max_requests": requests, "max_output_tokens": output, "unknown_usage_charge": 16384,
            "wall_safety_seconds": wall}


def _proxy_gone(run_dir):
    # Not only the pid the harness started: `node` may be a shim (Volta) whose child is the proxy.
    pid = json.loads((run_dir / "proxy.json").read_text())["pid"]
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    time.sleep(0.2)
    ps = subprocess.run(["ps", "-axo", "command="], capture_output=True, text=True).stdout
    assert str(run_dir / "proxy.jsonl") not in ps


def test_a_session_past_its_request_budget_ends_as_budget_and_counts(tmp_path):
    run_dir, upstream = _budgeted(tmp_path, "fake-pi-requests.mjs", _limits(requests=3))
    outcome = harness.execution_outcome(run_dir)
    assert outcome["completion"] == "budget" and outcome["censored"] is False
    assert upstream.hits == 3
    assert (run_dir / "workspace" / "requests.txt").read_text().split() == ["3", "429"]
    assert harness.budget_record(run_dir) == {"limits": _limits(requests=3),
                                              "spent": {"requests": 3, "output_tokens": 30}}
    _proxy_gone(run_dir)


def test_a_session_past_its_output_token_budget_ends_as_budget(tmp_path):
    run_dir, upstream = _budgeted(tmp_path, "fake-pi-requests.mjs", _limits(output=25))
    assert harness.execution_outcome(run_dir)["completion"] == "budget"
    assert harness.budget_record(run_dir)["spent"] == {"requests": 3, "output_tokens": 30}
    _proxy_gone(run_dir)


def test_a_session_that_hits_wall_safety_is_censored(tmp_path):
    run_dir, _ = _budgeted(tmp_path, "fake-pi-slow.sh", _limits(wall=1))
    outcome = harness.execution_outcome(run_dir)
    assert outcome["completion"] == "wall_safety" and outcome["censored"] is True
    assert (run_dir / "wall_safety").is_file()
    _proxy_gone(run_dir)


def test_a_counted_run_takes_no_deadline_or_budget_override(tmp_path):
    for flag in (["--deadline", "5"], ["--budget", str(tmp_path / "b.json")]):
        with pytest.raises(SystemExit):
            harness.main(["run", "--suite", "add", "--suites-dir", str(SUITES), "--runs-dir", str(tmp_path / "r"),
                          "--pi-binary", str(FIX / "fake-pi.sh"), "--host-card", str(tmp_path / "c.json"),
                          "--dry-run", *flag])


def test_a_counted_run_needs_a_suite_with_a_budget(tmp_path):
    with pytest.raises(SystemExit, match="budget"):
        harness.main(["run", "--suite", "add", "--suites-dir", str(SUITES), "--runs-dir", str(tmp_path / "r"),
                      "--pi-binary", str(FIX / "fake-pi.sh"), "--host-card", str(tmp_path / "c.json")])


def test_every_run_on_a_tier_is_budgeted_counted_or_not():
    easy = harness.load_suite(harness.SUITES, "easy")
    assert harness.session_budget(easy, False, None) == easy.budget
    assert harness.session_budget(easy, True, None) == easy.budget
    override = {**easy.budget, "max_requests": 5}
    assert harness.session_budget(easy, False, override) == override
    assert harness.session_budget(harness.load_suite(SUITES, "add"), False, None) is None


def test_an_explicit_deadline_on_a_budgeted_run_ends_as_deadline(tmp_path):
    # baseline.py's --deadline keeps its meaning; only the suite's own hang-guard is censored.
    upstream = _Upstream()
    profile = tmp_path / "profile"
    shutil.copytree(PROFILE, profile)
    models = json.loads((profile / "models.json").read_text())
    for provider in models["providers"].values():
        provider["baseUrl"] = f"http://127.0.0.1:{upstream.port}/v1"
    (profile / "models.json").write_text(json.dumps(models))
    try:
        run_dir = harness.run_suite(harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs", profile=profile,
                                    pi_binary=str(FIX / "fake-pi-slow.sh"), budget=_limits(wall=30), deadline=1)
    finally:
        upstream.close()
    outcome = harness.execution_outcome(run_dir)
    assert outcome["completion"] == "deadline" and outcome["censored"] is False


# --- F.5: the host gate -------------------------------------------------------------------

import conformance


def _free_port():
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class _FakeLlama:
    """A real process on a port, with a llama-server command line, serving /props and /slots."""

    def __init__(self, tmp_path, *changes, build="b12110-cd959bae9"):
        self.port = _free_port()
        pins = conformance.load_pins()
        argv = conformance.server_argv(pins, binary="llama-server", model=str(tmp_path / pins["weights"]["file"]),
                                       port=self.port, threads=16, log=str(tmp_path / "server.log"))[1:]
        for flag, value in changes:
            argv[argv.index(flag) + 1] = value
        self.child = subprocess.Popen([sys.executable, str(FIX / "fake-llama-server.py"), *argv],
                                      env={**os.environ, "FAKE_BUILD_INFO": build},
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.endpoint = f"http://127.0.0.1:{self.port}"
        for _ in range(200):
            if conformance.server_command(self.port):
                break
            time.sleep(0.05)

    def close(self):
        self.child.terminate()
        self.child.wait()


def _card(tmp_path, server, passed=True, pins=None):
    """A card as conformance.check records it, for the server that is live now."""
    pins = pins or conformance.load_pins()
    props = json.loads(subprocess.run(["curl", "-s", server.endpoint + "/props"], capture_output=True, text=True).stdout)
    slots = json.loads(subprocess.run(["curl", "-s", server.endpoint + "/slots"], capture_output=True, text=True).stdout)
    card = {"schema": conformance.SCHEMA, "passed": passed, "pins_digest": conformance.pins_digest(pins),
            "items": {}, "build_info": props["build_info"], "model_path": props["model_path"],
            "slots": [s["n_ctx"] for s in slots], "server_command": conformance.server_command(server.port)}
    path = tmp_path / "host-card.json"
    path.write_text(json.dumps(card))
    return path


@pytest.fixture
def live(tmp_path):
    server = _FakeLlama(tmp_path)
    yield server
    server.close()


def test_the_host_gate_accepts_a_passing_card_for_the_live_server(tmp_path, live):
    card = _card(tmp_path, live)
    record = harness.host_gate(card, live.endpoint, conformance.load_pins())
    assert record == {"path": str(card), "sha256": conformance.sha256_file(card), "passed": True}


def test_the_host_gate_refuses_a_failed_card(tmp_path, live):
    with pytest.raises(SystemExit, match="did not pass"):
        harness.host_gate(_card(tmp_path, live, passed=False), live.endpoint, conformance.load_pins())


def test_the_host_gate_refuses_a_card_from_another_pin_card(tmp_path, live):
    pins = conformance.load_pins()
    pins["tooling"]["pi"] = "1.3.0"
    with pytest.raises(SystemExit, match="pin card"):
        harness.host_gate(_card(tmp_path, live, pins=pins), live.endpoint, conformance.load_pins())


@pytest.mark.parametrize("change", [("-c", "50000"), ("-ngl", "0"), ("-ctk", "f16")])
def test_the_host_gate_refuses_a_restart_with_changed_flags(tmp_path, live, change):
    # Same build and weights, restarted differently: the old card does not cover it (review of the plan).
    card = _card(tmp_path, live)
    live.close()
    restarted = _FakeLlama(tmp_path, change)
    try:
        with pytest.raises(SystemExit, match="since the card"):
            harness.host_gate(card, restarted.endpoint, conformance.load_pins())
    finally:
        restarted.close()


def test_the_host_gate_refuses_another_build(tmp_path, live):
    card = _card(tmp_path, live)
    live.close()
    other = _FakeLlama(tmp_path, build="b11669-620d2225c")
    try:
        with pytest.raises(SystemExit, match="build_info"):
            harness.host_gate(card, other.endpoint, conformance.load_pins())
    finally:
        other.close()


def test_a_run_without_a_host_card_runs_and_is_uncounted(tmp_path):
    runs = tmp_path / "runs"
    assert harness.main(["run", "--suite", "add", "--suites-dir", str(SUITES), "--runs-dir", str(runs),
                         "--pi-binary", str(FIX / "fake-pi.sh")]) == 0
    record = json.loads(next(runs.glob("*/run.json")).read_text())
    assert (record["counted"], record["host_card"]) == (False, None)


def test_run_json_says_whether_a_run_counted(tmp_path):
    suite = harness.load_suite(SUITES, "add")
    gate = {"path": "/cards/host-card.json", "sha256": "ab" * 32, "passed": True}
    counted = harness._run_sessions(suite, runs_dir=tmp_path / "a", pi_binary=str(FIX / "fake-pi.sh"), repeat=1,
                                    grade_run=False, deadline=None, host_card=gate)
    uncounted = harness._run_sessions(suite, runs_dir=tmp_path / "b", pi_binary=str(FIX / "fake-pi.sh"), repeat=1,
                                      grade_run=False, deadline=None)
    first = json.loads((counted[0][0] / "run.json").read_text())
    second = json.loads((uncounted[0][0] / "run.json").read_text())
    assert (first["counted"], first["host_card"]) == (True, gate)
    assert (second["counted"], second["host_card"]) == (False, None)


def test_a_harness_stopped_while_the_proxy_starts_leaves_no_proxy(tmp_path, monkeypatch):
    # main turns SIGTERM into SystemExit; one that lands while waiting for `ready` must not orphan it.
    real = harness._jsonl

    def stopped(path):
        if Path(path).name == "proxy.jsonl":
            raise SystemExit(143)
        return real(path)

    monkeypatch.setattr(harness, "_jsonl", stopped)
    log = tmp_path / "proxy.jsonl"
    with pytest.raises(SystemExit):
        harness.start_budget_proxy(_limits(), "http://127.0.0.1:9/", log)
    time.sleep(0.2)
    ps = subprocess.run(["ps", "-axo", "command="], capture_output=True, text=True).stdout
    assert str(log) not in ps


def test_a_lan_profile_runs_without_the_proxy_and_is_still_bounded(tmp_path, capsys):
    # The proxy forwards to loopback only; lesson-check.sh's lan-profile is not (final review).
    profile = tmp_path / "profile"
    shutil.copytree(PROFILE, profile)
    models = json.loads((profile / "models.json").read_text())
    for provider in models["providers"].values():
        provider["baseUrl"] = "http://192.0.2.1:11485/v1"
    (profile / "models.json").write_text(json.dumps(models))
    run_dir = harness.run_suite(harness.load_suite(SUITES, "add"), runs_dir=tmp_path / "runs", profile=profile,
                                pi_binary=str(FIX / "fake-pi-slow.sh"), budget=_limits(wall=1))
    assert harness.execution_outcome(run_dir)["completion"] == "wall_safety"
    assert not (run_dir / "proxy.json").exists() and harness.budget_record(run_dir) is None
    assert "loopback" in (run_dir / "budget-unenforced").read_text()
    assert "not enforced" in capsys.readouterr().err


def test_a_counted_run_needs_a_loopback_server(tmp_path):
    profile = tmp_path / "profile"
    shutil.copytree(PROFILE, profile)
    models = json.loads((profile / "models.json").read_text())
    for provider in models["providers"].values():
        provider["baseUrl"] = "http://192.0.2.1:11485/v1"
    (profile / "models.json").write_text(json.dumps(models))
    (tmp_path / "card.json").write_text("{}")
    with pytest.raises(SystemExit, match="loopback"):
        harness.main(["run", "--suite", "easy", "--runs-dir", str(tmp_path / "r"), "--profile", str(profile),
                      "--pi-binary", str(FIX / "fake-pi.sh"), "--host-card", str(tmp_path / "card.json")])


def _mediated_suite(tmp_path):
    root = tmp_path / "suites" / "steps"
    shutil.copytree(SUITES / "steps", root)
    (root / "mediated").mkdir()
    for name in ("test_01_one.py", "test_02_two.py"):
        (root / "mediated" / name).write_text("def test_it():\n    pass\n")
    return harness.load_suite(tmp_path / "suites", "steps")


MEDIATED_UNIT = harness.REMEDIES / "check" / "mediated-test.ts"


def test_mediated_tests_belong_to_their_prompt_and_every_later_one(tmp_path):
    suite = _mediated_suite(tmp_path)
    assert [p.name for p in harness.mediated_tests(suite, 1)] == ["test_01_one.py"]
    assert [p.name for p in harness.mediated_tests(suite, 2)] == ["test_01_one.py", "test_02_two.py"]
    assert [p.name for p in harness.mediated_tests(suite, None)] == ["test_01_one.py", "test_02_two.py"]


def test_a_mediated_test_must_name_its_prompt(tmp_path):
    suite = _mediated_suite(tmp_path)
    (suite.root / "mediated" / "test_extra.py").write_text("")
    with pytest.raises(SystemExit, match="test_NN_"):
        harness.mediated_tests(suite, 1)


def test_each_prompt_gets_its_mediated_tests_from_outside_the_workspace(tmp_path):
    suite = _mediated_suite(tmp_path)
    run_dir = harness.run_suite(suite, runs_dir=tmp_path / "runs", profile=PROFILE,
                                pi_binary=str(FIX / "fake-pi-mediated.sh"), extras=[MEDIATED_UNIT])
    first, second = (run_dir / "workspace" / "mediated.txt").read_text().splitlines()
    mediated = suite.root / "mediated"
    assert first.split(os.pathsep) == [str(mediated / "test_01_one.py")]
    assert second.split(os.pathsep) == [str(mediated / "test_01_one.py"), str(mediated / "test_02_two.py")]
    assert not (run_dir / "workspace" / "mediated").exists()
    digest = hashlib.sha256(b"def test_it():\n    pass\n").hexdigest()
    assert json.loads((run_dir / "mediated.json").read_text()) == [
        [{"name": "test_01_one.py", "sha256": digest}],
        [{"name": "test_01_one.py", "sha256": digest}, {"name": "test_02_two.py", "sha256": digest}]]


@pytest.mark.parametrize("unit", ["mediated-test-show.ts", "mediated-test-settle.ts"])
def test_each_half_of_the_mediated_test_gets_the_suites_tests(tmp_path, unit):
    suite = _mediated_suite(tmp_path)
    run_dir = harness.run_suite(suite, runs_dir=tmp_path / "runs", pi_binary=str(FIX / "fake-pi-mediated.sh"),
                                extras=[harness.REMEDIES / "check" / unit])
    assert (run_dir / "workspace" / "mediated.txt").read_text().splitlines()[0].endswith("test_01_one.py")


def test_a_session_without_the_unit_gets_no_mediated_tests(tmp_path, monkeypatch):
    monkeypatch.setenv("MELLUM_MEDIATED_TEST", "/leaked/from/the/driver.py")
    suite = _mediated_suite(tmp_path)
    run_dir = harness.run_suite(suite, runs_dir=tmp_path / "runs", profile=PROFILE,
                                pi_binary=str(FIX / "fake-pi-mediated.sh"))
    assert (run_dir / "workspace" / "mediated.txt").read_text().splitlines() == ["unset", "unset"]


def test_the_unit_needs_the_suites_mediated_tests(tmp_path):
    with pytest.raises(SystemExit, match="mediated"):
        harness.run_suite(harness.load_suite(SUITES, "steps"), runs_dir=tmp_path / "runs", profile=PROFILE,
                          pi_binary=str(FIX / "fake-pi-mediated.sh"), extras=[MEDIATED_UNIT])


# F.6: on a pod a session runs as an unprivileged user, so the checkout (and the hidden grader) stay root's.

def test_a_session_user_env_keeps_only_what_a_session_needs():
    env = harness.session_user_env({"PATH": "/p:/q", "RUNPOD_API_KEY": "secret", "HF_TOKEN": "secret",
                                    "UV_PYTHON_INSTALL_DIR": "/x/python", "VERIFY_PYTEST": "pytest -x"},
                                   home="/home/s", user="s")
    assert env["PATH"] == "/p:/q" and env["HOME"] == "/home/s" and env["USER"] == "s"
    assert env["UV_CACHE_DIR"] == "/home/s/.cache/uv" and env["UV_PYTHON_INSTALL_DIR"] == "/x/python"
    assert env["UV_PYTHON_DOWNLOADS"] == "never" and env["VERIFY_PYTEST"] == "pytest -x"
    assert "RUNPOD_API_KEY" not in env and "HF_TOKEN" not in env


def test_chown_tree_never_follows_a_symlink(tmp_path, monkeypatch):
    (tmp_path / "tree").mkdir()
    (tmp_path / "tree" / "link").symlink_to("/etc/passwd")
    calls = []
    monkeypatch.setattr(harness.os, "chown", lambda path, uid, gid, follow_symlinks=True: calls.append((str(path), follow_symlinks)))
    import pwd
    harness.chown_tree(tmp_path / "tree", pwd.getpwuid(os.getuid()).pw_name)
    assert len(calls) == 2 and all(flag is False for _, flag in calls)


def test_dropping_privileges_clears_root_s_supplementary_groups():
    import pwd
    me = pwd.getpwuid(os.getuid())
    assert harness.drop_privileges(me.pw_name) == {"user": me.pw_name, "group": me.pw_gid, "extra_groups": []}


def test_a_session_users_tree_copies_the_units_and_their_imports(tmp_path):
    run = tmp_path / "run"; run.mkdir()
    unit = harness.REMEDIES / "check" / "mediated-test-settle.ts"
    root, extras, extension = harness.readable_tree(run, [unit], harness.EXTENSION)
    assert extras == [root / "remedies" / "check" / "mediated-test-settle.ts"]
    assert extension == root / "extensions" / harness.EXTENSION.name
    for name in ("remedies/mediated-test.ts", "remedies/task-prompt.ts", "remedies/install.ts",
                 "extensions/mellum-verify.ts", "extensions/bounded.ts", "extensions/mellum-task.ts",
                 "templates/llama-model-settings.json", "package.json"):
        assert (root / name).stat().st_mode & 0o444 == 0o444, name
    assert (root / "remedies").stat().st_mode & 0o555 == 0o555


def test_a_session_users_tree_refuses_a_unit_from_elsewhere(tmp_path):
    outside = tmp_path / "mine.ts"; outside.write_text("")
    with pytest.raises(SystemExit, match="session user"):
        harness.readable_tree(tmp_path, [outside], None)


def test_handed_tests_are_copied_where_a_session_user_can_read_but_not_list(tmp_path):
    source = tmp_path / "test_01_one.py"; source.write_text("x = 1\n")
    source.chmod(0o600)
    place = tmp_path / "handed"
    copied = harness.hand_over([source], place)
    assert copied == [place / "test_01_one.py"] and copied[0].read_text() == "x = 1\n"
    assert copied[0].stat().st_mode & 0o777 == 0o644
    assert place.stat().st_mode & 0o777 == 0o711


def test_the_user_sweep_ends_what_the_user_left(tmp_path, monkeypatch):
    child = subprocess.Popen(["sleep", "30"])
    fake = tmp_path / "ps"
    fake.write_text(f"#!/bin/sh\nif kill -0 {child.pid} 2>/dev/null; then echo '{child.pid} sleep'; fi\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    import threading
    reaper = threading.Thread(target=child.wait); reaper.start()
    assert harness.sweep_user("someone", grace=0.2) == [(child.pid, "sleep")]
    reaper.join(timeout=5)
    assert child.poll() is not None


def test_the_machine_label_names_a_pods_gpu(tmp_path, monkeypatch):
    for name, text in (("sysctl", ""), ("nvidia-smi", "NVIDIA A40-48Q")):
        tool = tmp_path / name
        tool.write_text(f"#!/bin/sh\necho '{text}'\n")
        tool.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    assert harness.machine_label().startswith("NVIDIA A40-48Q")


def test_a_counted_gate_reads_the_pin_card_its_host_card_names(monkeypatch, tmp_path):
    import conformance as conf
    pins = conf.load_pins(conf.POD_PINS)
    card = tmp_path / "card.json"
    card.write_text(json.dumps({"schema": conf.SCHEMA, "passed": True, "pins_digest": conf.pins_digest(pins),
                                "pins_file": "pod-pins.json", "build_info": "b", "model_path": "m", "slots": [1],
                                "server_command": ["x"]}))
    monkeypatch.setattr(conf, "_get", lambda endpoint, route: {"build_info": "b", "model_path": "m"}
                        if route == "/props" else [{"n_ctx": 1}])
    monkeypatch.setattr(conf, "server_command", lambda port: ["x"])
    assert harness.host_gate(card, "http://127.0.0.1:8001", conf.load_pins())["passed"] is True
