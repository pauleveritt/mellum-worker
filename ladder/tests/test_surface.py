"""A run record carries the system prompt and tool schemas the model was actually sent, so another harness or
test can reuse them without our source code."""
import hashlib
import json

from ladder.surface import load_surface, request_surface

TOOLS = [{"type": "function", "function": {"name": "read", "description": "Read a file",
                                           "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}}]


def req(system, tools=TOOLS, user="go"):
    return {"type": "provider_request", "payload": {
        "model": "m", "tools": tools,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}}


def test_the_first_request_gives_the_prompt_and_tools_with_hashes():
    events = [{"type": "agent_start"}, req("You are a worker."), {"type": "tool_call"}, req("You are a worker.", user="next")]
    s = request_surface(events)
    assert s["system_prompt"] == "You are a worker." and s["tools"] == TOOLS
    assert s["system_prompt_sha256"] == hashlib.sha256(b"You are a worker.").hexdigest()
    canon = json.dumps(TOOLS, sort_keys=True, separators=(",", ":")).encode()
    assert s["tools_sha256"] == hashlib.sha256(canon).hexdigest()
    assert s["surface_requests"] == 2 and s["distinct_system_prompts"] == 1 and s["distinct_tool_sets"] == 1


def test_a_prompt_or_tool_set_that_changes_mid_run_is_counted():
    s = request_surface([req("a"), req("b"), req("b", tools=[])])
    assert s["system_prompt"] == "a" and s["distinct_system_prompts"] == 2 and s["distinct_tool_sets"] == 2


def test_system_content_as_text_parts_and_an_anthropic_system_field_are_read():
    parts = {"type": "provider_request", "payload": {"messages": [
        {"role": "system", "content": [{"type": "text", "text": "one "}, {"type": "text", "text": "two"}]}]}}
    assert request_surface([parts])["system_prompt"] == "one two"
    top = {"type": "provider_request", "payload": {"system": [{"type": "text", "text": "sys"}], "messages": []}}
    assert request_surface([top])["system_prompt"] == "sys"


def test_no_request_gives_empty_fields_not_an_error():
    s = request_surface([{"type": "agent_start"}])
    assert s["system_prompt"] is None and s["tools"] == [] and s["surface_requests"] == 0


def test_load_surface_reads_a_record_or_a_manifest_and_checks_the_hashes(tmp_path):
    rec = {"rung": 1, **request_surface([req("You are a worker.")])}
    (tmp_path / "run.json").write_text(json.dumps(rec))
    assert load_surface(tmp_path / "run.json") == ("You are a worker.", TOOLS)
    (tmp_path / "manifest.json").write_text(json.dumps({"system_prompt": "hi", "tools": TOOLS}))
    assert load_surface(tmp_path / "manifest.json") == ("hi", TOOLS)  # hand-written: hashes optional
    rec["system_prompt"] = "edited"
    (tmp_path / "bad.json").write_text(json.dumps(rec))
    try:
        load_surface(tmp_path / "bad.json")
    except ValueError:
        return
    raise AssertionError("a prompt that no longer matches its hash was accepted")


def test_the_template_switches_sent_are_kept_with_the_surface():
    r = req("p"); r["payload"]["chat_template_kwargs"] = {"enable_thinking": False}
    assert request_surface([r])["chat_template_kwargs"] == {"enable_thinking": False}
    assert request_surface([req("p")])["chat_template_kwargs"] is None
