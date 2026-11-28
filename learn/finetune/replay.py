"""Rebuild a run's workspace at the end of each phase from its trace (pure functions).

The harness grades only the final workspace, so a phase's failure can't be told apart
from a later phase breaking it. Replaying the successful `write` and `edit` calls on
the suite's base files gives each phase's own end state, which can then be graded.
Bash changes (mv, sed -i, uv add) are not replayed: a caller must check that the
replayed final state grades the same as the recorded run before trusting it.
"""


def _rel(path, workspace):
    if path.startswith(workspace.rstrip("/") + "/"):
        return path[len(workspace.rstrip("/")) + 1:]
    if path.startswith("/") or path.startswith(".."):
        return None
    return path[2:] if path.startswith("./") else path


def _apply(files, tool, inp, workspace):
    rel = _rel(str(inp.get("path") or ""), workspace)
    if not rel:
        return
    if tool == "write":
        files[rel] = inp.get("content") or ""
    elif tool == "edit" and rel in files:
        edits = inp.get("edits") or [{"oldText": inp.get("oldText"), "newText": inp.get("newText")}]
        text = files[rel]
        for e in edits:
            if e.get("oldText") is None or e["oldText"] not in text:
                return  # the tool would have refused; leave the file as it was
            text = text.replace(e["oldText"], e.get("newText") or "", 1)
        files[rel] = text


def phase_snapshots(base, rows, workspace):
    """One {relative path: text} dict per phase, in phase order."""
    files, snaps, calls, started = dict(base), [], {}, False
    for row in rows:
        kind = row.get("type")
        if kind == "instance_start":
            if started:
                snaps.append(dict(files))
            started = True
        elif kind == "tool_call" and row.get("toolName") in ("write", "edit"):
            calls[row.get("toolCallId")] = (row["toolName"], row.get("input") or {})
        elif kind == "tool_result" and row.get("toolCallId") in calls:
            tool, inp = calls.pop(row["toolCallId"])
            if not row.get("isError"):
                _apply(files, tool, inp, workspace)
    if started:
        snaps.append(dict(files))
    return snaps
