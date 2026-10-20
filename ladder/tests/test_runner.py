import json
from pathlib import Path

import pytest

from ladder.pi_profile import REPO_ROOT
from ladder.run_ladder import (
    GUARDS_EXT,
    MODE_EXT,
    PROMPT_FILE,
    RECORD_EXT,
    build_pi_direct_args,
    build_pi_mode_args,
)


@pytest.fixture(autouse=True)
def controlled_launch_boundary(monkeypatch):
    from ladder import run_ladder

    monkeypatch.setattr(
        run_ladder,
        "resolve_pi",
        lambda executable: {"executable": executable, "version": "test"},
    )
    monkeypatch.setattr(
        run_ladder,
        "workspace_preflight",
        lambda ws, fixture, env: (env, {"node": None, "python": None}),
    )


def test_direct_args_are_the_clean_profile():
    args = build_pi_direct_args("fix it", prompt_mode="append")
    for flag in (
        "-p",
        "--no-extensions",
        "--no-skills",
        "--no-context-files",
        "--no-session",
    ):
        assert flag in args
    assert args[args.index("--tools") + 1] == "read,ls,bash,edit,write"
    assert args[args.index("--append-system-prompt") + 1] == str(PROMPT_FILE)
    assert args[-1] == "fix it"


def test_parse_pi_json_extracts_final_stop_and_text():
    from ladder.run_ladder import parse_pi_json

    lines = [
        '{"type":"message_end","message":{"role":"user","content":"hi"}}',
        '{"type":"message_end","message":{"role":"assistant","stopReason":"toolUse","content":[{"type":"toolCall","name":"read"}]}}',
        '{"type":"message_end","message":{"role":"assistant","stopReason":"length","content":[{"type":"thinking","thinking":"..."}]}}',
        '{"type":"agent_end"}',
    ]
    stop, text = parse_pi_json("\n".join(lines))
    assert stop == "length" and text == ""
    stop, text = parse_pi_json(
        '{"type":"message_end","message":{"role":"assistant","stopReason":"stop","content":[{"type":"text","text":"Done."}]}}'
    )
    assert stop == "stop" and text == "Done."


def test_direct_env_drops_virtual_env():
    from ladder.run_ladder import child_env

    env = child_env({"VIRTUAL_ENV": "/x", "PATH": "/bin"}, "/tmp/t.jsonl")
    assert "VIRTUAL_ENV" not in env and env["MELLUM_TRACE_FILE"] == "/tmp/t.jsonl"


def test_parse_pi_json_counts_thinking_reentries():
    from ladder.run_ladder import parse_pi_json

    two_blocks = (
        '{"type":"message_end","message":{"role":"assistant","stopReason":"toolUse","content":'
        '[{"type":"thinking","thinking":"a"},{"type":"text","text":"b"},{"type":"thinking","thinking":"c"}]}}'
    )
    one_block = (
        '{"type":"message_end","message":{"role":"assistant","stopReason":"stop","content":'
        '[{"type":"thinking","thinking":"a"},{"type":"text","text":"Done."}]}}'
    )
    stop, text, reentries = parse_pi_json(
        f"{two_blocks}\n{one_block}", with_reentries=True
    )
    assert stop == "stop" and text == "Done." and reentries == 1


def test_run_once_never_inherits_stdin(monkeypatch, tmp_path):
    """Pi blocks forever on a non-TTY stdin that never reaches EOF; the worker must get DEVNULL."""
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    seen = {}

    def fake_run(args, **kwargs):
        seen.update(kwargs)
        return sp.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(run_ladder.subprocess, "run", fake_run)
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(rung, "direct", "baseline", 1, tmp_path / "out", 5, {}, False)
    assert seen.get("stdin") is sp.DEVNULL


def test_run_record_carries_the_guards_override(monkeypatch, tmp_path):
    """A run under MELLUM_GUARDS must say so in run.json, or the record lies about which guards ran."""
    import json
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess,
        "run",
        lambda args, **kw: sp.CompletedProcess(args, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setenv("MELLUM_GUARDS", '{"emptyFinalNudge":3,"loopBreaker":true}')
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(rung, "direct", "baseline", 1, tmp_path / "out", 5, {}, True)
    record = json.loads(
        (tmp_path / "out" / "rung1-baseline-direct-guards-r1" / "run.json").read_text()
    )
    assert record["guards_env"] == {"emptyFinalNudge": 3, "loopBreaker": True}


def test_signal_handlers_raise_system_exit_so_finally_blocks_run():
    import signal

    from ladder.run_ladder import install_signal_handlers

    install_signal_handlers()
    for sig in (signal.SIGTERM, signal.SIGHUP):
        handler = signal.getsignal(sig)
        import pytest

        with pytest.raises(SystemExit):
            handler(sig, None)


def test_parse_parent_json_extracts_the_brief():
    from ladder.run_ladder import parse_parent_json

    lines = [
        '{"type":"message_end","message":{"role":"assistant","stopReason":"toolUse","content":[{"type":"toolCall","name":"subagent","arguments":{"agent":"mellum-worker","task":"Fix totalCents in calculator.js; run node --test"}}]}}',
        '{"type":"message_end","message":{"role":"assistant","stopReason":"stop","content":[{"type":"text","text":"Done: 3/3 tests pass."}]}}',
    ]
    parent = parse_parent_json("\n".join(lines))
    assert parent["delegated"] is True
    assert parent["brief"] == "Fix totalCents in calculator.js; run node --test"
    assert parent["parent_final_chars"] == len("Done: 3/3 tests pass.")
    assert parent["subagent_calls"] == 1


def test_parse_parent_json_reports_no_delegation():
    from ladder.run_ladder import parse_parent_json

    line = (
        '{"type":"message_end","message":{"role":"assistant","stopReason":"stop","content":'
        '[{"type":"toolCall","name":"edit","arguments":{}},{"type":"text","text":"I fixed it myself."}]}}'
    )
    parent = parse_parent_json(line)
    assert (
        parent["delegated"] is False
        and parent["brief"] == ""
        and parent["subagent_calls"] == 0
    )


def test_delegated_args_address_the_worker_by_name():
    from ladder.run_ladder import build_pi_delegated_args

    args = build_pi_delegated_args("fix it")
    assert (
        args[:2] == ["pi", "-p"]
        and "--no-session" in args
        and "--no-extensions" not in args
    )
    assert args[-1] == "Use mellum-worker to do this: fix it"


def test_direct_env_is_offline_and_uses_the_profile_agent_dir():
    from ladder.run_ladder import child_env

    env = child_env(
        {"PATH": "/bin"},
        "/tmp/t.jsonl",
        agent_dir=__import__("pathlib").Path("/tmp/agent"),
        offline=True,
    )
    assert env["PI_OFFLINE"] == "1" and env["PI_CODING_AGENT_DIR"] == "/tmp/agent"


def test_primary_args_run_mellum_as_the_parent_with_the_recorder():
    from ladder.run_ladder import MODEL, RECORD_EXT, build_pi_primary_args

    args = build_pi_primary_args("fix it")
    assert (
        args[:2] == ["pi", "-p"]
        and "--no-session" in args
        and "--no-extensions" not in args
    )
    assert args[args.index("--model") + 1] == MODEL
    assert args[args.index("-e") + 1] == str(RECORD_EXT)
    assert args[-1] == "fix it"


def test_primary_plain_args_strip_extensions_skills_and_context_but_keep_the_recorder():
    from ladder.run_ladder import MODEL, RECORD_EXT, build_pi_primary_args

    args = build_pi_primary_args("fix it", plain=True)
    for flag in (
        "--no-extensions",
        "--no-skills",
        "--no-context-files",
        "--no-session",
    ):
        assert flag in args
    assert args[args.index("--model") + 1] == MODEL
    assert args[args.index("-e") + 1] == str(RECORD_EXT)
    assert args[-1] == "fix it"


def test_direct_args_can_replace_the_system_prompt_and_set_thinking(tmp_path):
    """The shipped worker uses systemPromptMode: replace; the ladder must be able to measure that."""
    from ladder.run_ladder import build_pi_direct_args

    prompt = tmp_path / "v4.md"
    prompt.write_text("facts")
    args = build_pi_direct_args(
        "fix it",
        False,
        prompt=prompt,
        prompt_mode="replace",
        thinking="low",
    )
    assert "--append-system-prompt" not in args
    assert args[args.index("--system-prompt") + 1] == "facts"
    assert args[args.index("--thinking") + 1] == "low"


def test_direct_args_default_to_replace_mode_with_the_worker_prompt():
    """The shipped agent file replaces Pi's prompt, so a bare direct run measures that; `append` is phases 0-2."""
    from ladder.run_ladder import PROMPT_FILE, build_pi_direct_args

    args = build_pi_direct_args("fix it", False)
    assert args[args.index("--system-prompt") + 1] == PROMPT_FILE.read_text()
    assert "--append-system-prompt" not in args


def test_run_record_leaves_direct_only_fields_empty_in_other_modes(
    monkeypatch, tmp_path
):
    """prompt_file/prompt_mode/thinking only describe direct mode; recording them elsewhere misdescribes the run."""
    import json
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess,
        "run",
        lambda args, **kw: sp.CompletedProcess(args, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(run_ladder, "prepare_pi_workspace", lambda ws, ext: ws)
    monkeypatch.setattr(run_ladder, "mirror_agent_dir", lambda s, d, t, **kw: d)
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(rung, "delegated", "baseline", 1, tmp_path / "out", 5, {}, True)
    record = json.loads(
        (
            tmp_path / "out" / "rung1-baseline-delegated-guards-r1" / "run.json"
        ).read_text()
    )
    assert record["prompt_file"] is None and record["prompt_mode"] is None
    assert record["thinking"] is None and record["prompt_version"] is None


def test_mode_args_run_mellum_inside_the_operator_profile_with_the_mode_extension():
    """Mellum mode: the operator's full profile (extensions, skills), plus the mode, guards, recorder."""
    from ladder.run_ladder import MODE_EXT, MODEL, RECORD_EXT, build_pi_mode_args

    args = build_pi_mode_args("fix it")
    assert "--no-extensions" not in args and "--no-skills" not in args
    assert args[args.index("--model") + 1] == MODEL
    exts = [args[i + 1] for i, a in enumerate(args) if a == "-e"]
    assert exts.index(str(MODE_EXT)) < exts.index(str(RECORD_EXT))
    assert args[-1] == "fix it"


def test_mode_env_activates_the_mode_headlessly():
    from ladder.run_ladder import child_env

    env = child_env({}, "/t", None, offline=False, mode=True)
    assert env["MELLUM_MODE"] == "1"
    assert "MELLUM_MODE" not in child_env({}, "/t", None, offline=False)


def test_mode_runs_record_guards_on_because_the_mode_always_loads_them(
    monkeypatch, tmp_path
):
    import json
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess,
        "run",
        lambda args, **kw: sp.CompletedProcess(args, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(run_ladder, "mirror_agent_dir", lambda s, d, t, **kw: d)
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(rung, "mode", "baseline", 1, tmp_path / "out", 5, {}, False)
    record = json.loads(
        (tmp_path / "out" / "rung1-baseline-mode-guards-r1" / "run.json").read_text()
    )
    assert record["guards"] is True and record["subagents_config"] is None


def test_worker_files_are_this_checkouts():
    for p in (PROMPT_FILE, MODE_EXT, GUARDS_EXT, RECORD_EXT):
        assert p.is_absolute() and p.is_file(), p
    assert MODE_EXT == REPO_ROOT / "extensions" / "mellum-mode.ts"
    assert GUARDS_EXT == REPO_ROOT / "extensions" / "mellum-guards.ts"
    assert PROMPT_FILE == REPO_ROOT / "prompts" / "mellum-worker.md"


def test_mode_args_load_mode_and_recorder_but_no_guards_file():
    args = build_pi_mode_args("fix it")
    exts = [args[i + 1] for i, a in enumerate(args) if a == "-e"]
    assert exts == [str(MODE_EXT), str(RECORD_EXT)]


def test_worker_provenance_names_package_version_and_git():
    from ladder.run_ladder import worker_provenance

    got = worker_provenance()
    assert (
        got["worker_version"]
        == json.loads((REPO_ROOT / "package.json").read_text())["version"]
    )
    assert got["worker_git"]


def test_worker_provenance_without_git(tmp_path):
    from ladder.run_ladder import worker_provenance

    (tmp_path / "package.json").write_text('{"version": "9.9.9"}')
    assert worker_provenance(tmp_path) == {
        "worker_version": "9.9.9",
        "worker_git": None,
    }


def test_mode_env_isolates_the_run_log_under_scratch(tmp_path):
    from ladder.run_ladder import mode_env

    env = mode_env(
        {"HOME": "/h"}, tmp_path / "trace.jsonl", tmp_path / "agent", tmp_path
    )
    assert env["MELLUM_MODE"] == "1"
    assert Path(env["MELLUM_MODE_RUNS"]).is_relative_to(tmp_path)
    assert env["PI_CODING_AGENT_DIR"] == str(tmp_path / "agent")
    assert "PI_OFFLINE" not in env


def test_mode_env_turns_facts_off_only_when_asked(tmp_path):
    from ladder.run_ladder import mode_env

    args = ({"HOME": "/h"}, tmp_path / "trace.jsonl", tmp_path / "agent", tmp_path)
    assert "MELLUM_MODE_FACTS" not in mode_env(*args)
    assert "MELLUM_MODE_FACTS" not in mode_env(*args, facts=True)
    assert mode_env(*args, facts=False)["MELLUM_MODE_FACTS"] == "0"


def test_worker_run_records_stay_under_each_runs_scratch(tmp_path):
    from ladder.run_ladder import child_env, mode_env

    # The operator's own record file must not leak into a ladder child.
    parent = {"HOME": "/h", "MELLUM_WORKER_RUNS": "/operator/runs.jsonl"}
    trace = tmp_path / "trace.jsonl"
    agent = tmp_path / "agent"
    envs = {
        "direct": child_env(parent, str(trace), agent, offline=True),
        "delegated": child_env(parent, str(trace), agent),
        "mode": mode_env(parent, trace, agent, tmp_path),
    }
    for name, env in envs.items():
        record = Path(env["MELLUM_WORKER_RUNS"])
        assert record == tmp_path / "mellum-worker-runs.jsonl", name


def test_strip_mellum_section_drops_the_section_and_keeps_the_rest_exactly():
    from ladder.run_ladder import strip_mellum_section

    text = (
        "# Title\r\n\r\nintro\n\n## Mellum\n\n- Test command: x\n### Sub\n- y\n\n"
        "## Other\n\nkeep  \n\ttabbed\n"
    )
    assert strip_mellum_section(text) == (
        "# Title\r\n\r\nintro\n\n## Other\n\nkeep  \n\ttabbed\n"
    )


def test_strip_mellum_section_runs_to_eof_and_stops_at_a_level_one_heading():
    from ladder.run_ladder import strip_mellum_section

    assert strip_mellum_section("# A\n\n## Mellum\n- x\n- y") == "# A\n\n"
    assert strip_mellum_section("## Mellum\n- x\n# B\nz\n") == "# B\nz\n"


def test_strip_mellum_section_leaves_a_file_without_the_section_unchanged():
    from ladder.run_ladder import strip_mellum_section

    for text in ("", "# A\n\ntext", "# A\n### Mellum\n- x\n", "# A\n## Mellumx\n"):
        assert strip_mellum_section(text) == text


@pytest.mark.slow
def test_prepare_workspace_strips_the_section_before_the_baseline_commit(tmp_path):
    from ladder.run_ladder import git, prepare_workspace
    from ladder.rungs import RUNGS

    ws = prepare_workspace(RUNGS[6], tmp_path, strip_facts_section=True)
    agents = (ws / "AGENTS.md").read_text()
    assert "## Mellum" not in agents and "Test command" not in agents
    assert agents.startswith("# AgentClinic")
    assert git(ws, "status", "--porcelain").strip() == ""
    assert "Test command" not in git(ws, "show", "HEAD:AGENTS.md")


@pytest.mark.slow
def test_prepare_workspace_keeps_the_section_by_default(tmp_path):
    from ladder.run_ladder import prepare_workspace
    from ladder.rungs import RUNGS

    ws = prepare_workspace(RUNGS[6], tmp_path)
    assert "## Mellum" in (ws / "AGENTS.md").read_text()


def test_parser_defaults_to_facts_on_and_no_strip():
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "6", "--out", "x"]
    args = build_parser().parse_args(base)
    assert args.mode_facts == "on" and args.strip_facts_section is False
    args = build_parser().parse_args(
        [*base, "--mode-facts", "off", "--strip-facts-section"]
    )
    assert args.mode_facts == "off" and args.strip_facts_section is True


def _real_run_for_git(monkeypatch, run_ladder):
    """Let git run for real while the child (pi) call is faked."""
    import subprocess as sp

    real = sp.run

    def fake(args, **kwargs):
        if args[0] == "git":
            return real(args, **kwargs)
        return sp.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(run_ladder.subprocess, "run", fake)


def test_run_record_names_the_facts_switches(monkeypatch, tmp_path):
    import json

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    _real_run_for_git(monkeypatch, run_ladder)
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(
        run_ladder, "mirror_agent_dir", lambda *a, **k: tmp_path / "agent"
    )
    rung = Rung(6, "x", "s", ["true"], lambda ws, base: CheckResult(True, True))
    run_ladder.run_once(
        rung,
        "mode",
        "baseline",
        1,
        tmp_path / "out",
        5,
        {},
        False,
        mode_facts="off",
        strip_facts_section=True,
    )
    record = json.loads(next((tmp_path / "out").glob("*/run.json")).read_text())
    assert record["mode_facts"] == "off"
    assert record["strip_facts_section"] is True


def test_the_check_runs_after_the_diff_is_staged_so_hidden_files_stay_out(
    monkeypatch, tmp_path
):
    """The scorer copies _hidden_p*.py into the workspace; diff.patch and files_created must not show them."""
    import json

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("a\n")

    def prepare(rung, scratch, **kw):
        run_ladder.git(ws, "init", "-q")
        run_ladder.git(ws, "add", "-A")
        run_ladder.git(
            ws, "-c", "user.name=t", "-c", "user.email=t@l", "commit", "-qm", "b"
        )
        (ws / "app.py").write_text("a\nb\n")  # stands in for the run's own edit
        return ws

    def check(ws_, base):
        (ws_ / "_hidden_p1.py").write_text("def test_x():\n    pass\n")
        return CheckResult(True, True)

    _real_run_for_git(monkeypatch, run_ladder)
    monkeypatch.setattr(run_ladder, "prepare_workspace", prepare)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    rung = Rung(6, "x", "s", ["true"], check)
    run_ladder.run_once(rung, "direct", "baseline", 1, tmp_path / "out", 5, {}, False)
    run_dir = next((tmp_path / "out").glob("rung6-*"))
    record = json.loads((run_dir / "run.json").read_text())
    assert "_hidden_p1.py" not in (run_dir / "diff.patch").read_text()
    assert "app.py" in (run_dir / "diff.patch").read_text()
    assert "_hidden_p1.py" not in record["files_created"]
    assert "_hidden_p1.py" not in record["diff_stat"]


@pytest.mark.parametrize(
    ("mode_facts", "strip", "expect_env"),
    [("on", False, None), ("off", True, "0"), ("on", True, None), ("off", False, "0")],
)
def test_run_once_wires_the_switches_into_the_child_env_and_the_workspace(
    monkeypatch, tmp_path, mode_facts, strip, expect_env
):
    """--mode-facts off is the A18 treatment: the child env must carry MELLUM_MODE_FACTS=0, and
    --strip-facts-section must reach prepare_workspace."""
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    real = sp.run
    child_envs, prepared = [], []

    def fake(args, **kwargs):
        if args[0] == "git":
            return real(args, **kwargs)
        child_envs.append(kwargs.get("env"))
        return sp.CompletedProcess(args, 0, stdout="", stderr="")

    def prepare(rung, scratch, **kw):
        prepared.append(kw)
        return scratch

    monkeypatch.delenv("MELLUM_MODE_FACTS", raising=False)
    monkeypatch.setattr(run_ladder.subprocess, "run", fake)
    monkeypatch.setattr(run_ladder, "prepare_workspace", prepare)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(
        run_ladder, "mirror_agent_dir", lambda *a, **k: tmp_path / "agent"
    )
    rung = Rung(6, "x", "s", ["true"], lambda ws, base: CheckResult(True, True))
    run_ladder.run_once(
        rung,
        "mode",
        "baseline",
        1,
        tmp_path / "out",
        5,
        {},
        False,
        mode_facts=mode_facts,
        strip_facts_section=strip,
    )
    assert len(child_envs) == 1
    assert child_envs[0].get("MELLUM_MODE_FACTS") == expect_env
    assert prepared == [
        {
            "strip_facts_section": strip,
            "facts_section": "fixture",
            "roadmap": "phase-files",
            "acceptance_test": None,
        }
    ]


# ---- backend / base-url / sampling overrides (the scriptable-MLX-server benchmark) ----


def test_redispatch_message_names_the_test_and_includes_the_failure():
    from ladder.run_ladder import redispatch_message

    msg = redispatch_message("tests/acc.py", "E   assert 1 == 2")
    assert "tests/acc.py" in msg and "assert 1 == 2" in msg and "fail" in msg.lower()


def test_run_acceptance_suppresses_warnings_and_keeps_the_traceback(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder

    captured = {}

    def fake(argv, **k):
        captured["argv"] = argv
        return sp.CompletedProcess(argv, 1, stdout="", stderr="")

    monkeypatch.setattr(run_ladder.subprocess, "run", fake)
    run_ladder.run_acceptance(tmp_path, "tests/acc.py")
    # warnings off (they drowned the signal) and a short traceback (keeps the assertion)
    assert "no:warnings" in captured["argv"]
    assert "--tb=short" in captured["argv"]


def test_redispatch_message_sends_the_failure_not_the_warning_noise():
    from ladder.run_ladder import redispatch_message

    # pytest output: failures first (the assertion), then the summary — no warnings
    # because run_acceptance disables them. The message must carry the assertion.
    out = (
        "FF\n"
        "=================================== FAILURES ===================================\n"
        "tests/t.py:24: in test_resolve\n"
        "    assert r.status_code == 303\n"
        "E   assert 404 == 303\n"
        "=========================== short test summary info ===========================\n"
        "FAILED tests/t.py::test_resolve\n2 failed in 0.7s"
    )
    msg = redispatch_message("tests/t.py", out)
    assert "assert 404 == 303" in msg  # the real failure reaches the worker
    assert "FAILURES" in msg


def test_parser_redispatch_default_and_set():
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "9", "--out", "x", "--acceptance-test", "/tmp/t.py"]
    assert build_parser().parse_args(base).redispatch == 0
    assert build_parser().parse_args([*base, "--redispatch", "3"]).redispatch == 3
    # the temperature ramp per retry defaults to a 0.25 step capped at 0.5
    assert build_parser().parse_args(base).redispatch_temperature_step == 0.25
    assert build_parser().parse_args(base).redispatch_temperature_cap == 0.5
    assert (
        build_parser()
        .parse_args([*base, "--redispatch-temperature-step", "0.3"])
        .redispatch_temperature_step
        == 0.3
    )
    assert (
        build_parser()
        .parse_args([*base, "--redispatch-temperature-cap", "0.7"])
        .redispatch_temperature_cap
        == 0.7
    )


def test_main_refuses_redispatch_without_acceptance_test(tmp_path):
    from ladder.run_ladder import main

    with pytest.raises(SystemExit):
        main(["--profile", "baseline", "--rung", "9", "--out", str(tmp_path / "o"),
              "--mode", "direct", "--redispatch", "2"])


def test_run_once_redispatches_until_acceptance_passes(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    launches = []

    def fake_run(argv, **k):
        launches.append(argv)
        return sp.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(run_ladder.subprocess, "run", fake_run)
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    seq = iter([(1, "boom"), (0, "ok")])  # acceptance: fail once, then pass
    monkeypatch.setattr(run_ladder, "run_acceptance", lambda ws, name: next(seq))
    acc = tmp_path / "test_acc.py"
    acc.write_text("x")
    rung = Rung(9, "agentclinic-p4", "impl", ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        acceptance_test=acc, redispatch=3,
    )
    assert rec["redispatch_attempts"] == 1
    pi_launches = [a for a in launches if "-p" in a]
    assert len(pi_launches) == 2  # initial + one re-dispatch


def test_redispatch_overrides_grows_temperature_and_moves_the_seed():
    from ladder.run_ladder import redispatch_overrides

    a1 = redispatch_overrides({}, 1, 0.2)
    a2 = redispatch_overrides({}, 2, 0.2)
    assert a1["temperature"] == 0.2 and a1["seed"] == 43
    assert a2["temperature"] == 0.4 and a2["seed"] == 44
    # temperature is capped (default ceiling 1.0)
    assert redispatch_overrides({}, 10, 0.2)["temperature"] == 1.0
    # a custom base temperature and seed are honoured
    b = redispatch_overrides({"temperature": 0.5, "seed": 100}, 1, 0.1)
    assert b["temperature"] == 0.6 and b["seed"] == 101


def test_redispatch_overrides_caps_temperature_but_keeps_reseeding():
    from ladder.run_ladder import redispatch_overrides

    # step 0.25 capped at 0.5: temp holds at the cap past attempt 2, seed moves on
    s = [redispatch_overrides({}, n, 0.25, temp_cap=0.5) for n in range(1, 5)]
    assert [r["temperature"] for r in s] == [0.25, 0.5, 0.5, 0.5]
    assert [r["seed"] for r in s] == [43, 44, 45, 46]


def test_run_once_grows_temperature_and_seed_across_redispatches(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess,
        "run",
        lambda argv, **k: sp.CompletedProcess(argv, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    seq = iter([(1, "boom"), (1, "boom"), (0, "ok")])  # fail twice, then pass
    monkeypatch.setattr(run_ladder, "run_acceptance", lambda ws, name: next(seq))
    acc = tmp_path / "test_acc.py"
    acc.write_text("x")
    rung = Rung(9, "agentclinic-p4", "impl", ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        acceptance_test=acc, redispatch=3, redispatch_temperature_step=0.2,
    )
    assert rec["redispatch_attempts"] == 2
    assert rec["redispatch_schedule"] == [
        {"attempt": 1, "temperature": 0.2, "seed": 43},
        {"attempt": 2, "temperature": 0.4, "seed": 44},
    ]


def test_redispatch_effort_ramps_thinking_and_tokens():
    from ladder.run_ladder import redispatch_effort

    # quick start (initial attempt 0), escalating as the frozen test keeps failing
    assert redispatch_effort(0, 5) == {"thinking": "off", "max_tokens": 2048}
    assert redispatch_effort(1, 5) == {"thinking": "off", "max_tokens": 2048}
    assert redispatch_effort(2, 5) == {"thinking": "medium", "max_tokens": 8192}
    assert redispatch_effort(5, 5) == {"thinking": "high", "max_tokens": 16384}


def test_run_once_effort_ramp_escalates_across_redispatches(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess,
        "run",
        lambda argv, **k: sp.CompletedProcess(argv, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    seq = iter([(1, "boom"), (1, "boom"), (1, "boom"), (0, "ok")])  # fail 3, then pass
    monkeypatch.setattr(run_ladder, "run_acceptance", lambda ws, name: next(seq))
    acc = tmp_path / "test_acc.py"
    acc.write_text("x")
    rung = Rung(9, "agentclinic-p4", "impl", ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        acceptance_test=acc, redispatch=3, effort_ramp=True,
    )
    # with effort_ramp on, each re-dispatch slice carries its escalating effort
    sched = rec["redispatch_schedule"]
    assert [(s["thinking"], s["max_tokens"]) for s in sched] == [
        ("off", 2048), ("medium", 8192), ("high", 16384),
    ]


def test_run_once_redispatches_even_when_attempts_time_out(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    def fake(argv, **k):
        # the worker (pi -p) always times out; git and other calls succeed
        if "-p" in argv:
            raise sp.TimeoutExpired(argv, k.get("timeout", 1), output=b"", stderr=b"")
        return sp.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(run_ladder.subprocess, "run", fake)
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    # the frozen test never passes, so only the retry cap stops the loop
    monkeypatch.setattr(run_ladder, "run_acceptance", lambda ws, name: (1, "still failing"))
    acc = tmp_path / "test_acc.py"
    acc.write_text("x")
    rung = Rung(9, "agentclinic-p4", "impl", ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        acceptance_test=acc, redispatch=3,
    )
    # a timed-out attempt is still a failing frozen test, so every retry fires
    assert rec["deadline_hit"] is True
    assert rec["redispatch_attempts"] == 3
    assert [s["attempt"] for s in rec["redispatch_schedule"]] == [1, 2, 3]


def test_build_pi_direct_args_model_spec_and_extra_extensions(tmp_path):
    from ladder.run_ladder import build_pi_direct_args

    ext = tmp_path / "content-assist"
    a = build_pi_direct_args("do it", model_spec="content-assist/tiny", extra_extensions=(ext,))
    # the model override replaces the default omlx/<id> target
    assert a[a.index("--model") + 1] == "content-assist/tiny"
    assert not any(x.startswith("omlx/") for x in a)
    # the extra extension is loaded via -e, alongside the record extension
    assert str(ext) in a
    # default behaviour is unchanged
    b = build_pi_direct_args("do it")
    assert b[b.index("--model") + 1].startswith("omlx/")


def test_parser_model_spec_and_pi_extension(tmp_path):
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "1", "--out", "x"]
    assert build_parser().parse_args(base).model_spec is None
    assert build_parser().parse_args(base).pi_extension == []
    ns = build_parser().parse_args([*base, "--model-spec", "content-assist/tiny", "--pi-extension", "/p/ext"])
    assert ns.model_spec == "content-assist/tiny"
    assert ns.pi_extension == ["/p/ext"]


def test_parser_acceptance_test_default_and_set():
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "9", "--out", "x"]
    assert build_parser().parse_args(base).acceptance_test is None
    a = build_parser().parse_args([*base, "--acceptance-test", "/tmp/t.py"])
    assert str(a.acceptance_test) == "/tmp/t.py"


def test_main_refuses_acceptance_test_outside_direct_mode(tmp_path):
    from ladder.run_ladder import main

    with pytest.raises(SystemExit):
        main(["--profile", "baseline", "--rung", "9", "--out", str(tmp_path / "o"),
              "--mode", "mode", "--acceptance-test", "/tmp/t.py"])


def test_main_refuses_acceptance_test_not_collectable_by_pytest(tmp_path):
    """A test pytest won't collect (not test_*.py) would be placed but never run; fail fast."""
    from ladder.run_ladder import main

    bad = tmp_path / "acc_p4.py"  # pytest only auto-collects test_*.py
    bad.write_text("def test_x():\n    assert True\n")
    with pytest.raises(SystemExit):
        main(["--profile", "baseline", "--rung", "9", "--out", str(tmp_path / "o"),
              "--mode", "direct", "--acceptance-test", str(bad)])


def test_run_once_places_acceptance_test_and_sets_make_it_pass(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    seen = {}

    def prepare(rung, scratch, **kw):
        seen.update(kw)
        scratch.mkdir(parents=True, exist_ok=True)
        return scratch

    monkeypatch.setattr(run_ladder, "prepare_workspace", prepare)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(
        run_ladder.subprocess, "run",
        lambda a, **k: sp.CompletedProcess(a, 0, stdout="", stderr=""),
    )
    acc = tmp_path / "test_acc.py"
    acc.write_text("def test_x():\n    assert True\n")
    rung = Rung(9, "agentclinic-p4", "Implement specs/phase-4-resolve-reopen.md",
                ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False, acceptance_test=acc
    )
    assert seen.get("acceptance_test") == acc
    sentence = rec["launch"]["argv"][-1]
    assert sentence.startswith("Make tests/test_acc.py pass.")
    assert "do not run the app or start servers" in sentence  # blocking-command guard
    assert "Test command: uv run --offline python -m pytest tests" in sentence
    assert rec["acceptance_test"] == "test_acc.py"


@pytest.mark.slow
def test_prepare_workspace_places_the_acceptance_test_in_the_baseline(tmp_path):
    from ladder.run_ladder import git, prepare_workspace
    from ladder.rungs import RUNGS

    acc = tmp_path / "test_acc.py"
    acc.write_text("def test_x():\n    assert True\n")
    ws = prepare_workspace(RUNGS[9], tmp_path, acceptance_test=acc)
    placed = ws / "tests" / "test_acc.py"
    assert placed.exists() and placed.read_text() == acc.read_text()
    assert git(ws, "ls-files", "tests/test_acc.py").strip() == "tests/test_acc.py"


def test_parser_backend_base_url_and_sampling_defaults_and_choices():
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "1", "--out", "x"]
    args = build_parser().parse_args(base)
    assert args.backend == "omlx" and args.base_url is None
    assert args.temperature is None and args.top_p is None
    args = build_parser().parse_args(
        [
            *base,
            "--backend",
            "mlx-lm",
            "--base-url",
            "http://127.0.0.1:8080/v1",
            "--temperature",
            "0.7",
            "--top-p",
            "0.9",
        ]
    )
    assert args.backend == "mlx-lm" and args.base_url == "http://127.0.0.1:8080/v1"
    assert args.temperature == 0.7 and args.top_p == 0.9


def test_direct_args_use_the_model_id_override():
    from ladder.run_ladder import build_pi_direct_args

    args = build_pi_direct_args("fix it", model_id="/abs/path/Mellum-x")
    assert args[args.index("--model") + 1] == "omlx//abs/path/Mellum-x"


def test_direct_args_model_defaults_to_mellum():
    from ladder.run_ladder import MODEL, build_pi_direct_args

    args = build_pi_direct_args("fix it")
    assert args[args.index("--model") + 1] == MODEL


def test_parser_model_id_default_and_set():
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "1", "--out", "x"]
    assert build_parser().parse_args(base).model_id is None
    assert build_parser().parse_args([*base, "--model-id", "/abs/Mellum-x"]).model_id == "/abs/Mellum-x"


def test_main_refuses_model_id_outside_direct_mode(tmp_path):
    from ladder.run_ladder import main

    with pytest.raises(SystemExit):
        main(["--profile", "baseline", "--rung", "1", "--out", str(tmp_path / "o"),
              "--mode", "mode", "--model-id", "x"])


def test_run_once_sends_the_model_id_override(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess, "run",
        lambda a, **k: sp.CompletedProcess(a, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    rung = Rung(1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        model_id="/abs/path/Mellum-x", base_url="http://127.0.0.1:8080/v1",
    )
    assert "omlx//abs/path/Mellum-x" in rec["launch"]["argv"]
    assert rec["model_id"] == "/abs/path/Mellum-x"


def test_run_once_model_id_defaults_to_mellum(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.run_ladder import MODEL_ID
    from ladder.rungs import CheckResult, Rung

    monkeypatch.setattr(
        run_ladder.subprocess, "run",
        lambda a, **k: sp.CompletedProcess(a, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    rung = Rung(1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True))
    rec = run_ladder.run_once(rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False)
    assert rec["model_id"] == MODEL_ID


def test_main_refuses_mlx_lm_backend_without_a_base_url(tmp_path):
    from ladder.run_ladder import main

    with pytest.raises(SystemExit):
        main(
            [
                "--profile", "baseline", "--rung", "1",
                "--out", str(tmp_path / "o"), "--backend", "mlx-lm",
            ]
        )


def test_main_refuses_direct_only_flags_outside_direct_mode(tmp_path):
    from ladder.run_ladder import main

    for extra in (
        ["--base-url", "http://h/v1"],
        ["--temperature", "0.7"],
        ["--top-p", "0.9"],
        ["--backend", "mlx-lm", "--base-url", "http://h/v1"],
    ):
        with pytest.raises(SystemExit):
            main(
                [
                    "--profile", "baseline", "--rung", "1",
                    "--out", str(tmp_path / "o"), "--mode", "mode", *extra,
                ]
            )


def test_run_once_wires_base_url_and_overrides_into_direct(monkeypatch, tmp_path):
    import subprocess as sp

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    seen = {}

    def fake_direct(dest, prof, **kw):
        seen.update(kw)
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    monkeypatch.setattr(run_ladder, "direct_agent_dir", fake_direct)
    monkeypatch.setattr(
        run_ladder.subprocess,
        "run",
        lambda a, **k: sp.CompletedProcess(a, 0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        base_url="http://127.0.0.1:8080/v1",
        request_overrides={"temperature": 0.7, "top_p": 0.9},
    )
    assert seen["base_url"] == "http://127.0.0.1:8080/v1"
    assert seen["request_overrides"] == {"temperature": 0.7, "top_p": 0.9}


def test_run_record_names_backend_base_url_and_overrides(monkeypatch, tmp_path):
    import json

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    _real_run_for_git(monkeypatch, run_ladder)
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(
        rung, "direct", "tuned", 1, tmp_path / "out", 5, {}, False,
        backend="mlx-lm", base_url="http://127.0.0.1:8080/v1",
        request_overrides={"temperature": 0.7},
    )
    record = json.loads(next((tmp_path / "out").glob("*/run.json")).read_text())
    assert record["backend"] == "mlx-lm"
    assert record["base_url"] == "http://127.0.0.1:8080/v1"
    assert record["request_overrides"] == {"temperature": 0.7}


def test_run_record_leaves_backend_fields_empty_in_other_modes(monkeypatch, tmp_path):
    import json

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    _real_run_for_git(monkeypatch, run_ladder)
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(run_ladder, "mirror_agent_dir", lambda s, d, t, **kw: d)
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda ws, base: CheckResult(False, True)
    )
    run_ladder.run_once(rung, "delegated", "baseline", 1, tmp_path / "out", 5, {}, True)
    record = json.loads(next((tmp_path / "out").glob("*/run.json")).read_text())
    assert record["backend"] is None and record["base_url"] is None
    assert record["request_overrides"] is None


def test_main_runs_the_admin_profile_only_for_the_omlx_backend(monkeypatch, tmp_path):
    """omlx backend applies/restores the server profile; a plain mlx-lm server has no admin API, so it must not."""
    import contextlib

    from ladder import run_ladder

    calls = []

    class FakeClient:
        def __init__(self, base):
            calls.append(("client", base))

    @contextlib.contextmanager
    def fake_profile(client, model_id, name, path):
        calls.append(("profile", name))
        yield {"max_tokens": 1}

    monkeypatch.setattr(run_ladder, "AdminClient", FakeClient)
    monkeypatch.setattr(run_ladder, "profile", fake_profile)
    monkeypatch.setattr(run_ladder, "resolve_pi", lambda e: {"executable": e, "version": "t"})
    monkeypatch.setattr(run_ladder, "tool_version", lambda cmd: "t")
    monkeypatch.setattr(
        run_ladder, "run_once", lambda *a, **k: {"score": {"effective_params": None}}
    )
    monkeypatch.setattr(run_ladder, "table_row", lambda record: "")

    run_ladder.main(
        ["--profile", "baseline", "--rung", "1", "--out", str(tmp_path / "o"), "--mode", "direct"]
    )
    assert ("client", "http://127.0.0.1:8001") in calls
    assert any(c[0] == "profile" for c in calls)

    calls.clear()
    run_ladder.main(
        [
            "--profile", "baseline", "--rung", "1", "--out", str(tmp_path / "o2"),
            "--mode", "direct", "--backend", "mlx-lm",
            "--base-url", "http://127.0.0.1:8080/v1",
        ]
    )
    assert calls == []


@pytest.mark.parametrize("outcome", ["normal", "signal", "deadline"])
def test_runner_process_outcomes_do_not_invent_settlement(
    monkeypatch, tmp_path, outcome
):
    import subprocess
    from ladder import run_ladder
    from ladder.rungs import Rung, CheckResult

    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda *a, **kw: tmp_path)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda *a: (set(), {}))
    monkeypatch.setattr(run_ladder, "git", lambda *a: "")

    def execute(argv, **kw):
        if argv[0] == "git":
            return subprocess.CompletedProcess(
                argv, 0, stdout="test-revision", stderr=""
            )
        if outcome == "deadline":
            raise subprocess.TimeoutExpired(
                argv,
                1,
                output=b'{"type":"agent_end"}\n',
                stderr=b"mellum-trace: disk full",
            )
        return subprocess.CompletedProcess(
            argv,
            0 if outcome == "normal" else -15,
            stdout='{"type":"agent_end"}\n',
            stderr="",
        )

    monkeypatch.setattr(run_ladder.subprocess, "run", execute)
    rung = Rung(
        1, "calculator", "fix it", ["true"], lambda *a: CheckResult(False, True)
    )
    record = run_ladder.run_once(
        rung, "direct", "baseline", 1, tmp_path / "out", 1, {}, False
    )
    assert record["process"]["deadlineHit"] == (outcome == "deadline")
    assert record["process"]["exitCode"] == (0 if outcome == "normal" else None)
    assert record["process"]["signal"] == (15 if outcome == "signal" else None)
    assert record["process"]["settled"] is False
    assert record["process"]["elapsedMs"] >= 0
    if outcome == "deadline":
        assert (
            "mellum-trace: disk full"
            in next((tmp_path / "out").glob("*/stdout.txt")).read_text()
        )
        assert record["telemetry"]["status"] == "incomplete"


def test_run_once_stops_leftover_processes_in_the_workspace_and_records_them(
    monkeypatch, tmp_path
):
    """A server left running at the deadline is stopped before the workspace is staged."""
    import json

    from ladder import run_ladder
    from ladder.rungs import CheckResult, Rung

    calls = []
    _real_run_for_git(monkeypatch, run_ladder)
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(
        run_ladder, "mirror_agent_dir", lambda *a, **k: tmp_path / "agent"
    )
    left = [{"pid": 4242, "command": "uvicorn app:app --port 8000", "killed": True}]

    def fake_stop(ws, **kw):
        calls.append(ws)
        return left

    monkeypatch.setattr(run_ladder, "stop_leftovers", fake_stop)
    rung = Rung(6, "x", "s", ["true"], lambda ws, base: CheckResult(True, True))
    run_ladder.run_once(rung, "mode", "baseline", 1, tmp_path / "out", 5, {}, False)
    record = json.loads(next((tmp_path / "out").glob("*/run.json")).read_text())
    assert len(calls) == 1
    assert record["leftover_processes"] == left


# ---- A21: the lighter ## Mellum section and a one-file roadmap (fixture variants) ----

LIGHT = (
    "- Test command: uv run python -m pytest tests\n"
    "- Do not: install packages or add dependencies; add __init__.py, conftest.py,"
    " pytest.ini or setup.cfg files; weaken tests\n"
)


def test_light_section_replaces_the_bullets_and_keeps_the_rest_exactly():
    from ladder.run_ladder import light_mellum_section

    text = "# AgentClinic\n\n## Mellum\n\n- Test command: x\n- Write only: app.py\n\n## Notes\n\nkeep\n"
    assert light_mellum_section(text, LIGHT) == (
        "# AgentClinic\n\n## Mellum\n\n" + LIGHT + "\n## Notes\n\nkeep\n"
    )


def test_one_file_roadmap_joins_the_four_phase_specs_in_order():
    from ladder.run_ladder import one_file_roadmap

    text = one_file_roadmap()
    assert text.startswith("# AgentClinic roadmap\n")
    heads = [l for l in text.splitlines() if l.startswith("## Phase ")]
    assert heads == [
        "## Phase 1 — Home Page",
        "## Phase 2 — Complaints Board",
        "## Phase 3 — Add Complaint",
        "## Phase 4 — Resolve and Reopen",
    ]
    assert "# Phase" not in text.replace("## Phase", "")
    assert "`python app.py` starts the app with uvicorn, with reload." in text


@pytest.mark.slow
def test_prepare_workspace_applies_both_variants_before_the_baseline_commit(tmp_path):
    from ladder.run_ladder import git, prepare_workspace
    from ladder.rungs import RUNGS

    ws = prepare_workspace(RUNGS[7], tmp_path, facts_section="light", roadmap="one-file")
    agents = (ws / "AGENTS.md").read_text()
    assert LIGHT in agents and "Write only" not in agents
    assert sorted(p.name for p in (ws / "specs").iterdir()) == ["roadmap.md"]
    assert git(ws, "status", "--porcelain").strip() == ""
    assert "Write only" not in git(ws, "show", "HEAD:AGENTS.md")


def test_task_sentence_names_the_phase_of_the_one_file_roadmap():
    from ladder.run_ladder import variant_rung
    from ladder.rungs import RUNGS

    assert variant_rung(RUNGS[6], "one-file").sentence == "Implement Phase 1 of specs/roadmap.md"
    assert variant_rung(RUNGS[9], "one-file").sentence == "Implement Phase 4 of specs/roadmap.md"
    assert variant_rung(RUNGS[6], "phase-files") is RUNGS[6]


def test_parser_variant_defaults_and_choices():
    from ladder.run_ladder import build_parser

    base = ["--profile", "baseline", "--rung", "6", "--out", "x"]
    args = build_parser().parse_args(base)
    assert args.facts_section == "fixture" and args.roadmap == "phase-files"
    args = build_parser().parse_args([*base, "--facts-section", "light", "--roadmap", "one-file"])
    assert args.facts_section == "light" and args.roadmap == "one-file"


def test_variants_are_refused_on_rungs_without_the_agentclinic_fixture():
    from ladder.run_ladder import main

    with pytest.raises(SystemExit):
        main(["--profile", "baseline", "--rung", "2", "--out", "x", "--roadmap", "one-file"])


def test_run_record_names_the_variants_and_uses_the_roadmap_sentence(monkeypatch, tmp_path):
    import json

    from ladder import run_ladder
    from ladder.rungs import RUNGS

    seen = {}
    _real_run_for_git(monkeypatch, run_ladder)
    monkeypatch.setattr(
        run_ladder, "prepare_workspace", lambda rung, scratch, **kw: seen.update(kw) or scratch
    )
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(run_ladder, "mirror_agent_dir", lambda *a, **k: tmp_path / "agent")
    import dataclasses

    from ladder.rungs import CheckResult

    rung = dataclasses.replace(RUNGS[7], check=lambda ws, base: CheckResult(True, True))
    run_ladder.run_once(
        rung, "mode", "baseline", 1, tmp_path / "out", 5, {}, False,
        facts_section="light", roadmap="one-file",
    )
    record = json.loads(next((tmp_path / "out").glob("*/run.json")).read_text())
    assert record["facts_section"] == "light" and record["roadmap"] == "one-file"
    assert record["sentence"] == "Implement Phase 2 of specs/roadmap.md"
    assert seen["facts_section"] == "light" and seen["roadmap"] == "one-file"
