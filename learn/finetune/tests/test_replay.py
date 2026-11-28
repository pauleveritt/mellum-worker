"""replay: rebuild each phase's workspace from the trace's successful write/edit calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from replay import phase_snapshots  # noqa: E402

WS = "/r/run1/workspace"


def call(i, tool, inp):
    return {"type": "tool_call", "toolName": tool, "toolCallId": f"c{i}", "input": inp}


def res(i, err=False):
    return {"type": "tool_result", "toolCallId": f"c{i}", "isError": err, "content": []}


ROWS = [
    {"type": "instance_start"},
    call(1, "write", {"path": "app.py", "content": "a = 1\n"}), res(1),
    {"type": "instance_start"},
    call(2, "edit", {"path": f"{WS}/app.py", "edits": [{"oldText": "a = 1", "newText": "a = 2"}]}), res(2),
    call(3, "edit", {"path": "app.py", "edits": [{"oldText": "nope", "newText": "x"}]}), res(3, err=True),
    call(4, "write", {"path": "templates/t.html", "content": "<p>"}), res(4),
]


def test_snapshots_follow_phases_and_apply_only_successful_calls():
    snaps = phase_snapshots({"pyproject.toml": "[project]"}, ROWS, WS)
    assert snaps[0] == {"pyproject.toml": "[project]", "app.py": "a = 1\n"}
    assert snaps[1]["app.py"] == "a = 2\n"  # absolute path in the workspace, failed edit skipped
    assert snaps[1]["templates/t.html"] == "<p>"


def test_old_style_single_edit_arguments():
    rows = ROWS[:3] + [{"type": "instance_start"},
                       call(5, "edit", {"path": "app.py", "oldText": "a = 1", "newText": "a = 3"}), res(5)]
    assert phase_snapshots({}, rows, WS)[1]["app.py"] == "a = 3\n"


def test_a_path_outside_the_workspace_is_ignored():
    rows = ROWS[:3] + [call(6, "write", {"path": "/etc/x", "content": "no"}), res(6)]
    assert "/etc/x" not in phase_snapshots({}, rows, WS)[0] and len(phase_snapshots({}, rows, WS)[0]) == 1
