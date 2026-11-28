"""surface_probe.py scores one reply against the tool set a manifest declares."""
import json

from surface_probe import request_body, score_reply

TOOLS = [{"type": "function", "function": {"name": "read", "parameters": {
    "type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]


def call(name, args):
    return {"tool_calls": [{"function": {"name": name, "arguments": args}}]}


def test_a_well_formed_call_to_a_declared_tool_scores_ok():
    assert score_reply(call("read", json.dumps({"path": "a.py"})), TOOLS) == {"call": True, "ok": True, "fault": None}


def test_each_kind_of_faulty_call_is_named():
    assert score_reply({"content": "I would read it"}, TOOLS)["fault"] == "no call"
    assert score_reply(call("write", '{"path": "a"}'), TOOLS)["fault"] == "unknown tool"
    assert score_reply(call("read", "{bad json"), TOOLS)["fault"] == "bad arguments"
    assert score_reply(call("read", "[1]"), TOOLS)["fault"] == "bad arguments"
    assert score_reply(call("read", "{}"), TOOLS)["fault"] == "missing required"


def test_the_request_uses_the_manifest_prompt_and_tools_and_the_thinking_switch():
    body = request_body("You are X.", TOOLS, "List files.", "m", thinking=False)
    assert body["messages"] == [{"role": "system", "content": "You are X."}, {"role": "user", "content": "List files."}]
    assert body["tools"] == TOOLS and body["model"] == "m"
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert request_body(None, TOOLS, "hi", "m", thinking=None)["messages"] == [{"role": "user", "content": "hi"}]
    assert "chat_template_kwargs" not in request_body(None, TOOLS, "hi", "m", thinking=None)
