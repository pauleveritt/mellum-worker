"""RECORDING ONLY: a ladder run.json must carry the flat fields the scoreboard reads, derived from
the record already built (check/score/wall/backend) and the loaded remedy extensions — adding board
keys, changing nothing measured. `passed` is the rung's hidden-oracle verdict."""
import sys
from pathlib import Path

from ladder.run_ladder import board_fields

# The scoreboard lives in learn/code; load it to prove the fields are board-compatible end to end.
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "learn" / "code"))
import scoreboard  # noqa: E402


def test_board_fields_are_scoreboard_compatible(tmp_path):
    ext = tmp_path / "remedies" / "guard" / "no-live-server.ts"
    ext.parent.mkdir(parents=True)
    ext.write_text("export const x = 1\n")
    record = {
        "rung": 13,
        "backend": {"provider": "llamacpp", "model": "llamacpp/Mellum2.1-12B-A2.5B-Thinking"},
        "wall_seconds_untrusted": 512.4,
        "check": {"passed": True, "tests_unchanged": True},
        "score": {"requests": 72, "tool_calls_by_name": {"edit": 10, "bash": 5}},
    }
    fields = board_fields(record, extra_extensions=[ext])
    assert fields["suite"] == "medium"  # rung 13 is the four-phase medium tier
    assert fields["passed"] is True  # the hidden-oracle verdict, from check.passed
    assert fields["turns"] == 72 and fields["tool_calls"] == 15
    assert fields["wall"] == 512.4
    assert fields["model"] == "llamacpp/Mellum2.1-12B-A2.5B-Thinking"
    assert fields["remedies"] == ["guard/no-live-server"]

    record.update(fields)
    run_dir = tmp_path / "20261110T120000Z-rung13-tuned-direct-gate-r1"
    run_dir.mkdir()
    import json
    (run_dir / "run.json").write_text(json.dumps(record))
    entry = scoreboard.entry_from_run(run_dir)
    assert entry["suite"] == "medium" and entry["passed"] is True and entry["turns"] == 72
    assert "guard/no-live-server" in entry["stack"]


def test_board_fields_leave_unknown_rungs_off_the_board():
    fields = board_fields({"rung": 999, "check": {"passed": False}, "score": {}}, extra_extensions=[])
    assert fields["suite"] is None  # no tier -> the scoreboard never groups it under easy/medium/hard
    assert fields["passed"] is False
