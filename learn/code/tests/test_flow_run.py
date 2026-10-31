import re
import signal
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flow_run


def test_reap_group_swallows_eperm_and_no_such_process(monkeypatch):
    # EPERM crashed a whole best-of-N run: the pid was recycled into a group we do not own.
    for exc in (PermissionError(1, "Operation not permitted"), ProcessLookupError()):
        def boom(pid, sig, _e=exc):
            raise _e
        monkeypatch.setattr(flow_run.os, "killpg", boom)
        flow_run.reap_group(12345)  # must not raise


def test_reap_group_signals_the_group_on_the_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(flow_run.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    flow_run.reap_group(999)
    assert calls == [(999, signal.SIGKILL)]


def test_restore_gate_materialises_every_phase_and_clears_stale(tmp_path):
    gate = tmp_path / "plan" / "gate"
    gate.mkdir(parents=True)
    tests = tmp_path / "tests"
    tests.mkdir()
    (gate / "phase_1.py").write_text("def test_p1():\n    assert 1\n")
    (gate / "phase_2.py").write_text("def test_p2():\n    assert 2\n")
    (tests / "test_gate_phase_9.py").write_text("def test_stale():\n    assert 0\n")  # dropped phase
    (tests / "test_coder.py").write_text("def test_keep():\n    assert 1\n")  # coder's own, must stay

    flow_run.restore_gate(tmp_path)

    got = sorted(p.name for p in tests.iterdir())
    assert got == ["test_coder.py", "test_gate_phase_1.py", "test_gate_phase_2.py"]
    assert "test_p1" in (tests / "test_gate_phase_1.py").read_text()


def test_restore_gate_is_a_noop_without_a_gate_dir(tmp_path):
    flow_run.restore_gate(tmp_path)  # no plan/gate — must not raise


def _freeze(ws, phase, text):
    (ws / "plan" / "gate").mkdir(parents=True, exist_ok=True)
    (ws / "plan" / "gate" / f"phase_{phase}.py").write_text(text)


def test_phase_gate_ok_requires_a_real_frozen_test_for_this_phase(tmp_path):
    # the bug: a fork with no phase-N test inherits the earlier gate and "passes" trivially.
    assert flow_run.phase_gate_ok(tmp_path, 3) is False          # no gate dir / file at all
    _freeze(tmp_path, 1, "def test_home():\n    assert 1\n")
    assert flow_run.phase_gate_ok(tmp_path, 3) is False          # phase 1 frozen, but not phase 3
    _freeze(tmp_path, 3, "def test_add():\n    assert 1\n")
    assert flow_run.phase_gate_ok(tmp_path, 3) is True           # phase 3 now has a real test


def test_seeded_done_lists_the_phases_before_start(tmp_path):
    # resuming at phase N treats phases 1..N-1 as already built — their titles seed `done` so the
    # forward-context message lists them as implemented and passing.
    titles = ["Home", "Board", "Add", "Resolve", "Archive"]
    assert flow_run.seeded_done(titles, 1) == []
    assert flow_run.seeded_done(titles, 5) == ["Home", "Board", "Add", "Resolve"]
    assert flow_run.seeded_done(titles, 99) == titles  # clamped by the slice


def _mk_seed(seed: Path, gates: range):
    (seed / "plan" / "gate").mkdir(parents=True)
    (seed / "templates").mkdir()
    (seed / ".venv" / "bin").mkdir(parents=True)
    (seed / "app.py").write_text("app = 1\n")
    (seed / "models.py").write_text("complaints = []\n")
    (seed / "data.db").write_bytes(b"\x00seed")
    (seed / ".venv" / "bin" / "python").write_text("#!/stale/path\n")  # must NOT be copied
    (seed / "trace-p1-0.jsonl").write_text("{}\n")  # trace must NOT be copied
    for n in gates:
        (seed / "plan" / "gate" / f"phase_{n}.py").write_text(f"def test_p{n}():\n    assert 1\n")


def test_seed_from_bundle_copies_app_and_gates_but_not_venv_or_traces(tmp_path):
    seed = tmp_path / "seed"
    _mk_seed(seed, range(1, 5))  # phases 1-4 frozen
    ws = tmp_path / "ws"
    ws.mkdir()
    flow_run.seed_from_bundle(seed, ws, 5)  # resume at phase 5
    assert (ws / "app.py").read_text() == "app = 1\n"
    assert (ws / "models.py").is_file() and (ws / "data.db").is_file()
    assert (ws / "plan" / "gate" / "phase_1.py").is_file()
    assert (ws / "plan" / "gate" / "phase_4.py").is_file()
    assert not (ws / ".venv").exists()          # stale venv excluded
    assert not (ws / "trace-p1-0.jsonl").exists()  # traces excluded


def test_seed_from_bundle_requires_every_earlier_gate(tmp_path):
    seed = tmp_path / "seed"
    _mk_seed(seed, range(1, 3))  # only phases 1-2 frozen
    ws = tmp_path / "ws"
    ws.mkdir()
    with pytest.raises(FileNotFoundError, match=r"phase\(s\) \[3, 4\]"):
        flow_run.seed_from_bundle(seed, ws, 5)  # needs 1-4, 3 and 4 missing


def test_seed_from_bundle_missing_seed_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        flow_run.seed_from_bundle(tmp_path / "nope", tmp_path / "ws", 2)


def test_restore_fixture_data_puts_rows_back_keeping_migrated_schema(tmp_path):
    import sqlite3
    base = tmp_path / "base"
    base.mkdir()
    # pristine fixture: 3 ticket rows
    src = sqlite3.connect(base / "data.db")
    src.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY, cents INTEGER)")
    src.executemany("INSERT INTO tickets (id, cents) VALUES (?, ?)", [(1, 100), (2, 200), (3, 300)])
    src.commit()
    src.close()
    # workspace db: coder added a migration column (note), and a gate DELETEd the rows + inserted junk
    ws = tmp_path / "ws"
    ws.mkdir()
    dst = sqlite3.connect(ws / "data.db")
    dst.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY, cents INTEGER, note TEXT)")  # migrated schema
    dst.execute("INSERT INTO tickets (id, cents, note) VALUES (99, 9999, 'junk')")  # test leftover
    dst.commit()
    dst.close()

    restored = flow_run.restore_fixture_data(ws, base)
    assert restored == ["data.db"]
    out = sqlite3.connect(ws / "data.db")
    assert out.execute("SELECT COUNT(*), SUM(cents) FROM tickets").fetchone() == (3, 600)  # fixture rows back
    cols = [r[1] for r in out.execute("PRAGMA table_info(tickets)")]
    assert "note" in cols  # migrated schema preserved
    assert out.execute("SELECT note FROM tickets WHERE id=1").fetchone()[0] is None  # new col keeps default
    out.close()


def test_fixture_schema_note_lists_real_columns(tmp_path):
    import sqlite3
    ws = tmp_path / "ws"
    ws.mkdir()
    con = sqlite3.connect(ws / "data.db")
    con.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, agent TEXT, date TEXT, minutes INTEGER)")
    con.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY, cents INTEGER)")
    con.commit()
    con.close()
    note = flow_run.fixture_schema_note(ws)
    assert "data.db.visits(id, agent, date, minutes)" in note
    assert "data.db.tickets(id, cents)" in note
    assert "do not invent" in note.lower()


def test_app_compiles_detects_a_broken_module(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("x = 1\n")
    (ws / "models.py").write_text("y = 2\n")
    assert flow_run.app_compiles(ws) is True
    (ws / "app.py").write_text('cur.execute("""\nunterminated\n')  # the clean1 failure mode
    assert flow_run.app_compiles(ws) is False


def test_git_checkpoint_then_revert_restores_last_good(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("good = 1\n")
    flow_run.git_init_workspace(ws)                 # base checkpoint
    (ws / "app.py").write_text("good = 2\n")
    flow_run.git_checkpoint(ws, "phase 1: PASS")    # known-good anchor
    (ws / "app.py").write_text("BROKEN (((\n")       # a breaking change
    (ws / "junk.py").write_text("stray\n")           # an untracked stray file
    flow_run.git_revert_to_checkpoint(ws)
    assert (ws / "app.py").read_text() == "good = 2\n"   # reverted to last checkpoint
    assert not (ws / "junk.py").exists()                  # stray cleaned
    assert ".venv/" in (ws / ".gitignore").read_text()    # venv ignored, never tracked


def test_round_concurrency_escalates_only_on_retry(tmp_path):
    # first try cheap (round 0 = concurrency); retries throw best-of-N at the stuck phase.
    assert flow_run.round_concurrency(0, 1, 2) == 1   # round 0: single
    assert flow_run.round_concurrency(1, 1, 2) == 2   # round 1: escalate
    assert flow_run.round_concurrency(3, 1, 3) == 3   # later retries: full best-of-N
    assert flow_run.round_concurrency(0, 2, 2) == 2   # if concurrency already 2, round 0 is 2
    assert flow_run.round_concurrency(2, 2, 2) == 2   # default: same every round


def test_fixture_schema_note_empty_without_db(tmp_path):
    (tmp_path / "ws").mkdir()
    assert flow_run.fixture_schema_note(tmp_path / "ws") == ""


def test_restore_fixture_data_noop_without_base_or_db(tmp_path):
    assert flow_run.restore_fixture_data(tmp_path / "ws", tmp_path / "nobase") == []
    (tmp_path / "base").mkdir()
    (tmp_path / "ws").mkdir()
    assert flow_run.restore_fixture_data(tmp_path / "ws", tmp_path / "base") == []  # no *.db


def test_phase_gate_ok_rejects_html_and_testless_files(tmp_path):
    _freeze(tmp_path, 3, "templates/complaints.html\n{% extends 'base.html' %}\n<div>hi</div>\n")
    assert flow_run.phase_gate_ok(tmp_path, 3) is False          # an HTML blob does not compile
    _freeze(tmp_path, 3, "import pytest\nX = 1  # no test functions\n")
    assert flow_run.phase_gate_ok(tmp_path, 3) is False          # compiles but defines no test


def test_gate_files_selects_only_the_frozen_gate_not_the_coders_scratch_tests(tmp_path):
    # hard phase 4: the coder's own test_app.py order test was brittle (list-equality vs shared
    # in-memory state) and failed a CORRECT, gate-passing build. The phase is judged on the FROZEN
    # gate — the definition of DONE — never on the coder's scratch tests.
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_gate_phase_1.py").write_text("def test_g1():\n    assert 1\n")
    (tests / "test_gate_phase_2.py").write_text("def test_g2():\n    assert 1\n")
    (tests / "test_app.py").write_text("def test_coder():\n    assert 1\n")  # coder's own — excluded
    (tests / "conftest.py").write_text("")  # not a gate file
    got = sorted(p.name for p in flow_run.gate_files(tmp_path))
    assert got == ["test_gate_phase_1.py", "test_gate_phase_2.py"]
    # phase filter: score a phase on its OWN gate, so a brittle earlier gate can't poison it
    only2 = [p.name for p in flow_run.gate_files(tmp_path, phase=2)]
    assert only2 == ["test_gate_phase_2.py"]
    assert flow_run.gate_files(tmp_path, phase=9) == []  # no such phase


def test_gate_files_is_empty_when_no_cumulative_gate_was_frozen(tmp_path):
    # the single-file easy gate freezes no plan/gate/phase_*.py, so there are no test_gate_phase_*
    # files; callers fall back to running the whole suite in that case.
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_home.py").write_text("def test_h():\n    assert 1\n")
    assert flow_run.gate_files(tmp_path) == []


# --- free flow arm: the two invariants, as pure functions -----------------------------------
# INVARIANT 1 — a frozen external acceptance test exists BEFORE any build (freeze the oracle).
# INVARIANT 2 — exit is verified, never self-declared: the harness re-runs the frozen gate and
#               re-dispatches the agent on failure, bounded by the retry budget.

def test_ensure_gate_frozen_runs_examine_until_a_real_gate_exists():
    # the examiner writes the gate; the build may not start until one is frozen. One corrective
    # retry covers a dropped/mis-formatted reply that froze nothing (seen on hard phases 4 and 5).
    frozen = {"n": 0}

    def examine_ok():
        frozen["n"] += 1  # freezes on the first pass

    assert flow_run.ensure_gate_frozen(examine_ok, lambda: frozen["n"] >= 1, retries=1) is True
    assert frozen["n"] == 1  # no wasted retry once it froze

    calls = {"n": 0}

    def examine_second():
        calls["n"] += 1

    # never freezes → exhausts retries+1 attempts and reports no gate (the build must not proceed)
    assert flow_run.ensure_gate_frozen(examine_second, lambda: False, retries=1) is False
    assert calls["n"] == 2  # first try + one corrective retry

    late = {"n": 0}
    assert flow_run.ensure_gate_frozen(
        lambda: late.__setitem__("n", late["n"] + 1), lambda: late["n"] >= 2, retries=1) is True
    assert late["n"] == 2  # froze on the corrective retry


def test_drive_free_coder_redispatches_with_feedback_until_the_gate_passes():
    # the agent builds; the frozen gate decides. On a fail it is re-dispatched WITH the failure
    # text ("sorry, you didn't pass — here's what failed, try again"); 'done' is never the agent's
    # own word. Records how many rounds it took, so a run can report whether it ever solved it.
    seen: list[tuple[int, str]] = []
    checks = iter([(False, "E   assert 0  # /visits missing"), (True, "")])

    def dispatch(rnd, feedback):
        seen.append((rnd, feedback))

    solved, rounds = flow_run.drive_free_coder(dispatch, lambda: next(checks), attempts=5)
    assert solved is True and rounds == 2
    assert seen[0] == (0, "")                                   # first dispatch: no feedback yet
    assert seen[1] == (1, "E   assert 0  # /visits missing")    # second carries the gate's failure


def test_drive_free_coder_is_bounded_and_records_an_unsolved_run():
    # max retries are X (the budget); if the gate never passes, the run is recorded as NOT solved —
    # the harness removes obstacles, it cannot force a correct build out of a fixed model.
    dispatched = {"n": 0}

    def dispatch(rnd, feedback):
        dispatched["n"] += 1

    solved, rounds = flow_run.drive_free_coder(
        dispatch, lambda: (False, "still failing"), attempts=3)
    assert solved is False and rounds == 3  # exhausted the budget
    assert dispatched["n"] == 3             # one dispatch per allowed retry, no more


def _patch_free(monkeypatch, *, gate_freezes, gate_results):
    """Patch the pi-spawn and gate checks so drive_phase_free runs with no model/GPU. Records each
    run_top call's label; `gate_freezes` drives phase_gate_ok, `gate_results` drives run_gate."""
    calls: list[str] = []
    monkeypatch.setattr(flow_run, "run_top", lambda *a, **k: calls.append(k.get("label", "")))
    monkeypatch.setattr(flow_run, "restore_gate", lambda ws: None)
    monkeypatch.setattr(flow_run, "phase_gate_ok", lambda ws, ph: next(gate_freezes))
    monkeypatch.setattr(flow_run, "run_gate", lambda ws, to, ph: next(gate_results))
    return calls


def test_drive_phase_free_never_builds_without_a_frozen_gate(tmp_path, monkeypatch):
    # INVARIANT 1 end-to-end: if the examiner freezes no gate, there is no definition of DONE —
    # the coder must NEVER be dispatched. run_gate raises if the glue ever reaches a build.
    def boom(*a, **k):
        raise AssertionError("run_gate must not be called when no gate froze")

    calls = _patch_free(monkeypatch, gate_freezes=iter([False, False]), gate_results=iter([]))
    monkeypatch.setattr(flow_run, "run_gate", boom)
    solved, rounds = flow_run.drive_phase_free(
        3, workspace=tmp_path, profile=tmp_path, recorder=tmp_path, provider="p", model="m",
        run=tmp_path, timeout=10.0, thinking="off", attempts=5)
    assert solved is False and rounds == 0
    assert all("examiner" in c for c in calls)  # only examiner pass(es), no coder dispatch
    assert len(calls) == 2                        # first examine + one corrective retry


def test_drive_phase_free_builds_once_the_gate_is_frozen_and_passes(tmp_path, monkeypatch):
    # gate freezes, coder passes on the first round → solved in 1, examiner then coder ran.
    calls = _patch_free(
        monkeypatch, gate_freezes=iter([True, True]), gate_results=iter([(True, "")]))
    solved, rounds = flow_run.drive_phase_free(
        1, workspace=tmp_path, profile=tmp_path, recorder=tmp_path, provider="p", model="m",
        run=tmp_path, timeout=10.0, thinking="off", attempts=5)
    assert solved is True and rounds == 1
    assert "examiner" in calls[0] and "free coder" in calls[1]  # freeze first, THEN build


def test_drive_phase_free_injects_memory_grounding_and_learns_from_a_failure(tmp_path, monkeypatch):
    # memory makes the free arm skill-like: a matching lesson grounds the build, and the failure
    # teaches a new general lesson. No GPU — the pi-spawn and gate are monkeypatched.
    import memory as mem
    m = mem.Memory(tmp_path / "memory.jsonl")
    m.add("building a report that reads from a database store",
          "inspect the real columns before reading; never invent one")
    seen: list[tuple[str, str]] = []
    monkeypatch.setattr(flow_run, "run_top",
                        lambda task="", **k: seen.append((k.get("label", ""), task)))
    monkeypatch.setattr(flow_run, "restore_gate", lambda ws: None)
    monkeypatch.setattr(flow_run, "phase_gate_ok", lambda ws, ph: True)  # gate freezes
    results = iter([(False, "sqlite3.OperationalError: no such column: visited_at"), (True, "")])
    monkeypatch.setattr(flow_run, "run_gate", lambda ws, to, ph: next(results))

    solved, rounds = flow_run.drive_phase_free(
        2, workspace=tmp_path, profile=tmp_path, recorder=tmp_path, provider="p", model="m",
        run=tmp_path, timeout=10.0, thinking="off", attempts=5,
        memory=m, situation="building a report that reads from a database store")

    assert solved is True and rounds == 2
    coder_msgs = [t for lbl, t in seen if "coder" in lbl]
    assert any("inspect the real columns" in t for t in coder_msgs)   # grounded like a skill
    assert "no answer" in coder_msgs[0].lower()                        # with the agnostic caveat
    # the schema failure was distilled into a NEW general lesson and persisted — the run learned
    assert len(mem.Memory(tmp_path / "memory.jsonl").lessons) == 2


def _one_check_suite(tmp_path):
    import json
    import harness
    suite_dir = tmp_path / "suites" / "onecheck"
    (suite_dir / "tests").mkdir(parents=True)
    (suite_dir / "tests" / "test_add.py").write_text(
        "from add import add\n\ndef test_add():\n    assert add(2, 3) == 5\n\n"
        "def test_zero():\n    assert add(0, 0) == 0\n")
    (suite_dir / "expected.json").write_text(json.dumps([
        "grader_tests/test_add.py::test_add", "grader_tests/test_add.py::test_zero"]))
    (suite_dir / "task.md").write_text("Write add.py.\n")
    return harness.load_suite(tmp_path / "suites", "onecheck")


def test_hidden_grade_counts_passed_checks_on_a_partial_build(tmp_path):
    suite = _one_check_suite(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "add.py").write_text("def add(a, b):\n    return 0\n")
    assert flow_run.hidden_grade(workspace, suite) == (False, 1, 2)


def test_hidden_grade_passes_a_complete_build(tmp_path):
    suite = _one_check_suite(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "add.py").write_text("def add(a, b):\n    return a + b\n")
    assert flow_run.hidden_grade(workspace, suite) == (True, 2, 2)


def test_main_hands_loop_an_absolute_runs_dir(tmp_path, monkeypatch):
    # Pi runs with the workspace as its cwd, so a relative runs dir sends the
    # recorder and profile paths into the workspace, where they do not exist.
    seen = {}
    monkeypatch.setattr(flow_run, "loop", lambda name, **kw: seen.update(kw))
    monkeypatch.chdir(tmp_path)
    flow_run.main(["--suite", "easy", "--runs-dir", "runs/flow-x"])
    assert seen["runs_dir"].is_absolute()
    assert seen["runs_dir"] == tmp_path.resolve() / "runs" / "flow-x"


def test_revert_keeps_a_gate_frozen_after_the_last_checkpoint(tmp_path):
    # A phase's gate is frozen mid-phase, after the previous phase's checkpoint. A revert of a broken
    # round must not delete it, or the next round re-freezes a different (possibly weaker) gate.
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "app.py").write_text("good = 1\n")
    (ws / "plan" / "gate").mkdir(parents=True)
    (ws / "plan" / "gate" / "phase_1.py").write_text("def test_one():\n    assert True\n")
    flow_run.git_init_workspace(ws)
    flow_run.git_checkpoint(ws, "phase 1: PASS")
    frozen = "def test_two():\n    assert False\n"
    (ws / "plan" / "gate" / "phase_2.py").write_text(frozen)   # frozen after the checkpoint
    (ws / "app.py").write_text("BROKEN (((\n")
    flow_run.git_revert_to_checkpoint(ws)
    assert (ws / "app.py").read_text() == "good = 1\n"
    assert (ws / "plan" / "gate" / "phase_2.py").read_text() == frozen
    assert (ws / "plan" / "gate" / "phase_1.py").is_file()


def test_no_pi_session_in_the_flow_reads_stdin():
    # Pi with -p appends piped stdin to its prompt (the 2026-10-29 lesson-check
    # fault), so every Pi the flow starts gets no stdin.
    source = (Path(__file__).resolve().parents[1] / "flow_run.py").read_text()
    launches = re.findall(r"subprocess\.Popen\(argv[^)]*\)", source)
    assert launches and all("stdin=subprocess.DEVNULL" in call for call in launches), launches


def test_every_pi_in_the_flow_loads_the_think_tag_adapter():
    # Same reason as the harness: a host that returns reasoning as <think> text
    # must not change the model's context (research note 2026-10-29-lan-reasoning-leak).
    source = (Path(__file__).resolve().parents[1] / "flow_run.py").read_text()
    recorders = source.count('"-e", str(recorder)')
    assert recorders == 2
    assert source.count('"-e", str(harness.THINK_TAGS)') == recorders
