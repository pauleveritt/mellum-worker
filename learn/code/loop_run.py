#!/usr/bin/env python3
"""Variable-extension workflow loop runner (two review gates).

Each workflow is its own `pi` invocation over one shared workspace, with its own
minimal extension set and thinking budget. The orchestrator is the plan/verify
control, so those gates are not loaded as extensions.

    planning    -> write TODO.md (every task requirement).   ext: none     think: low
    plan_review -> is the plan the SIMPLEST that meets the    ext: none     think: low
                   task? too complicated -> back to planning.
    coding      -> follow TODO.md, implement.                 ext: guards   think: high
    code_review -> conformance + simplicity vs the spec;      ext: none     think: low
                   unmet/over-complex -> back to coding.
    testing     -> run the suite (orchestrator).              (no pi)
    rubberduck  -> on a REPEATED broken test: reason it out,  ext: none     think: high
                   amend TODO.md, then back to coding.

Reviews end with `REVIEW: PASS` or `REVIEW: REDO`, read from the review's trace.

    python3 loop_run.py --suite easy,medium --max-rounds 4
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

EXT = Path(__file__).resolve().parents[2] / "extensions"
# Each workflow runs with only the tools its job needs (pi --tools allowlist). Reviewers
# READ and judge — no bash, no write, no edit — so they can't wander off running the app
# or editing files; think/planning/rubberduck additionally write their one markdown file;
# only CODING gets the full executor set (bash to run pytest, write/edit to implement).
READ_ONLY = "read,grep,find,ls"
# Only CODING may write files. think/planning/rubberduck are read-only: they PRODUCE TEXT
# and the orchestrator saves it as the artifact (THINKING.md / TODO.md). This stops a weak
# model from using a `write` tool to build the whole app during the "think" stage — which
# collapses the think -> plan -> code pipeline into "think does everything".
WORKFLOW_TOOLS = {
    "think": READ_ONLY,
    "planning": READ_ONLY,
    "plan_review": READ_ONLY,
    "coding": f"{READ_ONLY},write,edit,bash",
    "code_review": READ_ONLY,
    "rubberduck": READ_ONLY,
}
# mellum-nonblock is loaded only on CODING — the one workflow with bash. A server start
# (uvicorn, app.py, flask run …) would block forever and hang the stage until the
# wf-timeout; the extension rewrites it to run threaded in the background and feeds its
# output back. run_pi reaps the process group when the stage ends, so nothing leaks.
NONBLOCK = EXT / "mellum-nonblock.ts"
WORKFLOW_EXT = {
    "think": [],
    "planning": [],
    "plan_review": [],
    "coding": [NONBLOCK, EXT / "mellum-guards.ts", EXT / "mellum-surgical.ts"],
    "code_review": [],
    "rubberduck": [],
}
WORKFLOW_THINK = {
    # Step 1 is think (reason, on) -> write plan (transcribe, off) -> review plan (judge, on).
    # Separating thinking from writing fixes fidelity: think gets the exact strings right in
    # THINKING.md; planning only transcribes. Coding (executor) thinks a little; reviews/duck hard.
    "think": "high", "planning": "off", "coding": "low",
    "plan_review": "high", "code_review": "high", "rubberduck": "high",
}
SYS = {
    "think": (
        "You are THINKING through the task — do NOT write code or TODO.md. Read specs/ and the TASK "
        "below (specs/roadmap.md lists ALL phases; consider ONLY the phase(s) the task names). Reason "
        "about: the overall goal (one-sentence north star), every requirement of those phase(s) with "
        "EXACT strings, keys and status codes copied verbatim from the spec, and the SIMPLEST way to "
        "meet them. Write your analysis to THINKING.md, BEGINNING with the exact line `## North Star` "
        "(two hashes) followed by the one-sentence goal, then the exact requirements and the approach. "
        "This is the reasoning; the plan is transcribed from it next."
    ),
    "planning": (
        "You are the PLAN WRITER — do NOT reason or add anything new, only transcribe. Read "
        "THINKING.md. Write TODO.md: BEGIN with the `## North Star` line copied EXACTLY from "
        "THINKING.md, then a checklist (`- [ ]`) of every requirement in THINKING.md, copying exact "
        "strings, keys and status codes verbatim. Do NOT write code. If TODO.md exists, update it "
        "from THINKING.md and the note below. End when TODO.md is written."
    ),
    "plan_review": (
        "You are the PLAN REVIEWER — you only READ and judge; you cannot change files. Read specs/ "
        "and TODO.md. Check the plan (a) has a North Star near the top stating the task's goal that "
        "every step serves (judge the SUBSTANCE — do NOT REDO over the heading level, `#` vs `##`, or "
        "any other formatting), (b) is complete for the TASK's phase(s), and (c) is the SIMPLEST that "
        "meets them — no over-engineering, speculative items, or steps the task does not need. "
        "If the goal is missing, or the plan is over-complicated or wrong, end with exactly "
        "`REVIEW: REDO` and state plainly what to simplify or fix — the plan writer will revise it. "
        "If it is already simple, complete and anchored, end with exactly `REVIEW: PASS`."
    ),
    "coding": (
        "You are the CODER. Read TODO.md and specs/. Implement each unchecked `- [ ]` item, in "
        "order; check it off (`- [x]`) once done. Run the tests with `uv run --with pytest pytest -q` "
        "(set PYTHONPATH to the project root so `from app import ...` resolves); never start a server "
        "— use starlette.testclient.TestClient. Make every test pass."
    ),
    "code_review": (
        "You are the CODE REVIEWER — you only READ and judge; you cannot change files. Read specs/ "
        "and the code. Two checks: (1) CONFORMANCE — every requirement of the TASK's phase(s) is "
        "actually implemented, including ones no visible test checks (exact keys, status codes, "
        "fields, migrations); (2) SIMPLICITY — the code is the simplest that meets the spec (flag "
        "over-engineering, unused code, needless layers). End with exactly `REVIEW: REDO` if anything "
        "is unmet or over-complex — list each item plainly so the coder can fix it — else `REVIEW: PASS`."
    ),
    "rubberduck": (
        "You are RUBBER-DUCKING a stuck problem — do NOT write code. The tests keep failing (below). "
        "Explain step by step what the failing test expects, what the code does, and where the "
        "mismatch is; reason out the root cause. Then update TODO.md with concrete steps to fix it."
    ),
}
# Run the worker's tests in the PROJECT venv (so the app's deps — starlette, fastapi —
# are importable) plus pytest, the same reliable way the hidden grader runs.
PYTEST = ["uv", "run", "--with", "pytest", "pytest", "-q", "tests"]


_FEED_PATH: Path | None = None


def emit(msg: str) -> None:
    """Print to the terminal AND append to the run bundle's feed.log."""
    print(msg, flush=True)
    if _FEED_PATH is not None:
        with open(_FEED_PATH, "a") as fh:
            fh.write(msg + "\n")


def fmt_event(row: dict) -> str | None:
    """One trace row -> one feed line (tool call, result, or assistant text), or None."""
    t = row.get("type")
    if t == "tool_call":
        i = row.get("input") or {}
        p = i.get("path") or i.get("file_path") or (i.get("command", "")[:60] if i.get("command") else "")
        return f"  → {row.get('toolName', ''):6} {str(p)[:70]}"
    if t == "tool_result":
        c = row.get("content") or []
        txt = (c[0].get("text", "") if c and isinstance(c[0], dict) else str(c)).strip().replace("\n", " ")
        return f"    {'ERR ' if row.get('isError') else 'ok  '}{txt[:76]}" if txt else None
    if t == "message_end":
        m = row.get("message") or {}
        if m.get("role") == "assistant":
            for b in m.get("content") or []:
                if b.get("type") == "text" and (b.get("text") or "").strip():
                    return "  \U0001f4ac " + b["text"].strip().replace("\n", " ")[:160]
    return None


def stream_trace(trace: Path, prefix: str, stop: threading.Event) -> None:
    """Follow a workflow's trace while pi runs, printing the LLM feed to stdout."""
    seen = 0
    while not stop.is_set():
        if trace.exists():
            lines = trace.read_text(errors="ignore").splitlines()
            for line in lines[seen:]:
                try:
                    out = fmt_event(json.loads(line))
                except ValueError:
                    out = None
                if out:
                    emit(f"{prefix}{out}")
            seen = len(lines)
        time.sleep(0.5)


def run_pi(workflow: str, task: str, *, workspace: Path, profile: Path, recorder: Path,
           provider: str, model: str, trace: Path, timeout: float) -> None:
    ext_flags: list[str] = []
    for e in WORKFLOW_EXT[workflow]:
        ext_flags += ["-e", str(e)]
    tool_flags = ["--tools", WORKFLOW_TOOLS[workflow]] if workflow in WORKFLOW_TOOLS else []
    argv = [
        "pi", *harness.FLAGS, "--provider", provider, "--model", model,
        "--thinking", WORKFLOW_THINK.get(workflow, "medium"), "--no-session",
        *tool_flags, *ext_flags, "-e", str(recorder), "--system-prompt", SYS[workflow], task,
    ]
    env = {**os.environ, "PI_CODING_AGENT_DIR": str(profile), "MELLUM_TRACE_FILE": str(trace)}
    emit(f"\n━━━ {workflow} (think={WORKFLOW_THINK.get(workflow, 'medium')}) ━━━")
    stop = threading.Event()
    feed = threading.Thread(target=stream_trace, args=(trace, f"[{workflow}]", stop), daemon=True)
    feed.start()
    child = subprocess.Popen(argv, cwd=workspace, env=env, start_new_session=True)
    try:
        child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
    finally:
        stop.set()
        feed.join(timeout=2)
        # Reap any backgrounded children (e.g. a server mellum-nonblock threaded)
        # so nothing leaks past this stage. child is the process-group leader.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def final_text(trace: Path) -> str:
    final = ""
    if not trace.exists():
        return final
    for line in trace.read_text(errors="ignore").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("type") == "message_end":
            message = row.get("message") or {}
            if message.get("role") == "assistant":
                for block in message.get("content") or []:
                    if block.get("type") == "text" and block.get("text"):
                        final = block["text"]
    return final


def verdict(trace: Path) -> str:
    """A review passes only if it explicitly ends with REVIEW: PASS."""
    return "PASS" if "REVIEW: PASS" in final_text(trace) else "REDO"


def reviewer_reason(trace: Path) -> str:
    """The reviewer's verdict text (REVIEW: REDO + why), for the next stage. Never empty."""
    text = final_text(trace).strip()
    return text or "(no reason given) — simplify, and make sure every requirement of the task is met."


def handoff(reason: str) -> str:
    """Frame a reviewer's reasons as a clear, unmissable instruction for the next stage."""
    return (
        "=== REVIEWER FEEDBACK — you MUST address every point below ===\n"
        f"{reason}\n"
        "=== end reviewer feedback ==="
    )


def run_tests(workspace: Path, timeout: float) -> tuple[bool, str]:
    # Mirror the hidden grader (harness.score_workspace_details): put the workspace
    # root on PYTHONPATH so `from app import app` resolves. Without this the visible
    # gate FALSE-FAILs a correct solution on an import error the grader never hits.
    env = {**os.environ, "PYTHONPATH": str(workspace)}
    try:
        proc = subprocess.run(PYTEST, cwd=workspace, capture_output=True, text=True,
                              timeout=timeout, check=False, env=env)
    except subprocess.TimeoutExpired:
        return False, "tests timed out"
    out = proc.stdout + proc.stderr
    return proc.returncode == 0, "\n".join(out.splitlines()[-25:])


def pin_profile(profile_dir: Path, base_url: str, model_id: str, context_window: int = 56000,
                thinking_format: str | None = None) -> None:
    mp = profile_dir / "models.json"
    data = json.loads(mp.read_text())
    _, prov = next(iter(data["providers"].items()))
    prov["baseUrl"] = base_url
    model = prov["models"][0]
    model["id"] = model_id
    # A smaller window reserves less KV per request, so best-of-N (--concurrency N) fits under the
    # oMLX memory guard — each concurrent request costs model + KV(window), and the guard rejects
    # the overflow. Keep it above the largest context a phase actually reaches or it truncates.
    model["contextWindow"] = context_window
    if thinking_format is not None:
        # The pinned model carries Mellum's thinking format (qwen-chat-template). A different
        # model served by vLLM (e.g. gemma) keeps reasoning AND tool calling, but needs its own
        # format or pi's injected thinking leaks as garbage tokens. Override just the format;
        # reasoning stays on. "chat-template" defers thinking to the model's own chat template.
        model.setdefault("compat", {})["thinkingFormat"] = thinking_format
    mp.write_text(json.dumps(data, indent=2) + "\n")


def loop(suite_name: str, *, runs_dir: Path, max_rounds: int, wf_timeout: float, duck_after: int,
         base_url: str, model_id: str) -> dict:
    global _FEED_PATH
    suite = harness.load_suite(harness.SUITES, suite_name)
    run = harness.new_run(runs_dir, f"loop-{suite_name}")
    workspace = run / "workspace"
    workspace.mkdir()
    _FEED_PATH = run / "feed.log"          # the live feed is also saved into the bundle
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    verdicts: list[dict] = []
    if suite.root is not None and (suite.root / "base").is_dir():
        shutil.copytree(suite.root / "base", workspace, dirs_exist_ok=True)
    shutil.copytree(harness.PROFILE, run / "profile")
    pin_profile(run / "profile", base_url, model_id)
    recorder = run / "record-pi.mjs"
    shutil.copy2(harness.RECORDER, recorder)
    provider, model = harness.profile_pin(run / "profile")
    task = "\n\n".join(suite.prompts)

    def pi(workflow: str, extra: str, tag: str) -> Path:
        trace = run / f"trace-{tag}.jsonl"
        run_pi(workflow, (task if not extra else f"{task}\n\n{extra}"),
               workspace=workspace, profile=run / "profile", recorder=recorder,
               provider=provider, model=model, trace=trace, timeout=wf_timeout)
        return trace

    round_ = 0
    passed = False
    note = ""
    # 1) Think (reason, on) -> write plan (transcribe, off) -> plan_review (judge, on),
    #    re-writing the plan while it is over-complicated.
    pi("think", "", "think")
    pi("planning", "", "0-plan")
    while True:
        planrev = pi("plan_review", "", f"{round_}-planrev")
        if verdict(planrev) == "PASS":
            break
        if round_ >= max_rounds:
            break
        round_ += 1
        # Pass the reviewer's ACTUAL reasons to the writer so it fixes the right thing.
        reason = reviewer_reason(planrev)
        emit(f"  plan_review REDO -> replan; feedback passed: {reason.splitlines()[-1][:120]}")
        pi("planning", handoff(reason) + "\n\nRewrite TODO.md so every point above is resolved.",
           f"{round_}-plan")
    # 2) Iterate the code: coding -> code_review -> testing, back to coding on failure.
    while round_ <= max_rounds:
        pi("coding", (handoff(note) if note else ""), f"{round_}-code")
        coderev = pi("code_review", "", f"{round_}-coderev")
        if verdict(coderev) != "PASS":
            reason = reviewer_reason(coderev)
            note = reason
            emit(f"  round {round_}: code_review REDO -> recode; feedback passed: {reason.splitlines()[-1][:120]}")
            verdicts.append({"round": round_, "code_review": "REDO", "tests": None})
            round_ += 1
            continue
        passed, tail = run_tests(workspace, wf_timeout)
        emit(f"  round {round_}: code_review PASS, tests {'PASS' if passed else 'FAIL'}")
        verdicts.append({"round": round_, "code_review": "PASS", "tests": "PASS" if passed else "FAIL"})
        if passed or round_ >= max_rounds:
            break
        round_ += 1
        note = f"The tests still fail. Pytest output:\n{tail}"
        if round_ > duck_after:
            # Rubber-duck reasons the failure out and amends TODO.md; the coder then reads both.
            pi("rubberduck", f"--- the tests keep failing: ---\n{tail}", f"{round_}-duck")
            note = note + "\n\nThe rubber-duck step just updated TODO.md — follow its new steps."

    graded, _ = harness.score_workspace(workspace, suite)
    todo = (workspace / "TODO.md").exists()
    result = {
        "suite": suite_name,
        "visible": passed,
        "graded": graded,
        "rounds": round_ + 1,
        "todo": todo,
        "model": model_id,
        "base_url": base_url,
        "max_rounds": max_rounds,
        "duck_after": duck_after,
        "started": started,
        "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdicts": verdicts,
    }
    # Save the run bundle's result summary alongside its feed.log, traces and workspace.
    (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    emit(f"{suite_name}: visible={'PASS' if passed else 'FAIL'} hidden-grader={'PASS' if graded else 'FAIL'} "
         f"rounds={round_ + 1} TODO.md={'yes' if todo else 'NO'} bundle={run}")
    _FEED_PATH = None
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--suite", required=True, help="a suite name, or comma-separated names")
    p.add_argument("--max-rounds", type=int, default=4)
    p.add_argument("--duck-after", type=int, default=1)
    p.add_argument("--wf-timeout", type=float, default=400.0)
    p.add_argument("--runs-dir", type=Path, default=harness.RUNS / "loop")
    p.add_argument("--base-url", default="http://127.0.0.1:8001/v1")
    p.add_argument("--model", default="Mellum2.1-12B-A2.5B-Thinking-6bit")
    args = p.parse_args(argv)
    for name in args.suite.split(","):
        loop(name.strip(), runs_dir=args.runs_dir, max_rounds=args.max_rounds,
             wf_timeout=args.wf_timeout, duck_after=args.duck_after,
             base_url=args.base_url, model_id=args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
