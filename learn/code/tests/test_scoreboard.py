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
        "model": "omlx/mellum-q4",
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
    assert e["model"] == "omlx/mellum-q4"
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
    row = board[("easy", "m", ("x",))]
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
    assert "easy" in text and "omlx/mellum-q4" in text
    # the record row shows the fastest pass (18 turns), not the 99-turn one
    assert "18" in text
    # turns and wall are both surfaced (the standing reporting rule)
    assert "turns" in text.lower() and "wall" in text.lower()


def test_an_entry_links_the_prompt_and_tools_it_ran_with_and_says_how_it_thought(tmp_path):
    tools = [{"type": "function", "function": {"name": "read"}}]
    d = _run_dir(tmp_path, "20261128T060429Z-easy-1ccf81", system_prompt="You are a worker.",
                 system_prompt_sha256="p" * 64, tools=tools, tools_sha256="t" * 64,
                 chat_template_kwargs={"enable_thinking": False}, tool_errors=92)
    e = scoreboard.entry_from_run(d)
    assert e["thinking"] == "off" and e["tool_errors"] == 92 and len(e["surface"]) == 16
    board = tmp_path / "board"
    scoreboard.record([d], board)
    saved = json.loads((board / "surfaces" / f"{e['surface']}.json").read_text())
    assert saved["system_prompt"] == "You are a worker." and saved["tools"] == tools
    assert saved["tools_sha256"] == "t" * 64 and saved["workspace_placeholder"] == "{workspace}"
    assert len(saved["system_prompt_sha256"]) == 64  # the hash of the stored (normalised) prompt
    assert len(list((board / "surfaces").iterdir())) == 1  # the same surface twice is stored once
    scoreboard.record([_run_dir(tmp_path, "again", system_prompt="You are a worker.", system_prompt_sha256="p" * 64,
                                tools=tools, tools_sha256="t" * 64)], board)
    assert len(list((board / "surfaces").iterdir())) == 1


def test_an_old_run_without_a_surface_still_records(tmp_path):
    e = scoreboard.entry_from_run(_run_dir(tmp_path, "old"))
    assert e["surface"] is None and e["thinking"] is None
    scoreboard.record([tmp_path / "old"], tmp_path / "board")
    assert not (tmp_path / "board" / "surfaces").exists()


def test_the_all_runs_table_shows_thinking_and_tool_errors():
    rows = scoreboard._run_rows([{"date": "2026-11-28", "model": "m", "stack": [], "passed": False, "turns": 10,
                                  "wall": 60, "id": "x", "thinking": "off", "tool_errors": 92}])
    assert "off" in rows[0] and "92" in rows[0]


def test_a_run_recorded_before_records_kept_the_surface_takes_it_from_its_trace(tmp_path):
    d = _run_dir(tmp_path, "older")
    req = {"type": "provider_request", "payload": {"tools": [{"type": "function", "function": {"name": "bash"}}],
           "chat_template_kwargs": {"enable_thinking": True},
           "messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "go"}]}}
    (d / "trace.jsonl").write_text(json.dumps(req) + "\n")
    e = scoreboard.entry_from_run(d)
    assert e["surface"] and e["thinking"] == "on"
    scoreboard.record([d], tmp_path / "board")
    saved = json.loads((tmp_path / "board" / "surfaces" / f"{e['surface']}.json").read_text())
    assert saved["system_prompt"] == "sys"


def test_the_weights_file_tells_tunes_apart_that_share_a_served_name(tmp_path):
    d = _run_dir(tmp_path, "new", model="llamacpp/Mellum2.1-12B-A2.5B-Thinking",
                 served={"model_path": "/m/tools-u15-Q4_K_M.gguf"})
    assert scoreboard.entry_from_run(d)["weights"] == "tools-u15-Q4_K_M.gguf"
    old = _run_dir(tmp_path, "old", model="llamacpp/Mellum2.1-12B-A2.5B-Thinking")
    assert scoreboard.entry_from_run(old)["weights"] is None
    assert scoreboard.entry_from_run(old, weights="Tsunami (tools update 15)")["weights"] == "Tsunami (tools update 15)"
    row = scoreboard._run_rows([{"model": "m", "weights": "tools-u15.gguf", "stack": [], "id": "x"}])[0]
    assert "tools-u15.gguf" in row


def test_records_never_blend_two_tunes_or_two_thinking_modes_under_one_served_name():
    base = {"suite": "easy", "model": "llamacpp/Mellum", "stack": [], "version": "v", "passed": True, "turns": 10, "wall": 1}
    entries = [dict(base, weights="base.gguf"), dict(base, weights="tsunami.gguf"),
               dict(base, weights="tsunami.gguf", thinking="off")]
    assert len(scoreboard._record_rows(entries)) == 3
    assert len(scoreboard.leaderboard(entries)) == 3


def test_runs_that_differ_only_by_workspace_path_share_one_stored_surface(tmp_path):
    tools = [{"type": "function", "function": {"name": "read"}}]
    board = tmp_path / "board"
    ids = []
    for name in ("r1", "r2"):
        d = tmp_path / "runs" / "batch" / name
        prompt = f"You are a worker.\nCurrent directory: {d / 'workspace'}\nGo."
        d.parent.mkdir(parents=True, exist_ok=True)
        rd = _run_dir(d.parent, name, system_prompt=prompt, system_prompt_sha256="x", tools=tools, tools_sha256="t")
        ids.append(scoreboard.entry_from_run(rd)["surface"])
        scoreboard.record([rd], board)
    assert ids[0] == ids[1]
    saved = json.loads((board / "surfaces" / f"{ids[0]}.json").read_text())
    assert saved["system_prompt"] == "You are a worker.\nCurrent directory: {workspace}\nGo."
    assert saved["workspace_placeholder"] == "{workspace}"
