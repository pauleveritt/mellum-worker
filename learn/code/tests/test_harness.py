import json
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
        "wall": 2.0,
    }


def test_report_without_text(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    _write_trace(run_dir, [{"type": "instance_start"}])
    assert harness.report(run_dir) == {
        "requests": 0, "turns": 0, "tool_calls": 0, "tool_errors": 0,
        "final_reply": "", "context": None, "output_tokens": None, "wall": None,
    }


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
    passed, tail, failed = harness.score_workspace_details(workspace, suite)
    assert not passed
    assert failed == 1
    assert "test_add" in tail


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
    assert record["turns"] == 0
    assert record["context"] is None
    assert record["wall"] is None


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
