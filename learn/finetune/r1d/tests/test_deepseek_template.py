"""The DeepSeek tool-call template: the exact text the model is trained on and served with."""
import json
from pathlib import Path

import jinja2

T = Path(__file__).parent.parent / "deepseek_tools.jinja"
TOOLS = [{"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}]
CALL = {"type": "function", "function": {"name": "read", "arguments": "{\"path\": \"a.py\"}"}}


def render(messages, tools=TOOLS, gen=False):
    env = jinja2.Environment()
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    return env.from_string(T.read_text()).render(messages=messages, tools=tools, add_generation_prompt=gen,
                                                 bos_token="<BOS>")


def test_a_call_with_text_keeps_both_and_args_are_not_double_encoded():
    out = render([{"role": "user", "content": "Fix it."},
                  {"role": "assistant", "content": "Reading.", "tool_calls": [CALL]}])
    assert out.endswith('<｜User｜>Fix it.<｜Assistant｜>Reading.<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function'
                        '<｜tool▁sep｜>read\n```json\n{"path": "a.py"}\n```<｜tool▁call▁end｜><｜tool▁calls▁end｜>'
                        '<｜end▁of▁sentence｜>')


def test_tool_results_close_before_the_next_turn_and_reopen_after():
    out = render([{"role": "assistant", "content": "", "tool_calls": [CALL]}, {"role": "tool", "content": "r1"},
                  {"role": "tool", "content": "r2"}, {"role": "assistant", "content": "", "tool_calls": [CALL]},
                  {"role": "tool", "content": "r3"}], gen=True)
    assert ("<｜tool▁outputs▁begin｜><｜tool▁output▁begin｜>r1<｜tool▁output▁end｜><｜tool▁output▁begin｜>r2"
            "<｜tool▁output▁end｜><｜tool▁outputs▁end｜><｜Assistant｜>") in out
    assert out.endswith("<｜tool▁output▁begin｜>r3<｜tool▁output▁end｜><｜tool▁outputs▁end｜><｜Assistant｜><think>\n")


def test_tools_preamble_then_system_and_thinking_is_dropped_from_history():
    out = render([{"role": "system", "content": "Be brief."},
                  {"role": "assistant", "content": "<think>x</think>done"}])
    assert out.startswith("<BOS>You can call any of the following function tools")
    assert '"name": "read"' in out and "Be brief.<｜Assistant｜>done<｜end▁of▁sentence｜>" in out


def test_no_tools_no_preamble():
    assert render([{"role": "user", "content": "hi"}], tools=None) == "<BOS><｜User｜>hi"
