"""tool_score: how cleanly a run calls its tools, counted from the trace.

A fault is a call the model got wrong, not a red test: an edit that matched nothing, a read of a missing file,
a bash command broken by its own shape, a search aimed outside the workspace."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tool_score import faults  # noqa: E402


def call(name, args, cid):
    return {"type": "tool_call", "toolName": name, "input": args, "toolCallId": cid}


def result(name, text, error, cid):
    return {"type": "tool_result", "toolName": name, "isError": error, "toolCallId": cid,
            "content": [{"type": "text", "text": text}]}


def test_faults_count_wrong_calls_but_not_red_tests_or_the_environment():
    rows = [call("edit", {"path": "a.py"}, "1"), result("edit", "Could not find the exact text in a.py.", True, "1"),
            call("bash", {"command": "uv run pytest"}, "2"), result("bash", "1 failed", True, "2"),
            call("bash", {"command": "cat -A a.py"}, "3"), result("bash", "cat: illegal option -- A", True, "3"),
            call("bash", {"command": "find / -name x"}, "4"), result("bash", "", False, "4"),
            call("read", {"path": "b.py"}, "5"), result("read", "ok", False, "5"),
            call("bash", {"command": "ruff check"}, "6"),
            result("bash", "ruff is not available and could not be downloaded", True, "6")]
    got = faults(rows, "/ws")
    assert got["calls"] == 6
    assert got["kinds"] == {"edit": 1, "flag": 1, "outside": 1}
    assert got["faults"] == 3
