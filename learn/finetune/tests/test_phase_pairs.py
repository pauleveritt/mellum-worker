"""phase_pairs: cut a multi-phase harness trace into per-phase training segments."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from phase_pairs import phase_outcomes, segment_trace, render_segment  # noqa: E402


def req(messages):
    return {"type": "provider_request", "payload": {"messages": messages, "tools": [{"t": 1}]}}


def act(text, tool="bash", think="why"):
    return {"type": "message_end", "message": {"role": "assistant", "content": [
        {"type": "thinking", "thinking": think, "text": think},
        {"type": "text", "text": text},
        {"type": "toolCall", "name": tool, "id": "c", "arguments": {"command": text}}]}}


def hist(text, tool="bash"):
    return {"role": "assistant", "content": None,
            "tool_calls": [{"function": {"name": tool, "arguments": "{}"}}]}


SYS = {"role": "system", "content": "s"}
U1 = {"role": "user", "content": "Phase 1"}
U2 = {"role": "user", "content": "Phase 2"}
TOOL = {"role": "tool", "content": "out"}

ROWS = [
    {"type": "instance_start"},
    req([SYS, U1]), act("a1"),
    req([SYS, U1, hist("a1"), TOOL]), act("a2"),
    {"type": "instance_start"},
    req([SYS, U1, hist("a1"), TOOL, hist("a2"), TOOL, U2]), act("b1"),
    req([SYS, U1, hist("a1"), TOOL, hist("a2"), TOOL, U2, hist("b1"), TOOL]), act("b2"),
]


def test_segments_follow_instance_starts():
    segs = segment_trace(ROWS)
    assert [s["phase"] for s in segs] == [1, 2]
    assert [s["n_phase"] for s in segs] == [2, 2]
    assert len(segs[1]["acts"]) == 4  # all acts up to the end of phase 2


def test_render_scores_only_the_current_phase():
    seg = segment_trace(ROWS)[1]
    msgs, scored = render_segment(seg)
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    assert len(ast) == 4
    assert scored == ast[2:]  # b1 and b2 only, never phase 1's turns
    assert msgs[ast[2]]["reasoning_content"] == "why" and msgs[-1]["tool_calls"]


def test_render_aligns_after_compaction():
    # compaction drops a1/a2 from the context; acts still hold all four
    rows = ROWS[:6] + [req([SYS, {"role": "user", "content": "summary"}, U2]), act("b1"),
                       req([SYS, {"role": "user", "content": "summary"}, U2, hist("b1"), TOOL]), act("b2")]
    msgs, scored = render_segment(segment_trace(rows)[1])
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    assert len(ast) == 2 and scored == ast


def test_render_rejects_mismatched_tool_names():
    rows = ROWS[:-1] + [act("b2", tool="write")]
    rows[-3] = req([SYS, U1, hist("a1"), TOOL, hist("a2"), TOOL, U2, hist("b1", tool="read"), TOOL])
    assert render_segment(segment_trace(rows)[1]) is None


def test_phase_outcomes_from_check_groups():
    run = {"contaminated": False, "check_groups": {
        "test_phase1_home.py": {"missing": 0, "total": 4},
        "test_phase2_board.py": {"missing": 2, "total": 6}}}
    assert phase_outcomes(run) == {1: True, 2: False}
    assert phase_outcomes({**run, "contaminated": True}) == {}


def test_worked_counts_only_writes_and_edits_in_this_phase():
    from phase_pairs import worked
    seg = segment_trace(ROWS)[1]
    assert not worked(seg)  # phase 2 only ran bash
    rows = ROWS[:-1] + [act("b2", tool="edit")]
    assert worked(segment_trace(rows)[1])
    rows = ROWS[:4] + [act("a2", tool="write")] + ROWS[5:]
    assert not worked(segment_trace(rows)[1])  # phase 1's write is not phase 2's work
