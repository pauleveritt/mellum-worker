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
    # A request only counts once its reply arrives: a request the deadline cut off
    # has no reply, and taking its context would shift every turn by one.
    segs, acts, errs, cur, pending = [], [], {}, None, None
    for row in rows:
        kind = row.get("type")
        if kind == "instance_start":
            if cur and cur["payload"] is not None:
                segs.append(cur)
            cur, pending = {"phase": len(segs) + 1, "payload": None, "n_phase": 0}, None
        elif cur is None:
            continue
        elif kind == "provider_request":
            payload = row.get("payload") or {}
            if payload.get("messages"):
                pending = payload
        elif kind == "message_end":
            msg = row.get("message")
            if (isinstance(msg, dict) and msg.get("role") == "assistant"
                    and not (msg.get("stopReason") in ("error", "aborted") and not msg.get("content"))):
                # a provider error turn has no content and never enters the context: Pi
                # retries the same request, so counting it would shift every turn by one
                acts.append(msg)
                cur["n_phase"] += 1
                if pending is not None:
                    cur["payload"], pending = pending, None
        elif kind == "tool_result" and acts:
            text = "".join(p.get("text", "") for p in row.get("content") or [] if isinstance(p, dict))
            errs.setdefault(len(acts) - 1, []).append((row.get("toolName"), bool(row.get("isError")), text[:500]))
        if cur is not None:
            cur["acts"], cur["errs"] = list(acts), dict(errs)
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
              "function": {"name": c.get("name"), "arguments": json.dumps(c.get("arguments") or {}, ensure_ascii=False)}}
             for i, c in enumerate(_calls(last))]
    if calls:
        final["tool_calls"] = calls
    msgs.append(final)
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    return msgs, ast[-min(n_phase, len(ast)):]


ENV_ERRORS = ("not available and could not be downloaded",)


def step_pairs(seg):
    """(failed act, recovering act) index pairs within this phase.

    A failed act is one whose non-bash tool call errored for a reason the model caused
    (a missing file, an edit that matched nothing), not the environment (a tool binary
    the sandbox lacks). Bash is left out: a failing test run is normal TDD, not a bad call.
    The recovery is the very next act, kept only if every one of its calls succeeded."""
    acts, errs = seg["acts"], seg.get("errs") or {}
    start, out = len(acts) - seg["n_phase"], []
    for k in range(start, len(acts) - 1):
        bad = [e for e in errs.get(k, []) if e[1] and e[0] != "bash" and not any(x in e[2] for x in ENV_ERRORS)]
        nxt = errs.get(k + 1, [])
        if bad and nxt and not any(e[1] for e in nxt):
            out.append((k, k + 1))
    return out


def _call_turn(context_act, call_act):
    """An assistant turn with `context_act`'s thinking and text and `call_act`'s tool calls."""
    calls = [{"id": c.get("id") or f"call_{i}", "type": "function",
              "function": {"name": c.get("name"), "arguments": json.dumps(c.get("arguments") or {}, ensure_ascii=False)}}
             for i, c in enumerate(_calls(call_act))]
    turn = {"role": "assistant", "content": _parts(context_act, ("text",)), "tool_calls": calls}
    reasoning = _parts(context_act, ("thinking", "reasoning"))
    if reasoning:
        turn["reasoning_content"] = reasoning
    return turn


def render_step(seg, bad, fix, cap=lambda text: text):
    """(chosen, rejected) message lists sharing the context before act `bad`.

    The model thinks on every turn, so both sides keep the thinking and text it wrote before the failed call:
    written before it saw any error, it can't leak one, and the turn keeps the model's own format. Only the
    tool call differs (the recovering call against the failed one); score it with `scored_span(calls_only)`."""
    rendered = render_segment(seg, cap)
    if rendered is None:
        return None
    msgs, acts = rendered[0], seg["acts"]
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    j = bad - (len(acts) - len(ast))
    if j < 0 or j >= len(ast):
        return None  # compacted away, or the last turn
    prefix = msgs[:ast[j]]
    return prefix + [_call_turn(acts[bad], acts[fix])], prefix + [_call_turn(acts[bad], acts[bad])]


TURN_END = "<|im_end|>"


def scored_span(text, start, end, calls_only):
    """The character span to score inside an assistant turn: all of it, or from its first real tool call.

    A real call comes after the thinking (a call written inside `<think>` is text, not a call). A turn with no
    call (a final answer paired against a call) scores only its end-of-turn token: the choice to stop."""
    if calls_only:
        think = text.find("</think>", start, end)
        after = think + len("</think>") if think >= 0 else start
        at = text.find("<tool_call>", after, end)
        if at >= 0:
            return at, end
        if text.endswith(TURN_END, start, end):
            return end - len(TURN_END), end
    return start, end


def phase_outcomes(run):
    """{phase: passed} from a harness run's per-module grade; {} if it can't be trusted."""
    if run.get("contaminated"):
        return {}
    groups = run.get("check_groups") or {}
    out = {}
    for module, group in groups.items():
        m = re.match(r"test_phase(\d+)_", module)
        if m and group.get("total"):
            out[int(m.group(1))] = group.get("missing", 0) == 0
    if not out and groups:  # a single-phase suite: phase 1 passes only if every test does
        out[1] = all(g.get("missing", 0) == 0 for g in groups.values())
    return out


def worked(seg):
    """Did this phase write or edit a file? A phase cut off while still reading never
    attempted the task, so it is not a fair `rejected` example."""
    return any(c.get("name") in ("write", "edit")
               for a in seg["acts"][len(seg["acts"]) - seg["n_phase"]:] for c in _calls(a))


def trusted_outcomes(outcome, reached):
    """Keep the grades a later phase could not have caused.

    The grade is taken on the FINAL workspace. A pass holds up, but a failure of an
    earlier phase may be a later phase breaking it (a broken import fails every
    phase), so a failure only counts for the last phase the run reached."""
    return {p: ok for p, ok in outcome.items() if ok or p == reached}


def best_outcomes(final, phase_grades, reached):
    """Each phase's own grade when a verified replay exists (regrade_phases.py), else
    the final-state grades a later phase could not have caused."""
    if phase_grades and phase_grades.get("verified") and phase_grades.get("phases"):
        return {int(p): bool(ok) for p, ok in phase_grades["phases"].items()}
    return trusted_outcomes(final, reached)


def grader_seen(trace_text, suite, canary):
    """Did the run see the hidden grader? The harness's own check also matches the
    suite's base/ (the starting files every workspace already holds), so a run that
    ran pytest on the base copy is flagged although it never saw a hidden test."""
    return bool((canary and canary in trace_text) or f"suites/{suite}/grader" in trace_text
                or "grader_tests/" in trace_text)
