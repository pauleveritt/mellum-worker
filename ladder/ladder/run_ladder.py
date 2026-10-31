"""Run ladder rungs against the Mellum worker and score the evidence.

Direct mode launches ``pi -p`` in the recovery report's clean profile: no
extensions, skills, or context files; the worker prompt in place of Pi's; the
bundle's record extension capturing every provider request and tool event.

    uv run python -m ladder.run_ladder --profile baseline --rung 1 --repeat 3 --out ../evals/baseline/2026-10-09-phase0-baseline
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from contextlib import nullcontext
from dataclasses import asdict, replace
from pathlib import Path
from uuid import uuid4

from .omlx_profiles import PROFILES, AdminClient, check_effective_params, profile
from .pi_launch import resolve_pi, workspace_preflight
from .pi_profile import (
    LADDER_ROOT,
    REPO_ROOT,
    direct_agent_dir,
    mirror_agent_dir,
)
from .pi_trace import load_trace, stdout_settlement, summarize_trace
from .leftovers import stop_leftovers
from .host_record import gpu_identity, server_identity
from .rungs import FIXTURES, RUNGS, Rung, copy_fixture
from .score import score

log = logging.getLogger(__name__)
PROMPT_FILE = REPO_ROOT / "prompts" / "mellum-worker.md"
RECORD_EXT = REPO_ROOT / "extensions" / "mellum-recorder.ts"
MODE_EXT = REPO_ROOT / "extensions" / "mellum-worker.ts"
GUARDS_EXT = REPO_ROOT / "extensions" / "mellum-guards.ts"
FLOW_EXT = REPO_ROOT / "extensions" / "mellum-flow.ts"
MODEL = "omlx/Mellum2.1-12B-A2.5B-Thinking-6bit"
MODEL_ID = MODEL.split("/", 1)[1]
TOOLS = "read,grep,find,ls,bash,edit,write"
# A mediated run (--acceptance-test) drops grep and find: offline they shell out to
# fd/rg, which are missing, and under v6 the worker spent turns on them chasing
# unrelated tests. The measured default keeps all seven.
MEDIATED_TOOLS = "read,ls,bash,edit,write"

# The spec-driven flow orchestrator (mellum-flow.ts): Pi coordinates the phase tools, which
# each run as an isolated sub-agent. The examiner writes the acceptance test FROM the spec, so
# a rung whose fixture ships no visible test still gets a checkable target. Constants mirror
# flow_run.py (the standalone flow runner); kept here so the ladder stays self-contained.
FLOW_TOOLS = "plan,review_plan,examine,code,review_code,test,read"
FLOW_ORCH_MSG = (
    "The task for this phase is in TASK.md. Build it by calling the tools — all take "
    "NO arguments. Start now by calling plan()."
)
FLOW_WORKFLOW = (
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


def prompt_version(prompt: Path) -> str:
    """The version named in the prompt file's first-line marker, else its stem."""
    first = prompt.read_text().splitlines()[0] if prompt.exists() else ""
    found = re.search(r"prompt (v\w+)", first)
    return found.group(1) if found else prompt.stem



HEADER = (
    "| rung | profile | mode | rep | result | tests_unchanged | requests | tool_errors | anchor_fail | "
    "noop_edit | write_existing | write_shrink | bash_mut | max_streak | largest_prompt_chars | nudges | stop | final_chars | reentries | deadline | wall_s (untrusted) |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
)


def build_pi_direct_args(
    sentence: str,
    guards: bool = False,
    prompt: Path = PROMPT_FILE,
    prompt_mode: str = "replace",
    thinking: str = "high",
    model: str = MODEL,
    extra_extensions: tuple[Path, ...] = (),
    tools: str = TOOLS,
) -> list[str]:
    """The worker alone. `replace` (the default) sends the worker prompt only, which is what
    the shipped agent file does; `append` keeps Pi's base prompt under it (phases 0-2)."""
    prompt_args = (
        ["--system-prompt", prompt.read_text()]
        if prompt_mode == "replace"
        else ["--append-system-prompt", str(prompt)]
    )
    args = [
        "pi",
        "-p",
        "--mode",
        "json",
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--no-session",
        "--thinking",
        thinking,
        "--model",
        model,
        "--tools",
        tools,
        *prompt_args,
        "-e",
        str(RECORD_EXT),
    ]
    if guards:
        args += ["-e", str(GUARDS_EXT)]
    # Extra extensions (e.g. a tool-call-assist plugin so a small model that
    # emits tool calls in its content can drive the loop) load alongside --no-extensions.
    for ext in extra_extensions:
        args += ["-e", str(ext)]
    return [*args, sentence]


def build_pi_flow_args(
    thinking: str = "high",
    model: str = MODEL,
    guards: bool = False,
) -> list[str]:
    """The spec-driven flow orchestrator in place of the direct worker. Pi loads mellum-flow.ts
    and drives the phase tools (plan, review_plan, examine, code, review_code, test); the examiner
    writes the acceptance test from the spec in TASK.md before the coder runs, so a rung with no
    shipped visible test still has a checkable target. The task text lives in TASK.md, so the
    orchestrator message carries no long argument."""
    args = [
        "pi",
        "-p",
        "--mode",
        "json",
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--no-session",
        "--thinking",
        thinking,
        "--model",
        model,
        "--tools",
        FLOW_TOOLS,
        "--system-prompt",
        FLOW_WORKFLOW,
        "-e",
        str(FLOW_EXT),
        "-e",
        str(RECORD_EXT),
    ]
    if guards:
        args += ["-e", str(GUARDS_EXT)]
    return [*args, FLOW_ORCH_MSG]


def child_env(
    parent: dict,
    trace: str,
    agent_dir: Path | None = None,
    offline: bool | None = None,
    mode: bool = False,
) -> dict:
    """The worker's environment: the parent's, minus the repo venv that uv exports.

    Direct mode runs offline against the ladder's own agent directory.
    Delegated mode points Pi at the mirrored operator profile and keeps the
    network, which the hosted parent model needs. MELLUM_WORKER_RUNS sends the
    guards' Worker run record beside the trace, so the operator's own log stays clean.
    """
    env = {k: v for k, v in parent.items() if k != "VIRTUAL_ENV"}
    if parent.get("VIRTUAL_ENV") and "PATH" in env:
        inherited_bin = str(Path(parent["VIRTUAL_ENV"]) / "bin")
        env["PATH"] = os.pathsep.join(
            p for p in env["PATH"].split(os.pathsep) if p != inherited_bin
        )
    env["MELLUM_TRACE_FILE"] = str(trace)
    env["MELLUM_WORKER_RUNS"] = str(Path(trace).parent / "mellum-worker-runs.jsonl")
    if mode:
        env["MELLUM_MODE"] = "1"
    if agent_dir is not None:
        env["PI_CODING_AGENT_DIR"] = str(agent_dir)
    if offline is None:
        offline = agent_dir is None
    if offline:
        env["PI_OFFLINE"] = "1"
    else:
        env.pop("PI_OFFLINE", None)
    return env


def mode_env(
    parent: dict, trace: Path, agent_dir: Path, scratch: Path, facts: bool = True
) -> dict:
    """Mode runs: headless Mode, the mirrored profile, and a run log under scratch.

    MELLUM_MODE_RUNS keeps the run out of the operator's real
    ~/.pi/agent/mellum-mode-runs.jsonl. ``facts=False`` sets MELLUM_MODE_FACTS=0,
    which turns the project-facts block off (Mode as shipped before it).
    """
    env = child_env(parent, str(trace), agent_dir, offline=False, mode=True)
    env["MELLUM_MODE_RUNS"] = str(scratch / "mellum-mode-runs.jsonl")
    if not facts:
        env["MELLUM_MODE_FACTS"] = "0"
    return env


def worker_provenance(root: Path = REPO_ROOT) -> dict:
    """Which worker the run measured: package.json's version and `git describe` (None outside git)."""
    version = json.loads((root / "package.json").read_text())["version"]
    try:
        described = subprocess.run(
            ["git", "-C", str(root), "describe", "--always", "--dirty"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except OSError, subprocess.CalledProcessError:
        described = None
    return {"worker_version": version, "worker_git": described or None}


def build_pi_primary_args(sentence: str, plain: bool = False, model: str = MODEL) -> list[str]:
    """Mellum as the primary agent, given the raw sentence.

    Two baselines the worker is measured against. Operator (default): no
    worker in the workspace, Superpowers and pi-subagents loaded as the
    operator has them — what "just swap the model" does. Plain: Pi's own base
    prompt and tools with no extensions, skills, or context files — the
    model's ceiling as a primary agent, separating Superpowers' effect from
    Pi's base prompt. Both load the recorder explicitly so the scorer sees the
    same events as direct mode.
    """
    plain_flags = (
        ["--no-extensions", "--no-skills", "--no-context-files"] if plain else []
    )
    return [
        "pi",
        "-p",
        "--mode",
        "json",
        "--no-session",
        *plain_flags,
        "--thinking",
        "high",
        "--model",
        model,
        "-e",
        str(RECORD_EXT),
        sentence,
    ]


def build_pi_mode_args(sentence: str, extra_extensions: tuple[Path, ...] = ()) -> list[str]:
    """Mellum mode: the operator's own profile with the mode extension forced on.

    Superpowers, pi-subagents and the skills catalog load as they do for the
    operator; the mode's before_provider_request hook then sends Mellum the
    worker prompt and only the messages since the mode began. The shipped mode
    runs the guard set itself, so no guards file is passed; the recorder loads
    after the mode so the trace shows what was sent. `extra_extensions`
    (--pi-extension) load alongside — e.g. the NCM verify gate, so the mediation
    reaches Mode.
    """
    args = [
        "pi",
        "-p",
        "--mode",
        "json",
        "--no-session",
        "--model",
        MODEL,
        "-e",
        str(MODE_EXT),
        "-e",
        str(RECORD_EXT),
    ]
    for ext in extra_extensions:
        args += ["-e", str(ext)]
    return [*args, sentence]


def parse_pi_json(stdout: str, with_reentries: bool = False):
    """Final assistant stop reason and visible text from Pi's JSON event stream.

    With ``with_reentries`` also returns how many assistant messages carried
    more than one thinking block: the model re-opened ``<think>`` after a
    close, which gives it a fresh server-side thinking budget each time.
    """
    stop, text, reentries = None, "", 0
    for line in stdout.splitlines():
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") or {}
        if event.get("type") != "message_end" or message.get("role") != "assistant":
            continue
        stop = message.get("stopReason")
        blocks = [b for b in (message.get("content") or []) if isinstance(b, dict)]
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        if sum(b.get("type") == "thinking" for b in blocks) > 1:
            reentries += 1
    if with_reentries:
        return stop, text.strip(), reentries
    return stop, text.strip()


def git(ws: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ws, capture_output=True, text=True, check=False
    ).stdout


def strip_mellum_section(text: str) -> str:
    """Drop each ``## Mellum`` section: its heading through the line before the next
    level-1 or level-2 heading, or to the end of the file. Everything else is kept byte for byte."""
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        if re.match(r"##[ \t]+Mellum[ \t]*$", line.rstrip("\r\n")):
            skipping = True
        elif skipping and re.match(r"#{1,2}[ \t]", line):
            skipping = False
        if not skipping:
            out.append(line)
    return "".join(out)


# A21's `## Mellum` bullets: what the README recommends since v0.1.5 (the test command,
# then the bends the records show), with no `Write only:` list.
LIGHT_SECTION = (
    "- Test command: uv run python -m pytest tests\n"
    "- Do not: install packages or add dependencies; add __init__.py, conftest.py,"
    " pytest.ini or setup.cfg files; weaken tests\n"
)
AGENTCLINIC_FIXTURES = ("agentclinic-p1", "agentclinic-p2", "agentclinic-p3", "agentclinic-p4")


def light_mellum_section(text: str, bullets: str = LIGHT_SECTION) -> str:
    """Replace the body of the ``## Mellum`` section with ``bullets``, framed by blank lines.
    The heading and everything outside the section are kept byte for byte."""
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        if re.match(r"##[ \t]+Mellum[ \t]*$", line.rstrip("\r\n")):
            out.append(line)
            out.append("\n" + bullets)
            skipping = True
            continue
        if skipping and re.match(r"#{1,2}[ \t]", line):
            skipping = False
            out.append("\n")
        if not skipping:
            out.append(line)
    return "".join(out)


def one_file_roadmap() -> str:
    """The four AgentClinic phase specs, verbatim, as one ``specs/roadmap.md`` (as ac-demo keeps
    them): each spec's ``# Phase N`` heading becomes ``## Phase N``."""
    parts = ["# AgentClinic roadmap\n\nFour ordered phases. Each builds on the one before; implement them in order.\n"]
    for spec in sorted((FIXTURES / "agentclinic-p4" / "specs").glob("phase-*.md")):
        parts.append("\n#" + spec.read_text())
    return "".join(parts)


def variant_rung(rung: Rung, roadmap: str) -> Rung:
    """With the one-file roadmap, an AgentClinic rung asks for its phase of specs/roadmap.md."""
    if roadmap != "one-file":
        return rung
    return replace(rung, sentence=f"Implement Phase {rung.number - 5} of specs/roadmap.md")


def prepare_workspace(
    rung: Rung,
    scratch: Path,
    strip_facts_section: bool = False,
    facts_section: str = "fixture",
    roadmap: str = "phase-files",
    acceptance_test: Path | None = None,
) -> Path:
    ws = copy_fixture(rung.fixture, scratch / f"rung{rung.number}")
    agents = ws / "AGENTS.md"
    # All before the baseline commit, so the changed files are the baseline.
    if strip_facts_section and agents.exists():
        agents.write_bytes(strip_mellum_section(agents.read_bytes().decode()).encode())
    if facts_section == "light" and agents.exists():
        agents.write_text(light_mellum_section(agents.read_text()))
    if roadmap == "one-file":
        for spec in (ws / "specs").glob("phase-*.md"):
            spec.unlink()
        (ws / "specs" / "roadmap.md").write_text(one_file_roadmap())
    # Place the mediated acceptance test in the baseline, so the worker must
    # make it pass and the existing_tests_kept scorer freezes it (unweakenable).
    if acceptance_test is not None:
        (ws / "tests").mkdir(exist_ok=True)
        shutil.copy(acceptance_test, ws / "tests" / acceptance_test.name)
    git(ws, "init", "-q")
    git(ws, "add", "-A")
    git(
        ws,
        "-c",
        "user.name=ladder",
        "-c",
        "user.email=ladder@localhost",
        "commit",
        "-qm",
        "baseline",
    )
    if (ws / "pyproject.toml").exists():
        sync = subprocess.run(
            ["uv", "sync", "--offline"],
            cwd=ws,
            capture_output=True,
            timeout=300,
            check=False,
        )
        if sync.returncode:
            raise RuntimeError(
                f"workspace preflight: uv sync failed: {sync.stderr.decode(errors='replace')}"
            )
    return ws


def baseline_index(ws: Path) -> tuple[set[str], dict[str, int]]:
    paths = {p for p in git(ws, "ls-files").split() if p}
    lines = {p: len((ws / p).read_text(errors="replace").splitlines()) for p in paths}
    return paths, lines


def read_events(trace: Path) -> list[dict]:
    if not trace.exists():
        return []
    return [json.loads(line) for line in trace.read_text().splitlines() if line.strip()]


def redispatch_message(test_rel: str, test_output: str) -> str:
    """The task handed to a fresh worker when the frozen acceptance test still fails."""
    # Keep the part that says WHAT failed — the FAILURES section (tracebacks and
    # assertions) — not a blind tail that can be all warnings and the summary.
    marker = test_output.find("FAILURES")
    detail = (test_output[marker:] if marker != -1 else test_output[-1800:])[:1800]
    return (
        f"The acceptance test {test_rel} still fails:\n{detail}\n"
        f"Fix the code and make {test_rel} pass. "
        f"Test command: uv run --offline python -m pytest {test_rel}"
    )


def redispatch_overrides(
    base_overrides: dict | None,
    attempt: int,
    temp_step: float,
    temp_cap: float = 1.0,
) -> dict:
    """Request overrides for re-dispatch ``attempt`` (1-based).

    A greedy (temperature 0) re-dispatch re-runs the same deterministic decode,
    so a retry must change the sampling to explore a different path. We grow the
    temperature by ``temp_step`` per attempt up to ``temp_cap`` and move the seed
    by the attempt number. Past the cap the temperature holds but the seed keeps
    moving, so retries keep diverging (reproducibly) without going hot — high
    temperature corrupts a tool-calling worker's JSON, so the cap stays low.
    """
    out = dict(base_overrides or {})
    base_temp = out.get("temperature") or 0
    base_seed = out.get("seed", 42)
    out["temperature"] = round(min(temp_cap, base_temp + attempt * temp_step), 4)
    out["seed"] = base_seed + attempt
    return out


def redispatch_effort(attempt: int, total: int) -> dict:
    """Effort for attempt ``attempt`` of an effort-ramped run (0 = the initial try).

    Start quick and cheap, escalate only as the frozen test keeps failing: early
    attempts run with thinking off and a small token budget (sub-second on an easy
    fix), the middle with moderate thinking, the last at full thinking and budget.
    The frozen test gates it — a quick slice that passes stops the ladder, so
    compute is spent in proportion to measured difficulty.
    """
    frac = attempt / max(total, 1)
    if frac < 0.34:
        return {"thinking": "off", "max_tokens": 2048}
    if frac < 0.67:
        return {"thinking": "medium", "max_tokens": 8192}
    return {"thinking": "high", "max_tokens": 16384}


def run_acceptance(ws: Path, test_rel: str) -> tuple[int, str]:
    """Run the frozen acceptance test in the workspace: (exit code, combined output)."""
    proc = subprocess.run(
        # -p no:warnings: deprecation warnings drowned the real failure and pushed
        # it out of the message window. --tb=short keeps the assertion, compactly.
        ["uv", "run", "--offline", "python", "-m", "pytest", test_rel, "-q",
         "-p", "no:warnings", "--tb=short"],
        cwd=ws,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def run_once(
    rung: Rung,
    mode: str,
    prof: str,
    repeat: int,
    out: Path,
    deadline: int,
    versions: dict,
    guards: bool,
    plain: bool = False,
    prompt: Path = PROMPT_FILE,
    prompt_mode: str = "replace",
    thinking: str = "high",
    mode_facts: str = "on",
    strip_facts_section: bool = False,
    pi_executable: str = "pi",
    facts_section: str = "fixture",
    roadmap: str = "phase-files",
    provider: str = "omlx",
    base_url: str = "http://127.0.0.1:8001/v1",
    model: str = MODEL,
    context_window: int = 56000,
    request_overrides: dict | None = None,
    acceptance_test: Path | None = None,
    redispatch: int = 0,
    redispatch_temperature_step: float = 0.25,
    redispatch_temperature_cap: float = 0.5,
    effort_ramp: bool = False,
    extra_extensions: tuple[Path, ...] = (),
    pi_agent_dir: Path | None = None,
) -> dict:
    rung = variant_rung(rung, roadmap)
    if acceptance_test is not None:
        rung = replace(
            rung,
            sentence=f"Make tests/{acceptance_test.name} pass. "
            "Verify only with the test command; do not run the app or start "
            "servers — they block. "
            f"Test command: uv run --offline python -m pytest tests/{acceptance_test.name}",
        )
    scratch = Path(tempfile.mkdtemp(prefix="ladder-"))
    ws = prepare_workspace(
        rung,
        scratch,
        strip_facts_section=strip_facts_section,
        facts_section=facts_section,
        roadmap=roadmap,
        acceptance_test=acceptance_test,
    )
    paths, lines = baseline_index(ws)
    trace = scratch / "trace.jsonl"
    if mode == "primary":
        agent_dir = mirror_agent_dir(
            pi_agent_dir or Path.home() / ".pi" / "agent", scratch / "pi-agent", [ws]
        )
        env = child_env(dict(os.environ), str(trace), agent_dir, offline=False)
        args = build_pi_primary_args(rung.sentence, plain, model)
    elif mode == "mode":
        agent_dir = mirror_agent_dir(
            Path.home() / ".pi" / "agent",
            scratch / "pi-agent",
            [ws],
            exclude_packages=("mellum-worker",),
        )
        env = mode_env(
            dict(os.environ), trace, agent_dir, scratch, facts=mode_facts == "on"
        )
        args = build_pi_mode_args(rung.sentence, extra_extensions=extra_extensions)
        guards = True  # the mode always loads the guard extension
    elif mode == "flow":
        provider_name, model_id = model.split("/", 1)
        agent_dir = direct_agent_dir(
            scratch / "pi-agent", prof, base_url,
            provider=provider_name, model_id=model_id,
            context_window=context_window,
        )
        env = child_env(dict(os.environ), str(trace), agent_dir, offline=True)
        env["MELLUM_FLOW_FEED"] = str(scratch / "flow.subfeed")
        env["MELLUM_PHASE"] = "1"  # a rung is one phase; the examiner freezes plan/gate/phase_1.py
        # The flow examiner reads plan/TASK.md (and specs/) to write its acceptance test.
        (ws / "plan").mkdir(exist_ok=True)
        (ws / "plan" / "TASK.md").write_text(rung.sentence + "\n")
        args = build_pi_flow_args(thinking, model, guards)
    else:
        provider_name, model_id = model.split("/", 1)
        # Effort ramp: the initial attempt (0) starts quick — thinking off, small
        # budget — and re-dispatches escalate it (see the loop below).
        init_thinking = thinking
        init_overrides = request_overrides
        if effort_ramp:
            eff0 = redispatch_effort(0, redispatch)
            init_thinking = eff0["thinking"]
            init_overrides = {**(request_overrides or {}), "max_tokens": eff0["max_tokens"]}
        agent_dir = direct_agent_dir(
            scratch / "pi-agent", prof, base_url,
            provider=provider_name, model_id=model_id,
            context_window=context_window,
            request_overrides=init_overrides,
        )
        env = child_env(dict(os.environ), str(trace), agent_dir, offline=True)
        args = build_pi_direct_args(rung.sentence, guards, prompt, prompt_mode,
                                    init_thinking, model, extra_extensions=extra_extensions,
                                    tools=MEDIATED_TOOLS if acceptance_test else TOOLS)
    selected_pi = versions.get("pi_launch") or resolve_pi(pi_executable)
    env, environment = workspace_preflight(ws, rung.fixture, env)
    launch = {"cwd": str(ws), "pi": selected_pi, **environment}
    env["MELLUM_TRACE_RUN_ID"] = str(uuid4())
    argv = [selected_pi["executable"], *args[1:]]
    launch["argv"] = argv
    started = time.time()
    monotonic_started = time.monotonic()

    def _launch(launch_argv, launch_env=env):
        try:
            proc = subprocess.run(
                launch_argv,
                cwd=ws,
                env=launch_env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=deadline,
                check=False,
            )
            return proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as error:
            captured = error.stdout or b""
            out = (
                captured.decode(errors="replace")
                if isinstance(captured, bytes)
                else str(captured)
            )
            captured_stderr = error.stderr or b""
            err = (
                captured_stderr.decode(errors="replace")
                if isinstance(captured_stderr, bytes)
                else str(captured_stderr)
            )
            return None, out, err, True

    returncode, process_stdout, stderr, deadline_hit = _launch(argv)
    stdout = process_stdout + ("\n[stderr]\n" + stderr if stderr else "")
    # Re-dispatch (direct + mediated only): re-run the frozen test and, on failure,
    # hand the failure to a fresh worker on the same workspace, up to `redispatch` times.
    redispatch_attempts = 0
    redispatch_schedule: list[dict] = []
    if acceptance_test is not None and redispatch and mode == "direct":
        test_rel = f"tests/{acceptance_test.name}"
        for _ in range(redispatch):
            # A timed-out attempt is still a failing frozen test, so retry on it
            # too — a fresh, hotter worker on the same (cumulative) workspace,
            # not a give-up. Keep the per-attempt --deadline small to bound cost.
            code, acc_out = run_acceptance(ws, test_rel)
            if code == 0:
                break
            redispatch_attempts += 1
            # Grow temperature + move the seed so the retry explores a new path
            # instead of re-running the same greedy decode. Rebuild the agent dir
            # (it bakes the request params) and point Pi at it for this attempt.
            overrides = redispatch_overrides(
                request_overrides,
                redispatch_attempts,
                redispatch_temperature_step,
                temp_cap=redispatch_temperature_cap,
            )
            entry = {
                "attempt": redispatch_attempts,
                "temperature": overrides["temperature"],
                "seed": overrides["seed"],
            }
            # Effort ramp: escalate thinking + token budget as the test keeps failing.
            re_thinking = thinking
            if effort_ramp:
                eff = redispatch_effort(redispatch_attempts, redispatch)
                re_thinking = eff["thinking"]
                overrides["max_tokens"] = eff["max_tokens"]
                entry["thinking"] = eff["thinking"]
                entry["max_tokens"] = eff["max_tokens"]
            redispatch_schedule.append(entry)
            re_agent_dir = direct_agent_dir(
                scratch / f"pi-agent-redispatch-{redispatch_attempts}",
                prof, base_url,
                provider=provider_name, model_id=model_id,
                context_window=context_window,
                request_overrides=overrides,
            )
            re_env = child_env(dict(os.environ), str(trace), re_agent_dir, offline=True)
            reargs = build_pi_direct_args(
                redispatch_message(test_rel, acc_out),
                guards,
                prompt,
                prompt_mode,
                re_thinking,
                model,
                extra_extensions=extra_extensions,
                tools=MEDIATED_TOOLS,
            )
            returncode, process_stdout, stderr, deadline_hit = _launch(
                [selected_pi["executable"], *reargs[1:]], re_env
            )
            stdout += "\n[re-dispatch]\n" + process_stdout + (
                "\n[stderr]\n" + stderr if stderr else ""
            )
    wall = time.time() - started
    # Servers Mellum started with `&` outlive Pi; stop them before staging the
    # workspace so they neither hold ports for later runs nor write after it.
    leftovers = stop_leftovers(ws)
    if mode == "flow":
        # plan/ is the flow harness's own bookkeeping (TASK/TODO/REVIEW + the frozen gate), not
        # the graded solution. Move it out of the workspace so it does not trip the write-list
        # check; the materialized acceptance tests under tests/ stay. Kept in scratch for debugging.
        plan_dir = ws / "plan"
        if plan_dir.exists():
            shutil.move(str(plan_dir), str(scratch / "plan"))
    stop_reason, final_text, thinking_reentries = parse_pi_json(
        stdout, with_reentries=True
    )
    elapsed_ms = (time.monotonic() - monotonic_started) * 1000
    events, trace_issues = load_trace(trace)
    telemetry = summarize_trace(events, trace_issues, stderr, selected_pi)
    git(ws, "add", "-A")
    record = {
        "rung": rung.number,
        "repeat": repeat,
        "profile": prof,
        "mode": mode,
        "backend": {
            "provider": provider,
            "base_url": base_url,
            "model": model,
        } if mode in ("direct", "flow") else None,
        "harness": "pi",
        "plain": plain,
        "guards": guards,
        "mode_facts": mode_facts if mode == "mode" else None,
        "strip_facts_section": strip_facts_section,
        "facts_section": facts_section,
        "roadmap": roadmap,
        "leftover_processes": leftovers,
        "guards_env": json.loads(os.environ["MELLUM_GUARDS"])
        if os.environ.get("MELLUM_GUARDS")
        else None,
        "prompt_version": prompt_version(prompt) if mode == "direct" else None,
        "prompt_file": (
            str(prompt.relative_to(REPO_ROOT))
            if prompt.is_relative_to(REPO_ROOT)
            else str(prompt)
        )
        if mode == "direct"
        else None,
        "prompt_mode": prompt_mode if mode == "direct" else None,
        "thinking": thinking if mode == "direct" else None,
        "request_overrides": request_overrides if mode == "direct" else None,
        "acceptance_test": acceptance_test.name
        if (acceptance_test is not None and mode == "direct")
        else None,
        "redispatch_attempts": redispatch_attempts if mode == "direct" else None,
        "redispatch_temperature_step": redispatch_temperature_step
        if (redispatch and mode == "direct")
        else None,
        "redispatch_temperature_cap": redispatch_temperature_cap
        if (redispatch and mode == "direct")
        else None,
        "effort_ramp": effort_ramp if (redispatch and mode == "direct") else None,
        "redispatch_schedule": redispatch_schedule if mode == "direct" else None,
        "versions": versions,
        "launch": launch,
        "telemetry": telemetry,
        "process": {
            "exitCode": returncode
            if returncode is not None and returncode >= 0
            else None,
            "signal": -returncode
            if returncode is not None and returncode < 0
            else None,
            "deadlineHit": deadline_hit,
            "elapsedMs": elapsed_ms,
            **stdout_settlement(process_stdout),
        },
        "sentence": rung.sentence,
        "started": started,
        "wall_seconds_untrusted": round(wall, 1),
        "deadline_hit": deadline_hit,
        "stop_reason": stop_reason,
        "final_text_chars": len(final_text),
        "thinking_reentries": thinking_reentries,
        "final_text_is": "worker",
        "baseline_lines": lines,
        "check": asdict(rung.check(ws, FIXTURES / rung.fixture)),
        "score": score(events, paths, lines).as_row(),
        "diff_stat": git(ws, "diff", "--cached", "--stat"),
        "files_created": [
            p
            for p in git(
                ws, "diff", "--cached", "--name-only", "--diff-filter=A"
            ).split()
            if p
        ],
        "workspace": str(ws),
        **worker_provenance(),
    }
    variant = f"{'-guards' if guards else ''}{'-plain' if plain else ''}"
    run_dir = out / f"rung{rung.number}-{prof}-{mode}{variant}-r{repeat}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(json.dumps(record, indent=2, default=str))
    if trace.exists():
        shutil.copy(trace, run_dir / "trace.jsonl")
    (run_dir / "stdout.txt").write_text(stdout)
    (run_dir / "final.md").write_text(final_text)
    (run_dir / "diff.patch").write_text(git(ws, "diff", "--cached"))
    return record


def table_row(record: dict) -> str:
    s, c = record["score"], record["check"]
    result = "pass" if c["passed"] else "FAIL"
    return (
        f"| {record['rung']} | {record['profile']}{'+guards' if record['guards'] else ''} | {record['mode']} | "
        f"{record['repeat']} | {result} | {c['tests_unchanged']} | {s['requests']} | {s['tool_errors']} | "
        f"{s['edit_anchor_failures']} | {s['noop_edits']} | {s['write_existing']} | {s['write_shrink']} | {s['bash_file_mutations']} | "
        f"{s['max_identical_streak']} | {s['largest_prompt_chars']} | {s.get('nudges', 0)} | {record['stop_reason']} | {record['final_text_chars']} | {record.get('thinking_reentries', '')} | {record['deadline_hit']} | "
        f"{record['wall_seconds_untrusted']} |\n"
    )


def install_signal_handlers() -> None:
    """SIGTERM/SIGHUP exit through SystemExit so the profile restore in `finally` still runs."""

    def exit_on_signal(signum, _frame):
        raise SystemExit(128 + signum)

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, exit_on_signal)


def tool_version(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=False
        )
    except OSError, subprocess.TimeoutExpired:
        return "unknown"
    lines = [line.strip() for line in (result.stdout + result.stderr).splitlines()
             if line.strip()]
    return lines[0] if lines else ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pi-executable",
        default="pi",
        help="Pi executable for version checks and all parent/child launches",
    )
    parser.add_argument(
        "--mode",
        choices=["direct", "primary", "mode", "flow"],
        default="direct",
    )
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--rung", type=int, action="append", required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--deadline", type=int, default=600)
    parser.add_argument("--guards", action="store_true")
    parser.add_argument(
        "--plain",
        action="store_true",
        help="primary mode: Pi's own prompt and tools with no extensions, skills or context files (the plain baseline)",
    )
    parser.add_argument(
        "--pi-agent-dir",
        type=Path,
        default=None,
        help="primary mode: the Pi agent directory to mirror (default ~/.pi/agent); "
             "a pinned profile keeps the operator's own configuration out of a baseline",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=PROMPT_FILE,
        help="direct mode: worker prompt file (default prompts/mellum-worker.md)",
    )
    parser.add_argument(
        "--prompt-mode",
        choices=["append", "replace"],
        default="replace",
        help="direct mode: replace Pi's base prompt (the shipped agent file; default) or append to it (phases 0-2)",
    )
    parser.add_argument(
        "--thinking", default="high", help="direct mode: Pi thinking level"
    )
    parser.add_argument(
        "--mode-facts",
        choices=["on", "off"],
        default="on",
        help="mode mode: off sets MELLUM_MODE_FACTS=0 (Mode without the project-facts block)",
    )
    parser.add_argument(
        "--strip-facts-section",
        action="store_true",
        help="remove the `## Mellum` section from the workspace's AGENTS.md before the run (fallback-only condition)",
    )
    parser.add_argument(
        "--facts-section",
        choices=["fixture", "light"],
        default="fixture",
        help="AgentClinic rungs: light replaces the `## Mellum` bullets with the README's (no Write only)",
    )
    parser.add_argument(
        "--roadmap",
        choices=["phase-files", "one-file"],
        default="phase-files",
        help="AgentClinic rungs: one-file joins the phase specs into specs/roadmap.md and asks for Phase N of it",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--omlx", default="http://127.0.0.1:8001")
    parser.add_argument("--provider", default="omlx",
                        help="model provider the direct profile writes (default omlx)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001/v1",
                        help="the provider's OpenAI-compatible base URL")
    parser.add_argument("--model", default=MODEL,
                        help="provider/model, e.g. llamacpp/Mellum2.1-12B-A2.5B-Thinking")
    parser.add_argument("--context-window", type=int, default=56000,
                        help="the model's context window in the direct profile")
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="direct mode: override the request temperature (default greedy 0). The ladder is greedy by design, so this is for sampling screens, not measured claims",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="direct mode: override the request top_p (default 1)",
    )
    parser.add_argument(
        "--acceptance-test",
        type=Path,
        default=None,
        help="direct or mode: a hand-written failing test placed in the workspace's tests/ before the baseline; the task becomes 'make tests/<name> pass' and the existing-tests scorer freezes it (the mediated-test screen, M.11)",
    )
    parser.add_argument(
        "--redispatch",
        type=int,
        default=0,
        help="direct mode, with --acceptance-test: after a run, re-run the frozen test and, on failure, hand the failure to a fresh worker on the same workspace, up to N times (the verify-and-re-hand loop)",
    )
    parser.add_argument(
        "--redispatch-temperature-step",
        type=float,
        default=0.25,
        help="with --redispatch: how much to grow the request temperature per retry (the seed moves with the attempt regardless), so a retry explores a new path instead of re-running the same greedy decode. 0 keeps every retry greedy. Unmeasured (conjecture)",
    )
    parser.add_argument(
        "--redispatch-temperature-cap",
        type=float,
        default=0.5,
        help="with --redispatch: ceiling for the temperature ramp. Past it the temperature holds and only the seed moves, so retries keep diverging without going hot (high temperature corrupts the worker's JSON tool calls)",
    )
    parser.add_argument(
        "--effort-ramp",
        action="store_true",
        help="with --redispatch: start quick (thinking off, small token budget) and escalate thinking off->medium->high and max_tokens 2k->16k as the frozen test keeps failing. Opt-in; on a known-hard rung a fixed high budget was faster (v7 ablation)",
    )
    parser.add_argument(
        "--pi-extension",
        action="append",
        default=[],
        help="direct or mode: an extra Pi extension to load with -e (repeatable), e.g. extensions/mellum-ncm.ts, so an extension can be measured without shipping it",
    )
    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Cross-argument constraints, split out of main() so they are unit-testable."""
    if (args.facts_section != "fixture" or args.roadmap != "phase-files") and any(
        RUNGS[n].fixture not in AGENTCLINIC_FIXTURES for n in args.rung
    ):
        parser.error("--facts-section and --roadmap apply only to the AgentClinic rungs 6-9")
    direct_only = {
        "--temperature": args.temperature is not None,
        "--top-p": args.top_p is not None,
    }
    if args.mode != "direct" and any(direct_only.values()):
        used = ", ".join(name for name, on in direct_only.items() if on)
        parser.error(f"{used} apply only to --mode direct")
    if args.acceptance_test is not None and not (
        args.acceptance_test.name.startswith("test_")
        and args.acceptance_test.suffix == ".py"
    ):
        parser.error(
            "--acceptance-test must be a pytest file named test_*.py, or "
            "`pytest tests` will not collect it and the worker never sees it"
        )
    if args.redispatch and args.acceptance_test is None:
        parser.error("--redispatch requires --acceptance-test")
    # The verify-and-re-dispatch loop and its effort ramp are implemented for direct
    # mode only; Mellum Mode can be handed the frozen test but not yet re-dispatched.
    if (args.redispatch or args.effort_ramp) and args.mode != "direct":
        parser.error("--redispatch and --effort-ramp apply only to --mode direct")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    request_overrides = {
        key: value
        for key, value in (("temperature", args.temperature), ("top_p", args.top_p))
        if value is not None
    } or None
    # Absolute, so the record's prompt_file is relative to REPO_ROOT; run from ladder/,
    # `prompts/ablation/v4a-no-procedure.md` is ladder/prompts/ablation/....
    args.prompt = args.prompt.resolve()
    install_signal_handlers()

    selected_pi = resolve_pi(args.pi_executable)
    versions = {"pi": selected_pi["version"], "pi_launch": selected_pi,
                "request_overrides": request_overrides}
    args.out.mkdir(parents=True, exist_ok=True)
    table = args.out / "table.md"
    if not table.exists():
        table.write_text(HEADER)
    if args.provider == "omlx":
        client = AdminClient(args.omlx)
        versions["omlx"] = tool_version(["omlx", "--version"])
        settings_path = Path.home() / ".omlx" / "model_settings.json"
        context = profile(client, MODEL_ID, args.profile, settings_path)
    else:
        versions["backend"] = tool_version(["llama-server", "--version"])
        versions["server"] = server_identity(args.base_url)
        versions["gpu"] = gpu_identity()
        context = nullcontext({})
    with context as live:
        versions["model_settings"] = {
            k: live.get(k)
            for k in (
                "max_tokens",
                "thinking_budget_tokens",
                "presence_penalty",
                "max_tool_result_tokens",
            )
        }
        for number in args.rung:
            for repeat in range(1, args.repeat + 1):
                record = run_once(
                    RUNGS[number],
                    args.mode,
                    args.profile,
                    repeat,
                    args.out,
                    args.deadline,
                    versions,
                    args.guards,
                    args.plain,
                    args.prompt,
                    args.prompt_mode,
                    args.thinking,
                    args.mode_facts,
                    args.strip_facts_section,
                    pi_executable=selected_pi["executable"],
                    facts_section=args.facts_section,
                    roadmap=args.roadmap,
                    provider=args.provider,
                    base_url=args.base_url,
                    model=args.model,
                    context_window=args.context_window,
                    request_overrides=request_overrides,
                    acceptance_test=args.acceptance_test,
                    redispatch=args.redispatch,
                    redispatch_temperature_step=args.redispatch_temperature_step,
                    redispatch_temperature_cap=args.redispatch_temperature_cap,
                    effort_ramp=args.effort_ramp,
                    extra_extensions=tuple(Path(p) for p in args.pi_extension),
                    pi_agent_dir=args.pi_agent_dir,
                )
                row = table_row(record)
                with table.open("a") as stream:
                    stream.write(row)
                if (args.mode == "direct" and args.provider == "omlx"
                        and not args.effort_ramp
                        and record["score"]["effective_params"]):
                    check_effective_params(
                        record["score"]["effective_params"],
                        args.profile,
                        request_overrides,
                    )
                print(row, end="", flush=True)


if __name__ == "__main__":
    main()
