"""The system prompt and tool schemas a run actually sent the model, read from its trace.

Pi assembles both at run time (its built-in tools plus whatever extensions and remedy units are loaded), so a list
of extensions and their hashes says how to rebuild them only with this repository at that commit. A record that
carries the resolved text and schemas can be reused anywhere: by another harness, or by a test that wants Pi's (or
OpenCode's) prompt and tool set against some other model. Standard library only, like the rest of the ladder.
"""
import hashlib
import json
from pathlib import Path


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _system(payload):
    if "system" in payload:  # Anthropic-style requests carry it beside the messages
        return _text(payload["system"])
    for message in payload.get("messages", []):
        if message.get("role") in ("system", "developer"):
            return _text(message.get("content"))
    return None


def _canon(tools):
    return json.dumps(tools, sort_keys=True, separators=(",", ":"))


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def request_surface(events):
    """{system_prompt, tools, their sha256s, how many requests, how many distinct prompts and tool sets}.

    The prompt and tools are the first request's; the distinct counts say whether later requests changed them."""
    prompts, tool_sets, first = set(), set(), None
    for event in events:
        if event.get("type") != "provider_request":
            continue
        payload = event.get("payload", {})
        system, tools = _system(payload), payload.get("tools") or []
        if first is None:
            first = (system, tools, payload.get("chat_template_kwargs"))
        prompts.add(system)
        tool_sets.add(_canon(tools))
    system, tools, kwargs = first if first else (None, [], None)
    return {
        "system_prompt": system,
        "system_prompt_sha256": _sha(system) if system is not None else None,
        "tools": tools,
        "tools_sha256": _sha(_canon(tools)),
        "chat_template_kwargs": kwargs,  # e.g. the thinking switch, which changes what the model sees
        "surface_requests": sum(1 for e in events if e.get("type") == "provider_request"),
        "distinct_system_prompts": len(prompts),
        "distinct_tool_sets": len(tool_sets),
    }


def load_surface(path):
    """(system_prompt, tools) from a run record or a hand-written manifest; ValueError if a hash no longer matches."""
    record = json.loads(Path(path).read_text())
    system, tools = record.get("system_prompt"), record.get("tools") or []
    if system is not None and record.get("system_prompt_sha256") not in (None, _sha(system)):
        raise ValueError(f"{path}: system_prompt does not match system_prompt_sha256")
    if record.get("tools_sha256") not in (None, _sha(_canon(tools))):
        raise ValueError(f"{path}: tools do not match tools_sha256")
    return system, tools
