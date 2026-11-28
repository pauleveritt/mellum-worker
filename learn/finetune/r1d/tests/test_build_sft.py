"""Supervised examples in the DeepSeek tool format, cut from passing runs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from build_sft import examples, render  # noqa: E402

TOOLS = [{"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}]
CALL = [{"id": "c0", "type": "function", "function": {"name": "read", "arguments": "{\"path\": \"a.py\"}"}}]
MSGS = [
    {"role": "system", "content": "Work."},
    {"role": "user", "content": "Fix a.py."},
    {"role": "assistant", "content": "", "reasoning_content": "Look first.", "tool_calls": CALL},
    {"role": "tool", "content": "x = 1"},
    {"role": "assistant", "content": "Done.", "reasoning_content": "It is fine."},
]


def test_one_example_per_scored_step_prompt_ends_in_open_thinking():
    ex = examples(MSGS, [2, 4], TOOLS, failed=set(), modes=("on",))
    assert len(ex) == 2
    assert ex[0]["prompt"].endswith("<｜User｜>Fix a.py.<｜Assistant｜><｜think▁on｜><think>\n")
    assert ex[0]["completion"] == ("Look first.\n</think>\n\n<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function"
                                   "<｜tool▁sep｜>read\n```json\n{\"path\": \"a.py\"}\n```<｜tool▁call▁end｜>"
                                   "<｜tool▁calls▁end｜><｜end▁of▁sentence｜>")
    assert ex[1]["prompt"].endswith("<｜tool▁output▁begin｜>x = 1<｜tool▁output▁end｜><｜tool▁outputs▁end｜>"
                                    "<｜Assistant｜><｜think▁on｜><think>\n")
    assert ex[1]["completion"] == "It is fine.\n</think>\n\nDone.<｜end▁of▁sentence｜>"


def test_prompt_plus_completion_is_the_full_rendered_conversation_with_thinking_on_the_last_turn():
    ex = examples(MSGS, [4], TOOLS, failed=set(), modes=("on",))[0]
    whole = render(MSGS, TOOLS)
    assert (ex["prompt"] + ex["completion"]).replace("<｜think▁on｜><think>\nIt is fine.\n</think>\n\n", "") == whole


def test_a_step_whose_call_failed_is_not_taught():
    assert [e["step"] for e in examples(MSGS, [2, 4], TOOLS, failed={2}, modes=("on",))] == [4]


def test_history_keeps_no_thinking():
    ex = examples(MSGS, [4], TOOLS, failed=set())[0]
    assert "Look first." not in ex["prompt"]


def test_held_out_suites_are_refused():
    from build_sft import held_out
    for s in ("easy", "medium", "hard", "satyrn-agentclinic-repair-depth-2", "py3.14-zstd-archive"):
        assert held_out(s), s
    for s in ("tt-log-analyser", "py3.14-zstd-bytes", "satyrn-format_number"):
        assert not held_out(s), s


def test_each_step_gives_both_modes_and_off_drops_only_the_thinking():
    on, off = examples(MSGS, [4], TOOLS, failed=set())
    assert (on["mode"], off["mode"]) == ("on", "off")
    assert off["prompt"].endswith("<｜Assistant｜><｜think▁off｜><think>\n\n</think>\n\n")
    assert off["completion"] == "Done.<｜end▁of▁sentence｜>"
    assert on["completion"].endswith(off["completion"])
    assert on["prompt"].removesuffix("<｜think▁on｜><think>\n") == off["prompt"].removesuffix("<｜think▁off｜><think>\n\n</think>\n\n")
