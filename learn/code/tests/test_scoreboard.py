"""The scoreboard: merge-friendly run records (one file per run) and a computed leaderboard."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scoreboard


def _run_dir(tmp, name, **over):
    d = tmp / name
    d.mkdir(parents=True)
    rec = {
        "suite": "easy",
        "arm": "bare",
        "model": "llamacpp/mellum-q4",
        "remedies": ["tool/background-long-commands"],
        "extensions": [
            {"path": "/x/remedies/tool/background-long-commands.ts", "sha256": "a"},
            {"path": "/x/extensions/mellum-acceptance.ts", "sha256": "b"},
            {"path": "/x/extensions/mellum-verify.ts", "sha256": "c"},
            {"path": "/x/extensions/mellum-recorder.ts", "sha256": "d"},
        ],
        "machine": "Apple M3 Max, 48 GiB",
        "passed": True,
        "turns": 18,
        "tool_calls": 17,
        "wall": 57.7,
        "missing_checks": [],
    }
    rec.update(over)
    (d / "run.json").write_text(json.dumps(rec))
    return d


def test_entry_from_run_pulls_the_fields_and_a_sorted_stack(tmp_path):
    e = scoreboard.entry_from_run(_run_dir(tmp_path, "20261031T080329Z-easy-74a7db"))
    assert e["suite"] == "easy"
    assert e["model"] == "llamacpp/mellum-q4"
    assert e["passed"] is True
    assert e["turns"] == 18 and round(e["wall"]) == 58
    assert e["id"] == "20261031T080329Z-easy-74a7db"
    # the stack is the remedies + mellum extension names, recorder dropped, sorted (stable key)
    assert e["stack"] == sorted(e["stack"]), "stack must be sorted for a stable group key"
    assert "tool/background-long-commands" in e["stack"]
    assert "mellum-acceptance" in e["stack"] and "mellum-verify" in e["stack"]
    assert not any("recorder" in s for s in e["stack"]), "the recorder is harness plumbing, not a remedy"


def test_stack_includes_a_non_bare_arm_so_a_worker_run_never_reads_as_bare(tmp_path):
    e = scoreboard.entry_from_run(_run_dir(tmp_path, "w", arm="worker", remedies=[], extensions=[]))
    assert "arm:worker" in e["stack"], e["stack"]
    bare = scoreboard.entry_from_run(_run_dir(tmp_path, "b", arm="bare", remedies=[], extensions=[]))
    assert bare["stack"] == [], "a bare run with no units stays bare"


def test_stack_label_normalizes_retired_unit_names_to_their_current_ones(tmp_path):
    # Guard units were renamed (8ed336f); recorded run.json evidence keeps the old
    # names and is immutable. The board must show one vocabulary so the same stack
    # groups together, without rewriting the evidence.
    old = scoreboard.entry_from_run(_run_dir(tmp_path, "old", extensions=[], remedies=[
        "guard/break-repeat-loops", "guard/stay-in-workspace", "guard/block-foreground-server"]))
    assert old["stack"] == [
        "guard/foreground-server", "guard/outside-workspace", "guard/repeat-loops"], old["stack"]
    new = scoreboard.entry_from_run(_run_dir(tmp_path, "new", extensions=[], remedies=[
        "guard/repeat-loops", "guard/outside-workspace", "guard/foreground-server"]))
    assert old["stack"] == new["stack"], "retired and current names must group as one stack"


def test_load_entries_folds_retired_names_in_already_stored_stacks(tmp_path):
    # Entries recorded before the rename kept the old names in their stored stack.
    # Loading must fold them so an old entry groups with its current-name twin
    # instead of forming a separate, phantom stack on the board.
    board = tmp_path / "board"
    (board / "entries").mkdir(parents=True)
    (board / "entries" / "old.json").write_text(json.dumps({
        "suite": "hard", "model": "m", "passed": True, "turns": 1, "wall": 1.0,
        "stack": ["guard/stay-in-workspace", "guard/break-repeat-loops",
                  "guard/refuse-whole-file-rewrite"]}))
    e = scoreboard.load_entries(board)[0]
    assert e["stack"] == [
        "guard/outside-workspace", "guard/repeat-loops", "guard/whole-file-rewrite"], e["stack"]


def test_record_writes_one_file_per_run_and_is_idempotent(tmp_path):
    board = tmp_path / "board"
    a = _run_dir(tmp_path, "run-a")
    b = _run_dir(tmp_path, "run-b", turns=20)
    scoreboard.record([a, b], board)
    files = sorted(p.name for p in (board / "entries").glob("*.json"))
    assert files == ["run-a.json", "run-b.json"], "one file per run -> merge-friendly"
    # re-recording the same run overwrites its own file; no duplicate, no shared file touched
    scoreboard.record([a], board)
    assert sorted(p.name for p in (board / "entries").glob("*.json")) == ["run-a.json", "run-b.json"]


def test_leaderboard_ranks_passes_shorter_first(tmp_path):
    entries = [
        {"id": "slow", "suite": "easy", "model": "m", "stack": ["x"], "passed": True, "turns": 99, "wall": 539.0},
        {"id": "fast", "suite": "easy", "model": "m", "stack": ["x"], "passed": True, "turns": 17, "wall": 76.0},
        {"id": "mid", "suite": "easy", "model": "m", "stack": ["x"], "passed": True, "turns": 20, "wall": 67.0},
        {"id": "faildrop", "suite": "easy", "model": "m", "stack": ["x"], "passed": False, "turns": 5, "wall": 10.0},
    ]
    board = scoreboard.leaderboard(entries)
    row = board[("easy", "m", ("x",), ("unknown", "", ""))]
    assert row["best"]["id"] == "fast", "fewest-turn pass is the record holder"
    assert row["passed"] == 3 and row["total"] == 4
    # a failing run with few turns never wins the record
    assert row["best"]["id"] != "faildrop"


def test_consolidate_writes_a_page_showing_the_record_per_config(tmp_path):
    board = tmp_path / "board"
    fast = _run_dir(tmp_path, "20261031T080329Z-easy-74a7db", turns=18, wall=58.0)
    slow = _run_dir(tmp_path, "20261031T074907Z-easy-ec96b0", turns=99, wall=539.0)
    scoreboard.record([fast, slow], board)
    page = tmp_path / "scoreboard.md"
    scoreboard.consolidate(board, page)
    text = page.read_text()
    assert "Scoreboard" in text
    assert "easy" in text and "llamacpp/mellum-q4" in text
    # the record row shows the fastest pass (18 turns), not the 99-turn one
    assert "18" in text
    # turns and wall are both surfaced (the standing reporting rule)
    assert "turns" in text.lower() and "wall" in text.lower()
