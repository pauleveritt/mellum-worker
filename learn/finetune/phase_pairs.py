"""Cut a multi-phase harness trace into per-phase DPO segments (pure functions, no MLX).

The harness runs a suite's phases as one Pi session, one child process per phase, so
each `instance_start` in the trace opens a phase. A phase's segment is its last
`provider_request` context plus every assistant turn the model generated up to the end
of that phase. Rendering restores each assistant turn to what the model produced (its
reasoning as `reasoning_content`, its native tool calls) and marks only THIS phase's
turns as scored: earlier phases are context, so a later phase is never credited or
blamed for them.

Compaction shrinks the context but not the recorded turns, so turns are aligned from
the end: the context's k assistant messages are the last k recorded turns before the
final one.
"""
import json
import re


def segment_trace(rows):
    segs, acts, cur = [], [], None
    for row in rows:
        kind = row.get("type")
        if kind == "instance_start":
            if cur and cur["payload"] is not None:
                segs.append(cur)
            cur = {"phase": len(segs) + 1, "payload": None, "n_phase": 0}
        elif cur is None:
            continue
        elif kind == "provider_request":
            payload = row.get("payload") or {}
            if payload.get("messages"):
                cur["payload"] = payload
        elif kind == "message_end":
            msg = row.get("message")
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                acts.append(msg)
                cur["n_phase"] += 1
        if cur is not None:
            cur["acts"] = list(acts)
    if cur and cur["payload"] is not None:
        segs.append(cur)
    return segs


def _parts(act, kinds):
    out = []
    for part in act.get("content") or []:
        if isinstance(part, dict) and part.get("type") in kinds:
            text = part.get("text") or part.get("thinking")
            if text:
                out.append(text)
    return "\n".join(out)


def _calls(act):
    return [p for p in act.get("content") or [] if isinstance(p, dict) and p.get("type") == "toolCall"]


def render_segment(seg, cap=lambda text: text):
    """(messages, scored assistant indices) for a segment, or None if it can't align."""
    ctx, acts, n_phase = seg["payload"]["messages"], seg["acts"], seg["n_phase"]
    in_ctx = [i for i, m in enumerate(ctx) if m.get("role") == "assistant"]
    if n_phase < 1 or len(in_ctx) + 1 > len(acts):
        return None
    aligned = acts[len(acts) - len(in_ctx) - 1:]
    msgs, k = [], 0
    for m in ctx:
        m = dict(m)
        if m.get("role") == "assistant":
            a = aligned[k]; k += 1
            want = [t["function"]["name"] for t in m.get("tool_calls") or []]
            if want != [c.get("name") for c in _calls(a)]:
                return None
            reasoning = _parts(a, ("thinking", "reasoning"))
            if reasoning:
                m["reasoning_content"] = reasoning
            m["content"] = _parts(a, ("text",))
        elif m.get("role") == "tool":
            m["content"] = cap(m.get("content") if isinstance(m.get("content"), str)
                               else json.dumps(m.get("content")))
        msgs.append(m)
    last = aligned[-1]
    final = {"role": "assistant", "content": _parts(last, ("text",))}
    reasoning = _parts(last, ("thinking", "reasoning"))
    if reasoning:
        final["reasoning_content"] = reasoning
    calls = [{"id": c.get("id") or f"call_{i}", "type": "function",
              "function": {"name": c.get("name"), "arguments": json.dumps(c.get("arguments") or {})}}
             for i, c in enumerate(_calls(last))]
    if calls:
        final["tool_calls"] = calls
    msgs.append(final)
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    return msgs, ast[-min(n_phase, len(ast)):]


def phase_outcomes(run):
    """{phase: passed} from a harness run's per-module grade; {} if it can't be trusted."""
    if run.get("contaminated"):
        return {}
    out = {}
    for module, group in (run.get("check_groups") or {}).items():
        m = re.match(r"test_phase(\d+)_", module)
        if m and group.get("total"):
            out[int(m.group(1))] = group.get("missing", 0) == 0
    return out
