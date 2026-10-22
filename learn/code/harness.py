#!/usr/bin/env python3
"""Run one eval suite through base Pi in a fresh directory and score it.

The ladder measures; this teaches. A suite is a project with a mission,
tech stack and roadmap; its hidden graders stay out of the workspace until
the child has exited, and the run lives outside the repo.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

CODE = Path(__file__).resolve().parent
RUNS = Path(tempfile.gettempdir()) / "mellum-eval-runs"
SUITES = CODE / "suites"
RECORDER = CODE / "record-pi.mjs"
PROFILE = CODE / "profile"
EXTENSION = CODE.parents[1] / "extensions" / "mellum-worker.ts"
ARMS = ("bare", "worker", "no-prompt", "no-nudge", "no-loop")
FLAGS = [
    "-p", "--no-approve", "--no-extensions", "--no-skills",
    "--no-prompt-templates", "--no-themes", "--no-context-files",
]


@dataclass(frozen=True)
class Suite:
    name: str
    prompts: list[str]
    tests: Path
    start: Path | None
    expected: tuple[str, ...] = ()
    canary: str | None = None
    root: Path | None = None

    @property
    def prompt(self) -> str:
        return self.prompts[0]


def _read_prompt(path: Path) -> str:
    text = path.read_text().strip()
    if not text:
        raise SystemExit(f"empty prompt: {path}")
    return text


def load_suite(suites_dir: Path, name: str) -> Suite:
    base = Path(suites_dir) / name
    prompts_dir = base / "prompts"
    if prompts_dir.is_dir():
        files = sorted(prompts_dir.glob("*.md"))
        if not files:
            raise SystemExit(f"no prompts in {prompts_dir}")
        prompts = [_read_prompt(path) for path in files]
    else:
        prompts = [_read_prompt(base / "task.md")]
    grader = base / "grader"
    expected = ()
    if (base / "expected.json").is_file():
        expected = tuple(json.loads((base / "expected.json").read_text()))
    canary = None
    if (grader / "canary").is_file():
        canary = (grader / "canary").read_text().strip() or None
    start = base / "start"
    return Suite(
        name=name,
        prompts=prompts,
        tests=grader if grader.is_dir() else base / "tests",
        start=start if start.is_dir() else None,
        expected=expected,
        canary=canary,
        root=base,
    )


def profile_pin(profile_dir: Path) -> tuple[str, str]:
    providers = json.loads((Path(profile_dir) / "models.json").read_text())["providers"]
    provider = next(iter(providers))
    return provider, providers[provider]["models"][0]["id"]


def new_run(runs_dir: Path, name: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run = Path(runs_dir) / f"{stamp}-{name}-{uuid.uuid4().hex[:6]}"
    run.mkdir(parents=True)
    return run


def arm_settings(arm: str) -> dict:
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}; choose from {', '.join(ARMS)}")
    if arm == "bare":
        return {"extension": None, "env": {}}
    env = {"MELLUM_MODE": "1"}
    if arm == "no-prompt":
        env["MELLUM_WORKER_PROMPT"] = "pi"
    elif arm == "no-nudge":
        env["MELLUM_GUARDS"] = json.dumps({"loopBreaker": True})
    elif arm == "no-loop":
        env["MELLUM_GUARDS"] = json.dumps({"emptyFinalNudge": 3})
    return {"extension": EXTENSION, "env": env}


def pi_argv(
    pi_binary: str,
    profile: Path,
    recorder: Path,
    provider: str,
    model: str,
    prompt: str,
    *,
    extension: Path | None = None,
    session_id: str | None = None,
    session_dir: Path | None = None,
) -> list[str]:
    session = (
        ["--session-id", session_id, "--session-dir", str(session_dir)]
        if session_id and session_dir
        else []
    )
    extra = ["-e", str(extension)] if extension is not None else []
    return [
        pi_binary, *FLAGS, "--provider", provider, "--model", model,
        *session, *extra, "-e", str(recorder), prompt,
    ]


def run_suite(
    suite: Suite,
    *,
    runs_dir: Path,
    arm: str = "bare",
    profile: Path = PROFILE,
    pi_binary: str = "pi",
    deadline: float | None = None,
) -> Path:
    run = new_run(runs_dir, suite.name)
    workspace = run / "workspace"
    workspace.mkdir()
    shutil.copytree(profile, run / "profile")
    recorder = run / "record-pi.mjs"
    shutil.copy2(RECORDER, recorder)
    if suite.root is not None and (suite.root / "base").is_dir():
        shutil.copytree(suite.root / "base", workspace, dirs_exist_ok=True)
    if suite.start is not None:
        shutil.copytree(suite.start, workspace, dirs_exist_ok=True)
    (run / "prompt.txt").write_text("\n\n".join(suite.prompts) + "\n")
    trace = run / "trace.jsonl"
    trace.touch()
    sessions = run / "sessions"
    sessions.mkdir()
    provider, model = profile_pin(profile)
    session_id = str(uuid.uuid4())
    settings = arm_settings(arm)
    env = {
        **os.environ,
        "PI_CODING_AGENT_DIR": str(run / "profile"),
        "MELLUM_TRACE_FILE": str(trace),
    }
    for key in ("MELLUM_MODE", "MELLUM_GUARDS", "MELLUM_WORKER_PROMPT"):
        env.pop(key, None)
    env.update(settings["env"])
    started = time.monotonic()
    for prompt in suite.prompts:
        remaining = None if deadline is None else deadline - (time.monotonic() - started)
        if remaining is not None and remaining <= 0:
            (run / "deadline").write_text("hit\n")
            break
        argv = pi_argv(
            pi_binary, run / "profile", recorder, provider, model, prompt,
            extension=settings["extension"],
            session_id=session_id, session_dir=sessions,
        )
        try:
            child = subprocess.Popen(argv, cwd=workspace, env=env,
                                     start_new_session=True)
        except FileNotFoundError:
            raise SystemExit(f"pi not found: {pi_binary}; install Pi before running a suite")
        try:
            child.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            (run / "deadline").write_text("hit\n")
            break
    if grader_touched(run, suite):
        (run / "contaminated").write_text("grader touched\n")
    return run


def grader_touched(run: Path, suite: Suite) -> bool:
    if suite.canary is None:
        return False
    text = (Path(run) / "trace.jsonl").read_text(errors="ignore")
    return suite.canary in text or f"suites/{suite.name}" in text


def grade(workspace: Path) -> list[tuple[str, bool, str]]:
    workspace = Path(workspace)
    (workspace / "pyrefly.toml").write_text(
        'project-includes = [\n    "**/*.py",\n]\n'
        'project-excludes = [\n    "tests/**",\n]\n')
    def tool(name: str, *args: str) -> list[str]:
        if (workspace / "pyproject.toml").is_file():
            return ["uv", "run", "--with", name, name, *args]
        return ["uvx", name, *args]

    commands = (
        ("ruff", tool("ruff", "check", "--select", "F,E9", "--exclude", "tests", "--exclude", "grader_tests", ".")),
        ("pyrefly", tool("pyrefly", "check", ".")),
        ("complexipy", tool("complexipy", "--max-complexity-allowed", "10",
                            "--exclude", "tests", "--exclude", "grader_tests", ".")),
    )
    results = []
    for name, command in commands:
        result = subprocess.run(
            command, cwd=workspace, capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": str(workspace)},
        )
        output = [line for line in (result.stdout + result.stderr).splitlines()
                  if line.strip()]
        results.append((name, result.returncode == 0, output[0] if output else ""))
    return results


def qualify(suite: Suite) -> tuple[bool, dict[str, bool]]:
    if suite.root is None:
        raise SystemExit(f"suite {suite.name} has no root")
    results: dict[str, bool] = {}
    for name in ("known-good", "known-broken"):
        fixture = Path(suite.root) / "fixtures" / name
        if not fixture.is_dir():
            raise SystemExit(f"missing fixture: {fixture}")
        workspace = Path(tempfile.mkdtemp(prefix=f"mellum-{suite.name}-{name}-"))
        try:
            shutil.copytree(Path(suite.root) / "base", workspace, dirs_exist_ok=True)
            shutil.copytree(fixture, workspace, dirs_exist_ok=True)
            passed, _ = score_workspace(workspace, suite)
            results[name] = passed
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
    return results["known-good"] and not results["known-broken"], results


def _trace_time(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def report(run: Path) -> dict:
    rows = [
        json.loads(line)
        for line in (Path(run) / "trace.jsonl").read_text().splitlines()
        if line.strip()
    ]
    final = ""
    inputs = []
    outputs = []
    times = []
    for row in rows:
        if (when := _trace_time(row.get("timestamp"))) is not None:
            times.append(when)
        if row.get("type") != "message_end":
            continue
        message = row.get("message") or {}
        usage = message.get("usage") or {}
        value = usage.get("input", usage.get("prompt_tokens"))
        if isinstance(value, (int, float)):
            inputs.append(value)
        value = usage.get("output", usage.get("completion_tokens"))
        if isinstance(value, (int, float)):
            outputs.append(value)
        if message.get("role") != "assistant":
            continue
        for block in message.get("content") or []:
            if block.get("type") == "text" and block.get("text"):
                final = block["text"]
                break
    return {
        "requests": sum(row.get("type") == "provider_request" for row in rows),
        "turns": sum(row.get("type") == "provider_request" for row in rows),
        "tool_calls": sum(row.get("type") == "tool_call" for row in rows),
        "tool_errors": sum(
            row.get("type") == "tool_result" and row.get("isError") for row in rows),
        "final_reply": final,
        "context": max(inputs) if inputs else None,
        "output_tokens": sum(outputs) if outputs else None,
        "wall": round((times[-1] - times[0]).total_seconds(), 3) if len(times) > 1 else None,
    }


def score(run: Path, suite: Suite) -> tuple[bool, str]:
    return score_workspace(Path(run) / "workspace", suite)


def score_details(run: Path, suite: Suite) -> tuple[bool, str, int]:
    return score_workspace_details(Path(run) / "workspace", suite)


def score_workspace_details(workspace: Path, suite: Suite) -> tuple[bool, str, int]:
    workspace = Path(workspace)
    target = workspace / "grader_tests"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(suite.tests, target)
    command = (
        ["uv", "run", "--with", "pytest", "pytest", "-q", "-rA", "grader_tests"]
        if (workspace / "pyproject.toml").is_file()
        else ["uvx", "pytest", "-q", "-rA", "grader_tests"]
    )
    result = subprocess.run(
        command, cwd=workspace, capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONPATH": str(workspace)},
    )
    output = (result.stdout + result.stderr).strip()
    missing = [test for test in suite.expected if f"PASSED {test}" not in output]
    lines = output.splitlines()[-20:]
    if missing:
        lines.append("missing expected tests: " + ", ".join(missing))
    return result.returncode == 0 and not missing, "\n".join(lines), len(missing)


def score_workspace(workspace: Path, suite: Suite) -> tuple[bool, str]:
    passed, tail, _ = score_workspace_details(workspace, suite)
    return passed, tail


def _run_sessions(
    suite: Suite,
    *,
    runs_dir: Path,
    pi_binary: str,
    repeat: int,
    grade_run: bool,
    deadline: float | None,
    arm: str = "bare",
) -> list[tuple]:
    results = []
    for _ in range(repeat):
        run_dir = run_suite(suite, runs_dir=runs_dir, pi_binary=pi_binary,
                            deadline=deadline, arm=arm)
        grades = grade(run_dir / "workspace") if grade_run else []
        tests_passed, tail, failed_checks = score_details(run_dir, suite)
        quality_ok = all(
            ok for name, ok, _ in grades if name in {"ruff", "complexipy"}
        ) if grades else True
        contaminated = (run_dir / "contaminated").exists()
        passed = tests_passed and quality_ok and not contaminated
        metrics = report(run_dir)
        record = {
            "suite": suite.name,
            "arm": arm,
            "passed": passed,
            "tests_passed": tests_passed,
            "quality_ok": quality_ok,
            "contaminated": contaminated,
            "failed_checks": failed_checks,
            **{key: value for key, value in metrics.items()
               if key != "final_reply"},
        }
        (run_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n")
        results.append((run_dir, passed, tail, grades, metrics,
                        tests_passed, quality_ok, contaminated))
    return results


def _print_task(
    suite: Suite, results: list[tuple], repeat: int
) -> int:
    for index, (run_dir, passed, tail, grades, counts, tests_passed,
                quality_ok, contaminated) in enumerate(results, 1):
        print(_line(suite, run_dir, passed, counts, repeat, index,
                    tests_passed, quality_ok, contaminated))
        _print_grades(grades)
        if not passed:
            print(tail, file=sys.stderr)
    ok = sum(1 for result in results if result[1])
    if repeat > 1:
        print(f"{suite.name}: {ok}/{repeat} sessions passed")
    return ok


def run_suites(
    names: list[str],
    *,
    suites_dir: Path = SUITES,
    runs_dir: Path = RUNS,
    pi_binary: str = "pi",
    grade_run: bool = False,
    repeat: int = 1,
    deadline: float | None = 600,
    arm: str = "bare",
) -> tuple[int, int]:
    available = sorted(
        path.name for path in Path(suites_dir).iterdir()
        if ((path / "grader").is_dir() or (path / "tests").is_dir())
        and ((path / "task.md").exists() or (path / "prompts").is_dir())
    )
    if "all" in names:
        names = available
    missing = [name for name in names if name not in available]
    if missing:
        raise SystemExit(f"no suite named {', '.join(missing)} in {suites_dir}; "
                         f"available: {', '.join(available)}")
    suites_passed = sessions_passed = sessions_total = 0
    for name in names:
        suite = load_suite(suites_dir, name)
        results = _run_sessions(
            suite, runs_dir=runs_dir, pi_binary=pi_binary,
            repeat=repeat, grade_run=grade_run, deadline=deadline, arm=arm,
        )
        sessions_passed += _print_task(suite, results, repeat)
        sessions_total += len(results)
        if all(result[1] for result in results):
            suites_passed += 1
    print(f"{suites_passed}/{len(names)} suites passed "
          f"({sessions_passed}/{sessions_total} sessions)")
    return suites_passed, len(names)


def _line(
    suite: Suite,
    run_dir: Path,
    passed: bool,
    counts: dict,
    repeat: int = 1,
    index: int = 1,
    tests_passed: bool = True,
    quality_ok: bool = True,
    contaminated: bool = False,
) -> str:
    tag = suite.name + (f" [{index}/{repeat}]" if repeat > 1 else "")
    n_text = f"n={repeat}; " if repeat == 1 else ""
    deadline = " deadline" if (Path(run_dir) / "deadline").exists() else ""
    label = "CONTAMINATED" if contaminated else ("PASS" if passed else "FAIL")
    notes = []
    if not quality_ok:
        notes.append("quality FAIL")
    if contaminated:
        notes.append("grader touched")
    note = ("; " + ", ".join(notes)) if notes else ""
    return (f"{tag}: {label} ({n_text}run {run_dir}; "
            f"{counts['requests']} requests, {counts['tool_calls']} tool calls, "
            f"{counts['tool_errors']} tool errors{deadline}{note})")


def _print_grades(grades: list[tuple[str, bool, str]]) -> None:
    for name, ok, detail in grades:
        label = "pyrefly (advisory)" if name == "pyrefly" else name
        print(f"{label}: {'PASS' if ok else 'FAIL'}" + (f" ({detail})" if not ok else ""))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one eval suite or all of them")
    qualify_p = sub.add_parser("qualify", help="prove a suite's grader both ways")
    qualify_p.add_argument("--suite", required=True)
    qualify_p.add_argument("--suites-dir", type=Path, default=SUITES)
    run.add_argument("--suite", required=True, help="a suite name, or all")
    run.add_argument("--suites-dir", type=Path, default=SUITES)
    run.add_argument("--runs-dir", type=Path, default=RUNS)
    run.add_argument("--pi-binary", default="pi")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--grade", action="store_true")
    run.add_argument("--repeat", type=int, default=1)
    run.add_argument("--deadline", type=float, default=600)
    run.add_argument("--arm", choices=ARMS, default="bare")
    args = parser.parse_args(argv)

    if args.command == "qualify":
        suite = load_suite(args.suites_dir, args.suite)
        ok, results = qualify(suite)
        for name, passed in results.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
        print(f"{suite.name}: {'QUALIFIED' if ok else 'NOT QUALIFIED'}")
        return 0 if ok else 1

    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    if args.suite == "all":
        run_suites(["all"], suites_dir=args.suites_dir, runs_dir=args.runs_dir,
                   pi_binary=args.pi_binary, grade_run=args.grade,
                   repeat=args.repeat, deadline=args.deadline, arm=args.arm)
        return 0

    suite = load_suite(args.suites_dir, args.suite)
    provider, model = profile_pin(PROFILE)
    if args.dry_run:
        settings = arm_settings(args.arm)
        print(shlex.join(pi_argv(args.pi_binary, PROFILE, RECORDER, provider,
                                 model, suite.prompt,
                                 extension=settings["extension"])))
        return 0
    results = _run_sessions(
        suite, runs_dir=args.runs_dir, pi_binary=args.pi_binary,
        repeat=args.repeat, grade_run=args.grade, deadline=args.deadline,
        arm=args.arm,
    )
    _print_task(suite, results, args.repeat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
