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


def test_trusted_outcomes_drop_failures_a_later_phase_could_have_caused():
    from phase_pairs import trusted_outcomes
    # final-state grading: phase 4 broke the import, so 2 and 3 read as failed too
    assert trusted_outcomes({2: False, 3: False, 4: False}, reached=4) == {4: False}
    assert trusted_outcomes({2: True, 3: False, 4: False}, reached=4) == {2: True, 4: False}
    assert trusted_outcomes({2: True, 3: False, 4: False}, reached=3) == {2: True, 3: False}


def test_grader_seen_ignores_the_suite_base_but_not_the_grader():
    from phase_pairs import grader_seen
    assert not grader_seen("ran ../../learn/code/suites/medium/base/tests/test_home.py", "medium", "CANARY-1")
    assert grader_seen("cat learn/code/suites/medium/grader/test_phase1_home.py", "medium", "CANARY-1")
    assert grader_seen("saw CANARY-1 in output", "medium", "CANARY-1")
    assert grader_seen("cat grader_tests/test_phase1_home.py", "medium", None)


def test_a_request_cut_off_by_the_deadline_does_not_break_alignment():
    rows = ROWS + [req([SYS, U1, hist("a1"), TOOL, hist("a2"), TOOL, U2, hist("b1"), TOOL, hist("b2"), TOOL])]
    seg = segment_trace(rows)[1]
    assert render_segment(seg) is not None and seg["n_phase"] == 2


def test_single_phase_suites_grade_on_all_their_tests():
    run = {"contaminated": False, "check_groups": {"test_review.py": {"missing": 0, "total": 6}}}
    assert phase_outcomes(run) == {1: True}
    run["check_groups"]["test_review.py"]["missing"] = 2
    assert phase_outcomes(run) == {1: False}


def result(tool, err, text="ok"):
    return {"type": "tool_result", "toolName": tool, "isError": err, "content": [{"type": "text", "text": text}]}


STEP_ROWS = [
    {"type": "instance_start"},
    req([SYS, U1]), act("a1", tool="read"), result("read", False),
    req([SYS, U1, hist("a1", tool="read"), TOOL]), act("bad", tool="edit"),
    result("edit", True, "Could not find the exact text in app.py."),
    req([SYS, U1, hist("a1", tool="read"), TOOL, hist("bad", tool="edit"), TOOL]), act("fix", tool="read"),
    result("read", False),
    req([SYS, U1, hist("a1", tool="read"), TOOL, hist("bad", tool="edit"), TOOL, hist("fix", tool="read"), TOOL]),
    act("done", tool="edit"), result("edit", False),
]


def test_step_pairs_pair_a_failed_call_with_the_recovery_that_followed():
    from phase_pairs import step_pairs
    seg = segment_trace(STEP_ROWS)[0]
    assert step_pairs(seg) == [(1, 2)]  # act 1 (the failed edit) vs act 2 (the read that recovered)


def test_step_pairs_skip_environment_errors_and_unrecovered_failures():
    from phase_pairs import step_pairs
    rows = [r if not (r.get("type") == "tool_result" and r["isError"]) else
            result("edit", True, "fd is not available and could not be downloaded") for r in STEP_ROWS]
    assert step_pairs(segment_trace(rows)[0]) == []
    rows = STEP_ROWS[:6]  # the failure is the last thing in the trace: no recovery to prefer
    assert step_pairs(segment_trace(rows)[0]) == []


def test_render_step_shares_the_prefix_and_keeps_only_the_tool_call():
    from phase_pairs import render_step
    seg = segment_trace(STEP_ROWS)[0]
    chosen, rejected = render_step(seg, 1, 2)
    assert chosen[:-1] == rejected[:-1]  # same context up to the failed call
    assert [m["role"] for m in chosen[:-1]] == ["system", "user", "assistant", "tool"]
    assert rejected[-1]["tool_calls"][0]["function"]["name"] == "edit"
    assert chosen[-1]["tool_calls"][0]["function"]["name"] == "read"
    # both sides keep the thinking the model wrote BEFORE the failed call (it never saw the error), so the
    # turn has the model's own format; only the call differs
    assert chosen[-1]["reasoning_content"] == rejected[-1]["reasoning_content"] == "why"
    assert chosen[-1]["content"] == rejected[-1]["content"]


def test_a_provider_error_turn_is_not_counted_as_an_act():
    # a connection error ends a turn with no content; Pi retries the same request and the
    # failed turn never enters the context, so it must not shift the alignment
    err = {"type": "message_end", "message": {"role": "assistant", "content": [], "stopReason": "error"}}
    rows = ROWS[:3] + [ROWS[3], err] + ROWS[3:]
    segs = segment_trace(rows)
    assert [s["n_phase"] for s in segs] == [2, 2]
    assert render_segment(segs[1]) is not None


def test_verified_phase_grades_replace_the_final_state_guess():
    from phase_pairs import best_outcomes
    final = {2: False, 3: False, 4: False}
    graded = {"verified": True, "phases": {"1": True, "2": True, "3": False, "4": False}}
    assert best_outcomes(final, graded, reached=4) == {1: True, 2: True, 3: False, 4: False}
    assert best_outcomes(final, {"verified": False, "phases": {}}, reached=4) == {4: False}
    assert best_outcomes(final, None, reached=4) == {4: False}


def test_tool_call_arguments_keep_non_ascii_like_the_template():
    from phase_pairs import render_step
    rows = [dict(r) for r in STEP_ROWS]
    rows[5] = {"type": "message_end", "message": {"role": "assistant", "content": [
        {"type": "thinking", "thinking": "why"},
        {"type": "toolCall", "name": "edit", "id": "c", "arguments": {"path": "café.py"}}]}}
    _chosen, rejected = render_step(segment_trace(rows)[0], 1, 2)
    assert "café.py" in rejected[-1]["tool_calls"][0]["function"]["arguments"]


def test_scored_span_can_start_at_the_tool_call():
    from phase_pairs import scored_span
    text = "<|im_start|>assistant\n<think>\nplan\n</think>\n\n<tool_call>\n{}\n</tool_call><|im_end|>"
    start, end = len("<|im_start|>assistant\n"), len(text)
    assert scored_span(text, start, end, calls_only=False) == (start, end)
    assert text[slice(*scored_span(text, start, end, calls_only=True))].startswith("<tool_call>")


def test_scored_span_ignores_a_tool_call_written_inside_the_thinking():
    from phase_pairs import scored_span
    text = '<think>\nmaybe <tool_call>{"name": "read"}</tool_call>\n</think>\n\n<tool_call>{"name": "bash"}</tool_call><|im_end|>'
    s, e = scored_span(text, 0, len(text), calls_only=True)
    assert text[s:e] == '<tool_call>{"name": "bash"}</tool_call><|im_end|>'


def test_scored_span_without_a_call_scores_only_the_end_of_the_turn():
    """A final answer against a tool call (cleanup pairs): only the choice to stop differs, not the thinking."""
    from phase_pairs import scored_span
    text = "<think>\nall tests pass\n</think>\n\nDone.<|im_end|>"
    s, e = scored_span(text, 0, len(text), calls_only=True)
    assert text[s:e] == "<|im_end|>"
