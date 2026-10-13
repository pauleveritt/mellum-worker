"""Run ladder rungs against the Mellum worker and score the evidence.

Direct mode launches ``pi -p`` in the recovery report's clean profile: no
extensions, skills, or context files; the worker prompt in place of Pi's; the
bundle's record extension capturing every provider request and tool event.

    uv run python -m ladder.run_ladder --profile baseline --rung 1 --repeat 3 --out ../docs/ladder/phase0-baseline
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
from dataclasses import asdict, replace
from pathlib import Path
from uuid import uuid4

from .omlx_profiles import PROFILES, AdminClient, check_effective_params, profile
from .pi_launch import resolve_pi, subagents_revision, workspace_preflight
from .pi_profile import (
    LADDER_ROOT,
    REPO_ROOT,
    direct_agent_dir,
    mirror_agent_dir,
    prepare_pi_workspace,
)
from .pi_trace import load_trace, stdout_settlement, summarize_trace
from .leftovers import stop_leftovers
from .rungs import FIXTURES, RUNGS, Rung, copy_fixture
from .score import score

log = logging.getLogger(__name__)
PROMPT_FILE = REPO_ROOT / "prompts" / "mellum-worker.md"
RECORD_EXT = LADDER_ROOT / "ladder" / "record-pi.js"
MODE_EXT = REPO_ROOT / "extensions" / "mellum-mode.ts"
GUARDS_EXT = REPO_ROOT / "extensions" / "mellum-guards.ts"
MODEL = "omlx/Mellum2.1-12B-A2.5B-Thinking-6bit"
MODEL_ID = MODEL.split("/", 1)[1]
TOOLS = "read,grep,find,ls,bash,edit,write"


def prompt_version(prompt: Path) -> str:
    """The version named in the prompt file's first-line marker, else its stem."""
    first = prompt.read_text().splitlines()[0] if prompt.exists() else ""
    found = re.search(r"prompt (v\w+)", first)
    return found.group(1) if found else prompt.stem


PARENT_PROMPT = "Use mellum-worker to do this: {sentence}"

HEADER = (
    "| rung | profile | mode | rep | result | tests_unchanged | requests | tool_errors | anchor_fail | "
    "noop_edit | write_existing | write_shrink | bash_mut | max_streak | largest_prompt_chars | nudges | stop | final_chars | reentries | deadline | wall_s (untrusted) | deleg | brief_chars |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
)


def build_pi_direct_args(
    sentence: str,
    guards: bool = False,
    prompt: Path = PROMPT_FILE,
    prompt_mode: str = "replace",
    thinking: str = "high",
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
        MODEL,
        "--tools",
        TOOLS,
        *prompt_args,
        "-e",
        str(RECORD_EXT),
    ]
    if guards:
        args += ["-e", str(GUARDS_EXT)]
    return [*args, sentence]


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


def build_pi_delegated_args(sentence: str) -> list[str]:
    """The parent: its normal profile (model, Superpowers, pi-subagents), addressed to the worker."""
    return [
        "pi",
        "-p",
        "--mode",
        "json",
        "--no-session",
        "--thinking",
        "high",
        PARENT_PROMPT.format(sentence=sentence),
    ]


def build_pi_primary_args(sentence: str, plain: bool = False) -> list[str]:
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
        MODEL,
        "-e",
        str(RECORD_EXT),
        sentence,
    ]


def build_pi_mode_args(sentence: str) -> list[str]:
    """Mellum mode: the operator's own profile with the mode extension forced on.

    Superpowers, pi-subagents and the skills catalog load as they do for the
    operator; the mode's before_provider_request hook then sends Mellum the
    worker prompt and only the messages since the mode began. The shipped mode
    runs the guard set itself, so no guards file is passed; the recorder loads
    after the mode so the trace shows what was sent.
    """
    return [
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
        sentence,
    ]


def parse_parent_json(stdout: str) -> dict:
    """What the parent did: whether it launched the worker, the brief it wrote, its final text."""
    brief, final, messages, calls = "", "", 0, 0
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
        messages += 1
        blocks = [b for b in (message.get("content") or []) if isinstance(b, dict)]
        final = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        for block in blocks:
            if block.get("type") == "toolCall" and block.get("name") == "subagent":
                arguments = block.get("arguments") or {}
                if arguments.get("agent") == "mellum-worker" and arguments.get("task"):
                    calls += 1
                    brief = brief or str(arguments["task"])
    return {
        "delegated": calls > 0,
        "brief": brief,
        "parent_final_chars": len(final.strip()),
        "parent_messages": messages,
        "subagent_calls": calls,
    }


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
# M.11: a developer's test per phase, handed to Mellum as the done criterion (only phase 4 so far).
GIVEN_TESTS = FIXTURES / "agentclinic-given"


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


def given_test_name(rung: Rung) -> str:
    """The given test's path inside the workspace, by phase."""
    return f"tests/test_phase{rung.number - 5}.py"


def variant_rung(rung: Rung, roadmap: str, given_test: bool = False) -> Rung:
    """With the one-file roadmap, an AgentClinic rung asks for its phase of specs/roadmap.md;
    with a given test, the sentence also names the test file to make pass (M.11)."""
    if roadmap == "one-file":
        rung = replace(rung, sentence=f"Implement Phase {rung.number - 5} of specs/roadmap.md")
    if given_test:
        rung = replace(rung, sentence=f"{rung.sentence}; make {given_test_name(rung)} pass")
    return rung


def prepare_workspace(
    rung: Rung,
    scratch: Path,
    strip_facts_section: bool = False,
    facts_section: str = "fixture",
    roadmap: str = "phase-files",
    given_test: bool = False,
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
    if given_test:
        source = GIVEN_TESTS / Path(given_test_name(rung)).name
        if not source.exists():
            raise FileNotFoundError(f"no given test for rung {rung.number}: {source}")
        (ws / "tests").mkdir(exist_ok=True)
        shutil.copy(source, ws / given_test_name(rung))
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
    subagents_config: dict | None = None,
    mode_facts: str = "on",
    strip_facts_section: bool = False,
    pi_executable: str = "pi",
    facts_section: str = "fixture",
    roadmap: str = "phase-files",
    given_test: bool = False,
) -> dict:
    rung = variant_rung(rung, roadmap, given_test)
    scratch = Path(tempfile.mkdtemp(prefix="ladder-"))
    ws = prepare_workspace(
        rung,
        scratch,
        strip_facts_section=strip_facts_section,
        facts_section=facts_section,
        roadmap=roadmap,
        given_test=given_test,
    )
    paths, lines = baseline_index(ws)
    trace = scratch / "trace.jsonl"
    if mode == "delegated":
        prepare_pi_workspace(ws, RECORD_EXT)
        agent_dir = mirror_agent_dir(
            Path.home() / ".pi" / "agent",
            scratch / "pi-agent",
            [ws],
            subagents_config=subagents_config,
        )
        env = child_env(dict(os.environ), str(trace), agent_dir)
        args = build_pi_delegated_args(rung.sentence)
    elif mode == "primary":
        agent_dir = mirror_agent_dir(
            Path.home() / ".pi" / "agent", scratch / "pi-agent", [ws]
        )
        env = child_env(dict(os.environ), str(trace), agent_dir, offline=False)
        args = build_pi_primary_args(rung.sentence, plain)
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
        args = build_pi_mode_args(rung.sentence)
        guards = True  # the mode always loads the guard extension
    else:
        agent_dir = direct_agent_dir(scratch / "pi-agent", prof)
        env = child_env(dict(os.environ), str(trace), agent_dir, offline=True)
        args = build_pi_direct_args(rung.sentence, guards, prompt, prompt_mode, thinking)
    selected_pi = versions.get("pi_launch") or resolve_pi(pi_executable)
    env, environment = workspace_preflight(ws, rung.fixture, env)
    if mode == "delegated":
        env["PI_SUBAGENT_PI_BINARY"] = selected_pi["executable"]
    launch = {"cwd": str(ws), "pi": selected_pi, **environment}
    if mode == "delegated":
        launch["pi_subagents_revision"] = subagents_revision(agent_dir)
    env["MELLUM_TRACE_RUN_ID"] = str(uuid4())
    argv = [selected_pi["executable"], *args[1:]]
    launch["argv"] = argv
    started = time.time()
    monotonic_started = time.monotonic()
    returncode = None
    process_stdout = ""
    stderr = ""
    deadline_hit = False
    stdout = ""
    try:
        proc = subprocess.run(
            argv,
            cwd=ws,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=deadline,
            check=False,
        )
        returncode = proc.returncode
        process_stdout = proc.stdout
        stderr = proc.stderr
        stdout = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
    except subprocess.TimeoutExpired as error:
        deadline_hit = True
        captured = error.stdout or b""
        process_stdout = (
            captured.decode(errors="replace")
            if isinstance(captured, bytes)
            else str(captured)
        )
        stdout = process_stdout
        captured_stderr = error.stderr or b""
        stderr = (
            captured_stderr.decode(errors="replace")
            if isinstance(captured_stderr, bytes)
            else str(captured_stderr)
        )
        if captured_stderr:
            stdout += "\n[stderr]\n" + stderr
    wall = time.time() - started
    # Servers Mellum started with `&` outlive Pi; stop them before staging the
    # workspace so they neither hold ports for later runs nor write after it.
    leftovers = stop_leftovers(ws)
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
        "harness": "pi",
        "plain": plain,
        "guards": guards,
        "subagents_config": subagents_config if mode == "delegated" else None,
        "mode_facts": mode_facts if mode == "mode" else None,
        "strip_facts_section": strip_facts_section,
        "facts_section": facts_section,
        "roadmap": roadmap,
        "given_test": given_test_name(rung) if given_test else None,
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
        "final_text_is": "parent" if mode == "delegated" else "worker",
        "parent": parse_parent_json(stdout) if mode == "delegated" else None,
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
    if record["parent"]:
        (run_dir / "brief.md").write_text(record["parent"]["brief"])
    return record


def table_row(record: dict) -> str:
    s, c = record["score"], record["check"]
    result = "pass" if c["passed"] else "FAIL"
    parent = record.get("parent") or {}
    deleg = parent.get("delegated", "") if parent else ""
    brief_chars = len(parent.get("brief", "")) if parent else ""
    return (
        f"| {record['rung']} | {record['profile']}{'+guards' if record['guards'] else ''} | {record['mode']} | "
        f"{record['repeat']} | {result} | {c['tests_unchanged']} | {s['requests']} | {s['tool_errors']} | "
        f"{s['edit_anchor_failures']} | {s['noop_edits']} | {s['write_existing']} | {s['write_shrink']} | {s['bash_file_mutations']} | "
        f"{s['max_identical_streak']} | {s['largest_prompt_chars']} | {s.get('nudges', 0)} | {record['stop_reason']} | {record['final_text_chars']} | {record.get('thinking_reentries', '')} | {record['deadline_hit']} | "
        f"{record['wall_seconds_untrusted']} | {deleg} | {brief_chars} |\n"
    )


def install_signal_handlers() -> None:
    """SIGTERM/SIGHUP exit through SystemExit so the profile restore in `finally` still runs."""

    def exit_on_signal(signum, _frame):
        raise SystemExit(128 + signum)

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, exit_on_signal)


def tool_version(cmd: list[str]) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=False
        ).stdout.strip()
    except OSError, subprocess.TimeoutExpired:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pi-executable",
        default="pi",
        help="Pi executable for version checks and all parent/child launches",
    )
    parser.add_argument(
        "--mode",
        choices=["direct", "delegated", "primary", "mode"],
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
        "--subagents-config",
        type=json.loads,
        default=None,
        help="delegated mode: JSON that replaces pi-subagents' config.json in the mirrored agent dir",
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
    parser.add_argument(
        "--given-test",
        action="store_true",
        help="AgentClinic rungs: copy fixtures/agentclinic-given/test_phase<N>.py into tests/ before the baseline and append '; make tests/test_phase<N>.py pass' to the task (M.11)",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--omlx", default="http://127.0.0.1:8001")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if (
        args.facts_section != "fixture" or args.roadmap != "phase-files" or args.given_test
    ) and any(RUNGS[n].fixture not in AGENTCLINIC_FIXTURES for n in args.rung):
        parser.error("--facts-section, --roadmap and --given-test apply only to the AgentClinic rungs 6-9")
    # Absolute, so the record's prompt_file is relative to REPO_ROOT; run from ladder/,
    # `prompts/ablation/v4a-no-procedure.md` is ladder/prompts/ablation/....
    args.prompt = args.prompt.resolve()
    install_signal_handlers()

    client = AdminClient(args.omlx)
    selected_pi = resolve_pi(args.pi_executable)
    versions = {
        "pi": selected_pi["version"],
        "pi_launch": selected_pi,
        "omlx": tool_version(["omlx", "--version"]),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    table = args.out / "table.md"
    if not table.exists():
        table.write_text(HEADER)
    settings_path = Path.home() / ".omlx" / "model_settings.json"
    with profile(client, MODEL_ID, args.profile, settings_path) as live:
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
                    args.subagents_config,
                    args.mode_facts,
                    args.strip_facts_section,
                    pi_executable=selected_pi["executable"],
                    facts_section=args.facts_section,
                    roadmap=args.roadmap,
                    given_test=args.given_test,
                )
                row = table_row(record)
                with table.open("a") as stream:
                    stream.write(row)
                if args.mode == "direct" and record["score"]["effective_params"]:
                    check_effective_params(
                        record["score"]["effective_params"], args.profile
                    )
                print(row, end="", flush=True)


if __name__ == "__main__":
    main()
