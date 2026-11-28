"""The tool-call chat template renders the exact text the 1.5B model will be trained on."""
import json
from pathlib import Path

import jinja2

TEMPLATE = Path(__file__).parent.parent / "toolcall.jinja"
TOOLS = [{"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}]


def render(messages, tools=TOOLS, gen=False):
    env = jinja2.Environment()
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    return env.from_string(TEMPLATE.read_text()).render(
        messages=messages, tools=tools, add_generation_prompt=gen, bos_token="<BOS>")


def test_a_tool_round_trip():
    out = render([
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": "Fix it."},
        {"role": "assistant", "content": "<think>look</think>",
         "tool_calls": [{"type": "function", "function": {"name": "read", "arguments": "{\"path\": \"a.py\"}"}}]},
        {"role": "tool", "content": "x = 1"},
    ], gen=True)
    assert out.startswith("<BOS>Be brief.\n\n# Tools")
    assert '{"type": "function", "function": {"name": "read"' in out
    assert out.endswith(
        '<｜User｜>Fix it.<｜Assistant｜>\n<tool_call>\n{"name": "read", "arguments": {"path": "a.py"}}\n</tool_call>'
        '<｜end▁of▁sentence｜><｜User｜><tool_response>\nx = 1\n</tool_response><｜Assistant｜><think>\n')


def test_a_second_user_turn_after_tools_has_no_stray_end_token():
    out = render([{"role": "user", "content": "a"}, {"role": "assistant", "content": "ok", "tool_calls": []},
                  {"role": "tool", "content": "r"}, {"role": "user", "content": "b"}])
    assert "</tool_response><｜User｜>b" in out


def test_two_tool_results_share_one_user_turn():
    out = render([{"role": "tool", "content": "r1"}, {"role": "tool", "content": "r2"}])
    assert out.endswith("<｜User｜><tool_response>\nr1\n</tool_response>\n<tool_response>\nr2\n</tool_response>")


def test_no_tools_no_tools_block():
    assert "# Tools" not in render([{"role": "user", "content": "hi"}], tools=None)
