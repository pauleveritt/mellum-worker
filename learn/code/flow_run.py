#!/usr/bin/env python3
"""Tool-based workflow runner: ONE `pi` per task; the model orchestrates the phases.

The phases are tools (plan / review_plan / code / review_code / test) registered by
the `mellum-flow` extension; the top agent calls them, driven by the workflow prompt
below. This replaces the external per-phase loop — a capable model orchestrates itself
when the harness offers well-shaped phase tools.

    python3 flow_run.py --suite easy,medium
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
import loop_run as lr  # reuse pin_profile, fmt_event, stream_trace, emit, scoring  # noqa: E402
from memory import Memory, distill as memory_distill  # portable learned grounding (free mode)  # noqa: E402

EXT = Path(__file__).resolve().parents[2] / "extensions"
FLOW = EXT / "mellum-flow.ts"
# The top agent gets ONLY the phase tools (+ read to peek). It orchestrates by calling them.
TOP_TOOLS = "plan,review_plan,examine,code,review_code,test,read"
WORKFLOW = (
    "The task for this phase is in the file TASK.md. You COORDINATE building it by CALLING TOOLS. "
    "CRITICAL: every tool takes NO arguments — call them exactly as `plan()`, `review_plan()`, "
    "`code()`, `review_code()`, `test()`. NEVER pass the task text (or any long text) as an "
    "argument; the tools read TASK.md, TODO.md and REVIEW.md themselves. Passing long arguments "
    "breaks the tool call.\n\n"
    "  plan()        — reads TASK.md, writes TODO.md (a `## North Star` goal + a checklist).\n"
    "  review_plan() — judges the plan; returns REVIEW: PASS or REVIEW: REDO.\n"
    "  examine()     — writes the acceptance test (the definition of DONE) from the spec.\n"
    "  code()        — implements to PASS the acceptance test (reads REVIEW.md for feedback).\n"
    "  review_code() — judges the code; returns REVIEW: PASS or REVIEW: REDO.\n"
    "  test()        — runs the acceptance test; returns TESTS: PASS or TESTS: FAIL.\n\n"
    "Your VERY FIRST action is to call `plan()` — no arguments. Do not reply with prose.\n\n"
    "TERMINATION — overrides everything: `test` is the ONLY exit. The MOMENT test returns "
    "`TESTS: PASS`, you are DONE — stop and call NO further tool.\n\n"
    "Workflow:\n"
    "  1. plan()\n"
    "  2. review_plan(). On REDO, call plan() again (it re-reads the feedback); repeat until PASS.\n"
    "  3. examine()  — write the acceptance test from the spec, BEFORE any coding.\n"
    "  4. code()\n"
    "  5. review_code(). On REDO, call code() again; repeat until PASS.\n"
    "  6. test(). On TESTS: PASS, STOP. On TESTS: FAIL, call code() again then test() again; "
    "repeat until it passes.\n"
    "Always plan, then examine, then code. Never call a tool after a passing test."
)

# --- FREE arm --------------------------------------------------------------------------------
# The harness enforces only two invariants (a frozen external acceptance test before any build,
# and a verified exit) and lets the agent decide every step between them. The examine-only pass
# freezes the gate; the free coder then solves with ordinary tools and the harness — not the
# agent — decides "done" by re-running that gate. See docs/superpowers/research/
# 2026-10-25-agent-decided-flow.md.
EXAMINE_ONLY_TOOLS = "examine,read"
EXAMINE_MSG = (
    "Write the acceptance test for THIS phase — the executable definition of DONE — by calling "
    "`examine()` with NO arguments. It reads the spec in plan/TASK.md itself. Call `examine()` now, "
    "once; when it reports the gate is written, STOP and call no further tool."
)
# The free coder gets ordinary coding tools — NO phase tools, no forced step order. It runs pytest
# itself through `bash` (`uv run python -m pytest -q tests/`). The frozen gate is already under
# tests/; the coder reads it as the definition of DONE and cannot weaken it (the harness restores
# the canonical frozen copy before the authoritative gate run, whatever the coder did to tests/).
FREE_CODER_TOOLS = "read,edit,write,bash,ls,find,grep,lookup"
FREE_WORKFLOW = (
    "You are a coding agent. Your task for this phase is in plan/TASK.md; read it first, and read "
    "specs/ for detail. The acceptance test — the definition of DONE — is ALREADY written under "
    "tests/ as `test_gate_phase_*.py`; read the newest one to see EXACTLY what this phase requires. "
    "You decide how to build it: plan in your head, read the existing app (app.py, models.py, "
    "templates/, tests/), edit or write files, and run the gate yourself with "
    "`uv run python -m pytest -q tests/` until it passes. Keep every earlier gate passing — build "
    "on the existing app, do not rewrite what already works. When you read from data that ALREADY "
    "EXISTS (a table the feature reports 'from'), FIRST inspect its real columns and rows "
    "(`PRAGMA table_info`, a `SELECT`) and use the columns that are actually there — never invent a "
    "column or assume a name the data does not use. Do NOT edit, weaken or delete the "
    "`test_gate_phase_*.py` files — they are the gate you must pass, not change. Stop when the gate "
    "passes."
)


def tail_feed(path: Path, stop: threading.Event) -> None:
    """Tail the sub-agent feed file the extension appends to, printing each new line."""
    seen = 0
    while not stop.is_set():
        if path.exists():
            lines = path.read_text(errors="ignore").splitlines()
            for line in lines[seen:]:
                lr.emit(line)
            seen = len(lines)
        time.sleep(0.4)


def reap_group(pid: int) -> None:
    """SIGKILL a child's process group, ignoring the cases where there is nothing to kill.
    ProcessLookupError: the group already exited. PermissionError (EPERM): the child exited
    and its pid was recycled into a group we do not own — killing it is neither possible nor
    ours to do. Both are safe to ignore; letting EPERM escape crashed a whole best-of-N run."""
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def run_top(task: str, *, workspace: Path, profile: Path, recorder: Path, provider: str,
            model: str, trace: Path, timeout: float, thinking: str, phase: int = 1,
            tools: str = TOP_TOOLS, system_prompt: str = WORKFLOW, load_flow: bool = True,
            label: str = "orchestrator") -> None:
    """Spawn ONE pi over the workspace. Defaults drive the FORCED flow (the phase tools + the
    workflow prompt, FLOW loaded). The FREE arm reuses the same shipped spawn path with a different
    tool set and prompt (`load_flow=False` for the free coder, which gets ordinary coding tools and
    no phase tools; `load_flow=True` for the examine-only pass, which needs the examine tool)."""
    subfeed = trace.parent / f"{trace.stem}.subfeed"
    subfeed.write_text("")
    argv = [
        "pi", *harness.FLAGS, "--provider", provider, "--model", model,
        "--thinking", thinking, "--no-session",
        "--tools", tools,
        "-e", str(harness.THINK_TAGS), *(["-e", str(FLOW)] if load_flow else []), "-e", str(recorder),
        "--system-prompt", system_prompt, task,
    ]
    # MELLUM_PHASE tells the examiner which phase it is writing for, so each phase's
    # acceptance test is frozen under its own name and the gate ACCUMULATES — a later
    # phase can never pass by regressing an earlier one.
    env = {**os.environ, "PI_CODING_AGENT_DIR": str(profile), "MELLUM_TRACE_FILE": str(trace),
           "MELLUM_FLOW_FEED": str(subfeed), "MELLUM_PHASE": str(phase)}
    lr.emit(f"\n━━━ {label} (think={thinking}) ━━━")
    stop = threading.Event()
    feed = threading.Thread(target=lr.stream_trace, args=(trace, "[flow]", stop), daemon=True)
    feed.start()
    subf = threading.Thread(target=tail_feed, args=(subfeed, stop), daemon=True)
    subf.start()
    # No stdin: Pi with -p appends piped stdin to its prompt.
    child = subprocess.Popen(argv, cwd=workspace, env=env, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        reap_group(child.pid)
        child.wait()
    finally:
        stop.set()
        feed.join(timeout=2)
        subf.join(timeout=2)
        reap_group(child.pid)  # reap any phase sub-agents


# A phase with at least this many top-level requirement bullets is "dense" and gets
# decomposed into one sub-phase per requirement. The measured wall is a throughput
# ceiling: the fixed model completes the salient requirement of a dense phase and drops
# the rest, even under best-of-N, feedback, and higher precision. Splitting a dense phase
# so each sub-phase carries ONE requirement (plus the phase's shared context) lowers the
# per-step load to what the model clears reliably; the loop already gates, materializes
# cumulatively, and checkpoints per phase, so N smaller phases "just work". Agnostic: the
# split is on the spec's own enumerated bullets, never on the hidden grader.
SUBDIVIDE_THRESHOLD = 5

_BULLET = re.compile(r"^(?:[-*]\s|\d+\.\s)")


def _heading_split(task: str) -> list[str]:
    """Split on the structure the text already has — Phase/Step headers at ANY level first
    (so `# Phase 5` groups with `## Phase 1`), then any markdown header. No structure → one
    unit (model-splitting an unstructured wall is the parked backlog item)."""
    for pat in (r"(?m)^(?=#{1,6}\s*(?:Phase|Step)\b)", r"(?m)^(?=#{1,6}\s+\S)"):
        parts = [p.strip() for p in re.split(pat, task) if p.strip()]
        if len(parts) > 1:
            return parts
    return [task]


def _requirements(slice_text: str) -> tuple[list[str], list[str]]:
    """Split a phase slice into its lead (heading + any intro prose) and its ordered
    top-level requirement bullets (each with its own nested sub-bullets attached)."""
    lead: list[str] = []
    reqs: list[str] = []
    cur: list[str] | None = None
    for ln in slice_text.splitlines():
        if _BULLET.match(ln):  # a new top-level requirement (column 0, not indented)
            if cur is not None:
                reqs.append("\n".join(cur))
            cur = [ln]
        elif cur is None:
            lead.append(ln)
        else:
            cur.append(ln)  # continuation / nested detail of the current requirement
    if cur is not None:
        reqs.append("\n".join(cur))
    return lead, reqs


def subdivide(slice_text: str) -> list[str]:
    """A dense phase (>= SUBDIVIDE_THRESHOLD requirements) becomes one sub-phase per
    requirement, each carrying the phase's shared context so it stays grounded. A phase with
    fewer requirements is returned unchanged."""
    lead, reqs = _requirements(slice_text)
    if len(reqs) < SUBDIVIDE_THRESHOLD:
        return [slice_text]
    has_head = bool(lead) and lead[0].lstrip().startswith("#")
    head = lead[0].rstrip() if has_head else ""
    body = "\n".join(lead[1:] if has_head else lead).strip()
    out = []
    n = len(reqs)
    for k, req in enumerate(reqs, 1):
        parts = [f"{head} — step {k} of {n}" if head else f"### Step {k} of {n}"]
        if body:
            parts.append(body)
        parts.append(req.strip())
        out.append("\n\n".join(parts))
    return out


def decompose(task: str) -> list[str]:
    """Split a task into small, ordered units for one-at-a-time implementation: by the text's
    Phase/Step or markdown headers. With MELLUM_SUBDIVIDE=1, also subdivide any dense phase
    (>= SUBDIVIDE_THRESHOLD requirements) into one sub-phase per stated requirement — the
    throughput lever for the dense-phase wall. Off by default (it changes phase count, which
    shifts --start-phase seed indices), opt-in for the decomposition experiment."""
    parts = _heading_split(task)
    if os.environ.get("MELLUM_SUBDIVIDE") not in ("1", "true", "yes"):
        return parts
    out: list[str] = []
    for part in parts:
        out.extend(subdivide(part))
    return out


def phase_title(slice_text: str) -> str:
    """A one-line title for a phase slice (its first heading, hashes stripped)."""
    first = slice_text.lstrip().splitlines()[0] if slice_text.strip() else "task"
    return first.lstrip("#").strip()[:80]


ORIENT = (
    "You are ORIENTING a build, not doing it. You are given the list of phase titles for a task "
    "(and specs/ may be present to read). In ONE short line, state the NORTH STAR — the overall "
    "goal of the finished app, one sentence. Output ONLY that one line: no preamble, no list, no "
    "code, no markdown."
)


def run_orient(titles: str, *, workspace: Path, profile: Path, recorder: Path, provider: str,
               model: str, trace: Path, timeout: float) -> str:
    """Ask the model for the one-line north star from the phase titles. Best-effort + fallback."""
    argv = [
        "pi", *harness.FLAGS, "--provider", provider, "--model", model,
        "--thinking", "off", "--no-session", "--tools", "read,grep,find,ls",
        "-e", str(harness.THINK_TAGS), "-e", str(recorder), "--system-prompt", ORIENT,
        f"Phase titles, in order:\n{titles}\n\nState the north star in one line.",
    ]
    env = {**os.environ, "PI_CODING_AGENT_DIR": str(profile), "MELLUM_TRACE_FILE": str(trace)}
    # No stdin: Pi with -p appends piped stdin to its prompt.
    child = subprocess.Popen(argv, cwd=workspace, env=env, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
    finally:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for line in lr.final_text(trace).splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:200]
    return "Build the complete application described across all the phases."


def fork_workspace(base: Path, dest: Path) -> None:
    """A fresh copy of the workspace SOURCE for an independent attempt. The venv is shared
    read-only (`uv run --frozen` does not mutate it), so forking is cheap."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for item in base.iterdir():
        if item.name == ".venv":
            os.symlink(item.resolve(), dest / ".venv")
        elif item.is_dir():
            shutil.copytree(item, dest / item.name)
        else:
            shutil.copy2(item, dest / item.name)


def promote(winner: Path, base: Path) -> None:
    """Make the winning attempt the new shared workspace: replace the source, keep the venv."""
    for item in list(base.iterdir()):
        if item.name == ".venv":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    for item in winner.iterdir():
        if item.name == ".venv":
            continue
        if item.is_dir():
            shutil.copytree(item, base / item.name)
        else:
            shutil.copy2(item, base / item.name)


def restore_gate(workspace: Path) -> None:
    """Re-materialise EVERY frozen per-phase acceptance test into tests/ before the
    authoritative scoring run. This makes the gate cumulative: a later phase cannot
    pass by regressing an earlier one, and a coder that edited or deleted a gate file
    gets it restored. The examiner froze each phase under plan/gate/phase_<n>.py."""
    gate = workspace / "plan" / "gate"
    if not gate.is_dir():
        return  # single-phase easy runs may freeze a single file instead; nothing to do
    tests = workspace / "tests"
    tests.mkdir(exist_ok=True)
    for stale in tests.glob("test_gate_phase_*.py"):
        stale.unlink()
    for frozen in sorted(gate.glob("phase_*.py")):
        shutil.copy2(frozen, tests / f"test_gate_{frozen.stem}.py")


def _git(workspace: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(workspace), *args],
                          capture_output=True, text=True, check=False)


def git_init_workspace(workspace: Path) -> None:
    """Put the workspace under git so each PASSING phase is a checkpoint a later breaking change can
    be reverted to and redone — a broken phase must not poison the accumulated good work or the
    grade. The venv, caches and run traces are ignored so only the app + gates are tracked."""
    gi = workspace / ".gitignore"
    text = gi.read_text() if gi.is_file() else ""
    for pat in (".venv/", "__pycache__/", "*.pyc", "*.subfeed", "trace*.jsonl"):
        if pat not in text:
            text += ("\n" if text and not text.endswith("\n") else "") + pat + "\n"
    gi.write_text(text)
    _git(workspace, "init", "-q")
    _git(workspace, "config", "user.email", "flow@harness.local")
    _git(workspace, "config", "user.name", "flow-harness")
    git_checkpoint(workspace, "base")


def git_checkpoint(workspace: Path, msg: str) -> None:
    """Commit the workspace as a per-phase checkpoint (no-op safe if nothing changed)."""
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "--allow-empty", "-m", msg)


def git_revert_to_checkpoint(workspace: Path) -> None:
    """Roll the workspace back to the last checkpoint (the last passing phase), discarding a broken
    attempt — the harness's 'revert the breaking change' so the next round redoes from known-good.
    The frozen gates survive it: a phase's gate is frozen after the last checkpoint, and losing it
    lets the next round freeze a different, possibly weaker, gate for the same phase."""
    gate = workspace / "plan" / "gate"
    frozen = {f.name: f.read_bytes() for f in gate.glob("phase_*.py")} if gate.is_dir() else {}
    _git(workspace, "reset", "--hard", "-q", "HEAD")
    _git(workspace, "clean", "-fdq", "-e", ".venv")
    if frozen:
        gate.mkdir(parents=True, exist_ok=True)
        for name, body in frozen.items():
            (gate / name).write_bytes(body)


def app_compiles(workspace: Path) -> bool:
    """True if every top-level app module compiles. A failed phase can leave app.py with a syntax
    error (e.g. an unterminated string), which would make the whole app un-importable and sink the
    grade; when this is false the harness reverts to the last checkpoint instead of grading rubble."""
    import py_compile
    for p in sorted(workspace.glob("*.py")):
        try:
            py_compile.compile(str(p), doraise=True)
        except py_compile.PyCompileError:
            return False
    return True


def round_concurrency(rnd: int, concurrency: int, retry_concurrency: int) -> int:
    """First try (round 0) uses `concurrency` (default 1, cheap); retries (rounds 1+) escalate to
    `retry_concurrency`, so best-of-N parallel samples are spent only on rounds that actually retry
    — the hard phases — not on phases that pass first try. Agnostic: no hardcoded phase numbers."""
    return concurrency if rnd == 0 else retry_concurrency


def ensure_gate_frozen(examine, is_frozen, retries: int = 1) -> bool:
    """Free-arm INVARIANT 1 — a frozen external acceptance test exists BEFORE any build. Run the
    examiner, then verify it froze a real gate; one corrective retry covers a dropped or
    mis-formatted reply that froze nothing (seen on hard phases 4 and 5). Returns whether a gate is
    now frozen; a False means the build must not proceed — this phase has no definition of DONE yet.
    Pure of the model: `examine` runs one examiner pass, `is_frozen` re-checks the frozen file."""
    for _ in range(retries + 1):
        examine()
        if is_frozen():
            return True
    return False


def drive_free_coder(dispatch, check, attempts: int) -> tuple[bool, int]:
    """Free-arm INVARIANT 2 — exit is verified, never self-declared. The agent builds freely; the
    harness re-runs the FROZEN gate (`check`) and, on a fail, re-dispatches the agent WITH the
    failure text ("sorry, you didn't pass — here's what failed, try again"), bounded by `attempts`
    (the max-retries budget). 'Done' is the harness's word, not the agent's. Returns (solved, rounds)
    so a run records whether the fixed model was EVER able to pass and how many rounds it took.
      dispatch(rnd, feedback) -> None   runs the coder once on the shared workspace
      check() -> (ok: bool, output: str)  re-runs the frozen gate; output is the next feedback"""
    feedback = ""
    for rnd in range(attempts):
        dispatch(rnd, feedback)
        ok, output = check()
        if ok:
            return True, rnd + 1
        feedback = output
    return False, attempts


def gate_files(workspace: Path, phase: int | None = None) -> list[Path]:
    """The restored frozen acceptance gate — tests/test_gate_phase_*.py — and nothing else. The
    phase is judged on this, the frozen definition of DONE, never on the coder's own scratch tests.
    With `phase` set, return only THAT phase's gate; otherwise the whole cumulative set. Scoring a
    phase on its OWN gate stops one stochastically-brittle earlier gate (a false-fail) from
    poisoning every later phase's pass decision — the run's observed failure mode. Regressions are
    caught by the final hidden grade, not by blocking mid-run on a possibly-brittle earlier gate.
    Empty when no gate was frozen (the single-file easy gate), so callers fall back to the suite."""
    tests = workspace / "tests"
    if not tests.is_dir():
        return []
    pat = f"test_gate_phase_{phase}.py" if phase is not None else "test_gate_phase_*.py"
    return sorted(tests.glob(pat))


def run_gate(workspace: Path, timeout: float, phase: int | None = None) -> tuple[bool, str]:
    """Score the workspace against the frozen acceptance gate (see gate_files). With `phase`, score
    only that phase's own gate. Falls back to the whole suite when there is no frozen gate. Mirrors
    loop_run.run_tests' env so `from app import app` resolves exactly as the hidden grader sees it."""
    gates = gate_files(workspace, phase)
    if not gates:
        return lr.run_tests(workspace, timeout)
    env = {**os.environ, "PYTHONPATH": str(workspace)}
    cmd = ["uv", "run", "--with", "pytest", "pytest", "-q",
           *[str(g.relative_to(workspace)) for g in gates]]
    try:
        proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True,
                              timeout=timeout, check=False, env=env)
    except subprocess.TimeoutExpired:
        return False, "gate tests timed out"
    out = proc.stdout + proc.stderr
    return proc.returncode == 0, "\n".join(out.splitlines()[-25:])


def phase_gate_ok(workspace: Path, phase: int) -> bool:
    """A fork may only count as passing phase N if it actually FROZE a real acceptance
    test for phase N. Without this, a fork whose examiner produced nothing just inherits
    the earlier phases' gate and 'passes' trivially — and best-of-N then promotes that
    weakest fork first. The frozen file must exist, be importable Python (an examiner that
    emitted an HTML blob fails here), and define at least one test."""
    f = workspace / "plan" / "gate" / f"phase_{phase}.py"
    if not f.is_file():
        return False
    text = f.read_text()
    try:
        compile(text, str(f), "exec")
    except SyntaxError:
        return False
    return re.search(r"(?m)^\s*(async\s+)?def\s+test\w*\s*\(|^\s*class\s+Test\w*", text) is not None


def pin_temperature(profile_dir: Path, temp: float) -> None:
    """Set the sampling temperature in a per-attempt profile, to SPREAD the best-of-N samples:
    low temps write the by-the-book correct code, high temps explore out of a stuck solution."""
    mp = profile_dir / "models.json"
    data = json.loads(mp.read_text())
    _, prov = next(iter(data["providers"].items()))
    prov["models"][0].setdefault("samplingParams", {})["temperature"] = temp
    mp.write_text(json.dumps(data, indent=2) + "\n")


def temp_ladder(n: int) -> list[float]:
    """A temperature spread across n parallel attempts (0.3 conservative → 1.2 exploratory)."""
    if n <= 1:
        return [0.7]
    return [round(0.3 + 0.9 * i / (n - 1), 2) for i in range(n)]


def seeded_done(titles: list[str], start_phase: int) -> list[str]:
    """When resuming at `start_phase`, the earlier phases are assumed already built and passing.
    Their titles seed the `done` list so the forward-context message lists them as implemented."""
    return list(titles[: max(0, start_phase - 1)])


def seed_from_bundle(seed: Path, workspace: Path, start_phase: int) -> None:
    """Resume at phase `start_phase` by seeding `workspace` from a PRIOR run's `seed` workspace:
    its built app (app.py, models.py, templates/, tests/, data.db, pyproject/uv.lock) and the
    frozen per-phase gates under plan/gate/. The gates for phases 1..start_phase-1 MUST exist in
    the seed — scoring phase N re-runs the whole cumulative gate. The venv, caches and traces are
    NOT copied (a copied .venv carries stale absolute paths); `uv sync` recreates the venv."""
    if not seed.is_dir():
        raise FileNotFoundError(f"--seed-from workspace not found: {seed}")
    missing = [n for n in range(1, start_phase)
               if not (seed / "plan" / "gate" / f"phase_{n}.py").is_file()]
    if missing:
        raise FileNotFoundError(
            f"seed {seed} has no frozen gate for phase(s) {missing}; cannot resume at phase {start_phase}")
    shutil.copytree(seed, workspace, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc",
                                                  "trace*.jsonl", "*.subfeed", "node_modules"))


def fixture_schema_note(workspace: Path) -> str:
    """Ground the phase on the REAL fixture schema: list each persistent table's actual columns, so
    the examiner and coder USE the columns that exist (e.g. a report's real `date` column) instead
    of inventing or renaming one — a prose 'inspect the schema' rule the small model ignores. Empty
    when the workspace ships no database. Agnostic: reflects whatever *.db tables are present."""
    import sqlite3
    lines: list[str] = []
    for db in sorted(workspace.glob("*.db")):
        try:
            con = sqlite3.connect(db)
            try:
                tables = [r[0] for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                for t in tables:
                    cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
                    if cols:
                        lines.append(f"  {db.name}.{t}({', '.join(cols)})")
            finally:
                con.close()
        except sqlite3.Error:
            continue
    if not lines:
        return ""
    return ("\n\nEXISTING DATABASE SCHEMA — use these REAL columns; do not invent, rename or assume "
            "a column the data does not have:\n" + "\n".join(lines))


def restore_fixture_data(workspace: Path, base_dir: Path) -> list[str]:
    """Before the authoritative grade, put each fixture table's ROWS back from the suite's pristine
    base database into the workspace database, keeping the workspace's (migrated) schema. A test
    that mutated the fixture — e.g. `DELETE FROM tickets` in a report gate — otherwise corrupts the
    very data the spec's 'report from the database' and the hidden grader read. Columns the fixture
    lacks (added by the coder's migrations) keep their defaults. Agnostic: it mirrors whatever
    tables the base fixture ships, nothing suite-specific. Returns the names of restored dbs."""
    import sqlite3
    restored: list[str] = []
    if not base_dir.is_dir():
        return restored
    for base_db in sorted(base_dir.glob("*.db")):
        ws_db = workspace / base_db.name
        if not ws_db.is_file():
            continue
        src = sqlite3.connect(base_db)
        dst = sqlite3.connect(ws_db)
        try:
            tables = [r[0] for r in src.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            ws_tables = {r[0] for r in dst.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            for t in tables:
                if t not in ws_tables:
                    continue  # a table the workspace dropped — leave the grade to judge that
                base_cols = [r[1] for r in src.execute(f"PRAGMA table_info({t})")]
                ws_cols = {r[1] for r in dst.execute(f"PRAGMA table_info({t})")}
                cols = [c for c in base_cols if c in ws_cols]  # intersection: tolerate a migrated/renamed schema
                if not cols:
                    continue
                rows = src.execute(f"SELECT {','.join(cols)} FROM {t}").fetchall()
                dst.execute(f"DELETE FROM {t}")
                if rows:
                    ph = ",".join("?" * len(cols))
                    dst.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({ph})", rows)
            dst.commit()
            restored.append(base_db.name)
        finally:
            src.close()
            dst.close()
    return restored


def drive_phase_free(pnum: int, *, workspace: Path, profile: Path, recorder: Path, provider: str,
                     model: str, run: Path, timeout: float, thinking: str,
                     attempts: int, memory=None, situation: str = "") -> tuple[bool, int]:
    """Drive ONE phase the FREE way: freeze the gate (invariant 1), then let the agent build and
    verify the exit by re-running that gate (invariant 2), re-dispatching with the failure text on
    each fail. Returns (solved, rounds) — whether the fixed model was EVER able to pass, and how
    many rounds it took. The forced step order is gone; the two invariants are all the harness
    enforces. Uses the same shipped spawn path (`run_top`) as the forced flow, so the guards,
    recorder and feed are identical — only the tools and prompt differ.

    With a `memory` (learn/code/memory.Memory), the agent is grounded like a skill: lessons whose
    situation matches this phase are injected into each dispatch, and a general, agnostic lesson is
    distilled from every gate failure and stored — so the run learns from its own mistakes and the
    portable memory file carries that forward to later phases, runs, machines or a fine-tune."""
    # INVARIANT 1 — a frozen external acceptance test must exist before any build.
    def examine() -> None:
        run_top("Call examine() now — no arguments.", workspace=workspace, profile=profile,
                recorder=recorder, provider=provider, model=model,
                trace=run / f"trace-p{pnum}-examine.jsonl", timeout=min(timeout, 180.0),
                thinking=thinking, phase=pnum, tools=EXAMINE_ONLY_TOOLS,
                system_prompt=EXAMINE_MSG, load_flow=True, label=f"examiner p{pnum}")

    if not ensure_gate_frozen(examine, lambda: phase_gate_ok(workspace, pnum), retries=1):
        lr.emit(f"  phase {pnum}: examiner froze no gate — no definition of DONE, skipping")
        return False, 0
    restore_gate(workspace)  # materialize the frozen gate under tests/ so the coder can read it
    lr.emit(f"  phase {pnum}: gate frozen — free coder may build (max {attempts} round(s))")

    # INVARIANT 2 — exit is verified by the harness, never self-declared by the agent.
    def dispatch(rnd: int, feedback: str) -> None:
        if rnd == 0:
            msg = ("Build the task in plan/TASK.md so the frozen acceptance test under tests/ "
                   "passes. Run it yourself with `uv run python -m pytest -q tests/`.")
        else:
            msg = ("Your previous attempt did NOT pass the acceptance test. Here is what still "
                   f"failed:\n\n{feedback}\n\nFix it and make the gate pass; continue from the "
                   "current workspace, do not start over.")
        if memory is not None:  # ground the agent with lessons this situation has earned (like a skill)
            grounding = memory.as_grounding(memory.retrieve(situation or f"phase {pnum}"))
            if grounding:
                msg += "\n\n" + grounding
        run_top(msg, workspace=workspace, profile=profile, recorder=recorder, provider=provider,
                model=model, trace=run / f"trace-p{pnum}-free-{rnd}.jsonl", timeout=timeout,
                thinking=thinking, phase=pnum, tools=FREE_CODER_TOOLS,
                system_prompt=FREE_WORKFLOW, load_flow=False, label=f"free coder p{pnum} r{rnd + 1}")

    def check() -> tuple[bool, str]:
        restore_gate(workspace)  # canonical frozen gate — undo any coder tampering before judging
        ok, out = run_gate(workspace, 120.0, pnum)
        ok = ok and phase_gate_ok(workspace, pnum)
        tail = out[-2000:]  # the tail of the gate output becomes the next round's feedback
        if not ok and memory is not None:  # learn from the failure: store one general, agnostic lesson
            lesson = memory_distill(tail)
            if lesson and memory.add(f"{situation} :: {lesson.situation}".strip(" :"), lesson.lesson):
                lr.emit(f"  phase {pnum}: learned a lesson — {lesson.lesson[:70]}…")
        return ok, tail

    return drive_free_coder(dispatch, check, attempts)


def loop(suite_name: str, *, runs_dir: Path, timeout: float, base_url: str, model_id: str,
         thinking: str, attempts: int, concurrency: int,
         start_phase: int = 1, seed_from: Path | None = None, context_window: int = 56000,
         thinking_format: str | None = None,
         retry_concurrency: int | None = None, flow_mode: str = "forced",
         memory_path: Path | None = None) -> dict:
    retry_concurrency = retry_concurrency or concurrency  # retries escalate to this (default: same)
    memory = Memory(memory_path) if (memory_path and flow_mode == "free") else None
    suite = harness.load_suite(harness.SUITES, suite_name)
    run = harness.new_run(runs_dir, f"flow-{suite_name}")
    workspace = run / "workspace"
    workspace.mkdir()
    lr._FEED_PATH = run / "feed.log"
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if start_phase > 1:
        if seed_from is None:
            raise ValueError("--start-phase > 1 requires --seed-from <a prior run's workspace>")
        seed_from_bundle(seed_from, workspace, start_phase)
        lr.emit(f"  resuming at phase {start_phase}, seeded from {seed_from}")
    elif suite.root is not None and (suite.root / "base").is_dir():
        shutil.copytree(suite.root / "base", workspace, dirs_exist_ok=True)
    shutil.copytree(harness.PROFILE, run / "profile")
    lr.pin_profile(run / "profile", base_url, model_id, context_window, thinking_format=thinking_format)
    recorder = run / "record-pi.mjs"
    shutil.copy2(harness.RECORDER, recorder)
    provider, model = harness.profile_pin(run / "profile")
    task = "\n\n".join(suite.prompts)

    # Create the venv from the lockfile (synchronously — parallel attempts fork it) and index it
    # for the `lookup` tool. uv sync blocks; the BM25 index builds in the background.
    docs_lookup = Path(__file__).resolve().parent / "docs_lookup.py"
    subprocess.run(["uv", "sync", "--frozen"], cwd=workspace, capture_output=True, timeout=300, check=False)
    subprocess.Popen(["python3", str(docs_lookup), "--rebuild", "warmup"], cwd=workspace,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    git_init_workspace(workspace)  # checkpoint per passing phase; revert a breaking change, redo

    # Decompose into phases and drive ONE at a time over the shared workspace, so each
    # orchestrator run gets a small, answerable task. Each phase carries a small, constant
    # FORWARD CONTEXT — a model-determined north star, a running summary of what is already
    # built, and the last phase's context — so a decomposed step stays grounded without ever
    # handing the model the whole task. Within a phase the orchestrator runs in -p mode and can
    # stall on turn 1, so we re-invoke it (it resumes from the workspace) until that phase's
    # tests pass or the attempt budget runs out.
    phases = decompose(task)
    titles = [phase_title(p) for p in phases]
    lr.emit(f"  decomposed into {len(phases)} phase(s): " + " | ".join(titles))
    if len(phases) > 1:
        north_star = run_orient(
            "\n".join(f"{i}. {t}" for i, t in enumerate(titles, 1)),
            workspace=workspace, profile=run / "profile", recorder=recorder,
            provider=provider, model=model, trace=run / "trace-orient.jsonl",
            timeout=min(timeout, 150.0))
    else:
        north_star = titles[0]
    lr.emit(f"  north star: {north_star}")

    # One independent best-of-N attempt: fork the workspace, run the orchestrator at its own
    # sampling temperature, report whether that fork's tests pass. Run concurrently so the
    # batched oMLX server actually fills — this is where the concurrency we unlocked turns into
    # speed, and best-of-N beats the per-phase variance of a single try.
    # The orchestrator's own message is SHORT — the phase task lives in TASK.md (forked into each
    # attempt), and every tool is argument-free, so the model never generates a large tool-call
    # argument (which oMLX's parser drops, the root cause of the "stalls").
    orch_msg = ("The task for this phase is in TASK.md. Build it by calling the tools — all take "
                "NO arguments. Start now by calling plan().")

    def one_attempt(pnum: int, rnd: int, idx: int, temp: float):
        aw = run / f"p{pnum}-r{rnd}-t{idx}"
        fork_workspace(workspace, aw)
        prof = run / f"profile-t{idx}"
        if not prof.exists():
            shutil.copytree(run / "profile", prof)
            pin_temperature(prof, temp)
        run_top(orch_msg, workspace=aw, profile=prof, recorder=recorder, provider=provider,
                model=model, trace=run / f"trace-p{pnum}-r{rnd}-{idx}.jsonl",
                timeout=timeout, thinking=thinking, phase=pnum)
        restore_gate(aw)  # materialize every frozen gate so the coder sees them; score THIS phase's own
        ok, _ = run_gate(aw, 120.0, pnum)  # a brittle earlier gate must not poison this phase's pass
        ok = ok and phase_gate_ok(aw, pnum)  # and THIS phase must have frozen a real acceptance test
        return idx, ok, aw

    passed = False
    phase_results: list[bool] = []
    phase_rounds: list[int] = []  # free mode: how many rounds each phase took (0 = no gate frozen)
    done: list[str] = seeded_done(titles, start_phase)  # earlier phases came from the seed
    for pnum, ptext in enumerate(phases, start=1):
        title = titles[pnum - 1]
        if pnum < start_phase:
            continue  # already built and frozen in the seeded workspace
        if pnum == 1:
            base_msg = (f"NORTH STAR: {north_star}\n\n"
                        f"YOUR TASK — phase 1 of {len(phases)}:\n\n{ptext}")
        else:
            progress = (
                f"PROGRESS SO FAR: already implemented and passing — {'; '.join(done)}.\n"
                f"LAST PHASE: {done[-1]} — built, its tests pass; build on it, do not break it.\n\n"
                if done else
                "PROGRESS SO FAR: earlier phase(s) did NOT pass — implement this phase on the "
                "workspace as it currently stands.\n\n"
            )
            base_msg = (
                f"NORTH STAR: {north_star}\n"
                + progress
                + f"YOUR TASK — phase {pnum} of {len(phases)}:\n\n{ptext}\n\n"
                + "Build on the existing workspace (app.py, models.py, templates/, tests/); keep "
                "every existing route and test working, and do not rewrite what already passes."
            )
        # The phase task (north star + progress + spec) goes in plan/TASK.md — NOT a tool argument.
        # Append the REAL fixture schema so the coder/examiner use the columns that exist.
        (workspace / "plan").mkdir(exist_ok=True)
        (workspace / "plan" / "TASK.md").write_text(base_msg + fixture_schema_note(workspace))
        (workspace / "plan" / "REVIEW.md").unlink(missing_ok=True)  # fresh feedback per phase
        lr.emit(f"\n========== PHASE {pnum}/{len(phases)}: {title} ==========")
        passed = False
        if flow_mode == "free":
            # FREE arm: freeze the gate, then let the agent self-drive with a harness-verified exit
            # (re-run the frozen gate; re-dispatch on failure, bounded). No forced step order.
            passed, rnds = drive_phase_free(
                pnum, workspace=workspace, profile=run / "profile", recorder=recorder,
                provider=provider, model=model, run=run, timeout=timeout, thinking=thinking,
                attempts=attempts, memory=memory, situation=title)
            phase_rounds.append(rnds)
            if passed:
                git_checkpoint(workspace, f"phase {pnum}: {title} — PASS (free, {rnds} round(s))")
                lr.emit(f"  phase {pnum}: SOLVED in {rnds} round(s)")
                done.append(title)
            elif not app_compiles(workspace):  # never carry a broken app into later phases/the grade
                git_revert_to_checkpoint(workspace)
                lr.emit(f"  phase {pnum}: not solved in {attempts} round(s) — reverted broken app")
            else:
                lr.emit(f"  phase {pnum}: not solved in {attempts} round(s) — continuing")
            phase_results.append(passed)
            continue
        for rnd in range(attempts):
            # Escalate-on-retry: the first try runs at `concurrency` (default 1, cheap — most phases
            # pass round 1); retries escalate to `retry_concurrency` so best-of-N samples are spent
            # only where retries actually happen (the hard phases), not on phases that pass first
            # try. Agnostic — it adapts to where the model struggles, with no hardcoded phase numbers.
            eff_conc = round_concurrency(rnd, concurrency, retry_concurrency)
            if eff_conc <= 1:
                nudge = "" if rnd == 0 else (
                    " Work from a previous attempt may already be in the workspace — continue toward "
                    "passing tests; call plan() only if TODO.md is missing."
                )
                run_top(orch_msg + nudge, workspace=workspace, profile=run / "profile", recorder=recorder,
                        provider=provider, model=model, trace=run / f"trace-p{pnum}-{rnd}.jsonl",
                        timeout=timeout, thinking=thinking, phase=pnum)
                restore_gate(workspace)  # materialize every frozen gate for the coder; score THIS phase's own
                passed, _ = run_gate(workspace, 120.0, pnum)  # a brittle earlier gate must not poison this phase
                passed = passed and phase_gate_ok(workspace, pnum)  # and THIS phase must have frozen a real acceptance test
            else:
                temps = temp_ladder(eff_conc)
                lr.emit(f"  phase {pnum} round {rnd + 1}: {eff_conc} parallel attempts, temps {temps}")
                winner = None
                with cf.ThreadPoolExecutor(max_workers=eff_conc) as ex:
                    futs = [ex.submit(one_attempt, pnum, rnd, i, temps[i]) for i in range(eff_conc)]
                    for fut in cf.as_completed(futs):
                        i, ok, aw = fut.result()
                        lr.emit(f"  phase {pnum} try{i} (t={temps[i]}): {'PASS' if ok else 'fail'}")
                        if ok and winner is None:
                            winner = aw
                if winner is not None:
                    promote(winner, workspace)
                    passed = True
            if passed:
                git_checkpoint(workspace, f"phase {pnum}: {title} — PASS")  # known-good anchor
                lr.emit(f"  phase {pnum}: tests PASS")
                break
            lr.emit(f"  phase {pnum} round {rnd + 1}/{attempts}: no pass — retrying")
            if not app_compiles(workspace):  # a round left the app broken — revert, redo from last good
                git_revert_to_checkpoint(workspace)
                lr.emit(f"  phase {pnum}: app did not compile — reverted to last checkpoint")
        if not passed:
            if not app_compiles(workspace):  # never carry a broken app into later phases or the grade
                git_revert_to_checkpoint(workspace)
                lr.emit(f"  phase {pnum}: still FAIL — reverted the broken attempt to last checkpoint")
            lr.emit(f"  phase {pnum}: still FAIL after {attempts} round(s) — continuing")
        phase_results.append(passed)
        if passed:
            done.append(title)

    # Never grade a broken app: if the final state does not compile (a last failed phase left it so),
    # revert to the last known-good checkpoint so the hidden grade scores coherent work, not rubble.
    if not app_compiles(workspace):
        git_revert_to_checkpoint(workspace)
        lr.emit("  final app did not compile — reverted to last checkpoint before grading")
    # A report gate can mutate the fixture db (DELETE/INSERT); put the fixture rows back before the
    # authoritative grade so it reads the real data the spec reports "from the database", not a
    # test's leftovers. Keeps the coder's migrated schema.
    if suite.root is not None:
        restored = restore_fixture_data(workspace, suite.root / "base")
        if restored:
            lr.emit(f"  restored fixture data before grading: {', '.join(restored)}")
    # Granular hidden grade: full pass (bool) is almost always False on hard (the 31/34 ceiling), so
    # record the COUNT of hidden tests passed — that's what discriminates one run/arm from another.
    graded, hidden_passed, hidden_total = hidden_grade(workspace, suite)
    todo = (workspace / "plan" / "TODO.md").exists()
    result = {
        "suite": suite_name, "flow_mode": flow_mode,
        "memory": str(memory_path) if memory is not None else None,
        "coder_feedback": os.environ.get("MELLUM_CODER_FEEDBACK") != "0",
        "visible": passed, "graded": graded,
        "hidden_passed": hidden_passed, "hidden_total": hidden_total,
        "todo": todo, "phases": len(phases), "phase_results": phase_results,
        "phase_rounds": phase_rounds,  # free mode: rounds each phase took (0 = no gate frozen)
        "north_star": north_star, "model": model_id, "thinking": thinking, "started": started,
        "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    lr.emit(f"{suite_name}: visible={'PASS' if passed else 'FAIL'} "
            f"hidden={hidden_passed}/{hidden_total} ({'PASS' if graded else 'partial'}) "
            f"TODO.md={'yes' if todo else 'NO'} bundle={run}")
    lr._FEED_PATH = None
    return result


def hidden_grade(workspace: Path, suite) -> tuple[bool, int, int]:
    """The suite's hidden grade as (full pass, checks passed, checks expected)."""
    graded, _, missing, _ = harness.score_workspace_details(workspace, suite)
    total = len(suite.expected)
    return graded, total - len(missing), total


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--suite", required=True, help="a suite name, or comma-separated names")
    p.add_argument("--timeout", type=float, default=900.0, help="per-attempt wall-clock budget")
    p.add_argument("--attempts", type=int, default=6, help="max rounds per phase (retries / best-of-N rounds)")
    p.add_argument("--concurrency", type=int, default=1,
                   help="parallel attempts per phase (best-of-N on the batched server); 1 = sequential")
    p.add_argument("--thinking", default="medium", help="orchestrator thinking budget")
    p.add_argument("--runs-dir", type=Path, default=harness.RUNS / "flow")
    p.add_argument("--base-url", default="http://127.0.0.1:8001/v1")
    p.add_argument("--model", default="Mellum2.1-12B-A2.5B-Thinking-6bit")
    p.add_argument("--start-phase", type=int, default=1,
                   help="resume at this 1-indexed phase; phases before it are taken from --seed-from")
    p.add_argument("--seed-from", type=Path, default=None,
                   help="a prior run's workspace to seed the built app and earlier frozen gates from "
                        "(required when --start-phase > 1)")
    p.add_argument("--context-window", type=int, default=56000,
                   help="pinned context window; smaller reserves less KV per request so --concurrency "
                        ">1 (best-of-N) fits under the oMLX memory guard. Keep above the largest "
                        "context a phase reaches or it truncates.")
    p.add_argument("--thinking-format", default=None,
                   help="override the pinned model's thinkingFormat (pi compat) for a non-Mellum "
                        "model served elsewhere, e.g. 'chat-template' for a vLLM-served gemma. Keeps "
                        "reasoning and tool calling on; only changes how thinking is encoded, so pi "
                        "does not force Mellum's qwen-chat-template onto it (the cause of the leaked "
                        "thought tokens).")
    p.add_argument("--retry-concurrency", type=int, default=None,
                   help="best-of-N concurrency for RETRY rounds (rounds 2+); defaults to --concurrency. "
                        "Set e.g. --concurrency 1 --retry-concurrency 2 to try singles first and spend "
                        "parallel samples only on phases that actually retry (the hard ones).")
    p.add_argument("--flow-mode", choices=["forced", "free"], default="forced",
                   help="forced (default): the fixed six-step pipeline (plan→review→examine→code→"
                        "review→test) as ordered tools. free: the harness freezes the gate, then the "
                        "agent self-drives with ordinary tools and a harness-verified exit (re-run the "
                        "frozen gate; re-dispatch on failure, bounded by --attempts).")
    p.add_argument("--memory", type=Path, default=None,
                   help="free mode only: a portable memory.jsonl of GENERAL lessons. Retrieved lessons "
                        "ground each build (like a skill), and a general, agnostic lesson is distilled "
                        "from every gate failure and appended — so the run learns from its mistakes "
                        "and the file carries forward to later runs, machines or a fine-tune. The "
                        "with-vs-without comparison is the deciding experiment (see the research note).")
    args = p.parse_args(argv)
    for name in args.suite.split(","):
        loop(name.strip(), runs_dir=args.runs_dir.resolve(), timeout=args.timeout,
             base_url=args.base_url, model_id=args.model, thinking=args.thinking,
             attempts=args.attempts, concurrency=args.concurrency,
             start_phase=args.start_phase, seed_from=args.seed_from,
             context_window=args.context_window, thinking_format=args.thinking_format,
             retry_concurrency=args.retry_concurrency,
             flow_mode=args.flow_mode, memory_path=args.memory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
