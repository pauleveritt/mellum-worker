#!/usr/bin/env python3
"""trace -> SFT: build an adherence training set from clean-winner trajectories.

A "clean winner" is a graded run whose hidden grader passed, that built in the
named files (no outside_write), kept the tests intact, and still has a trace on
disk. Each model response in that trace becomes one (context -> on-task action)
example: messages = the exact context the model saw, plus the assistant action it
took. We keep the native tool-calling shape and let mlx-lm apply the chat
template at train time (so the trained format matches inference exactly).

Phase-4 (the lost-id miss) is held out entirely for measurement.
Quality filtering is aggressive on purpose: small models take data literally.
"""
import json, glob, os, sys, collections, random, argparse
from pathlib import Path

REPO = Path("/Users/mac/projects/mellum-worker")
OUTDIR = Path("./data")
MODEL = "mlx-community/Mellum2-12B-A2.5B-Thinking-4bit"
MAX_TOKENS = 4096          # drop examples whose rendered context exceeds this
MIN_CONTEXT_MSGS = 2       # need at least system+user
random.seed(0)

def is_phase4(brief: str) -> bool:
    b = (brief or "").lower()
    return ("phase-4" in b or "phase_4" in b or "phase4" in b
            or "resolve-reopen" in b or "test_phase4" in b)

def clean_winner(d) -> bool:
    ck, sc = d.get("check"), d.get("score")
    if not isinstance(ck, dict) or not isinstance(sc, dict):
        return False
    det = ck.get("details", {}) or {}
    return bool(det.get("hidden_pass") and ck.get("passed")
                and not (det.get("outside_write_list") or [])
                and ck.get("tests_unchanged"))

def norm_content(content):
    """Harness content (str or list of typed parts) -> (text, tool_calls)."""
    if isinstance(content, str):
        return content, []
    text_parts, tool_calls = [], []
    if isinstance(content, list):
        for p in content:
            if not isinstance(p, dict):
                continue
            t = p.get("type")
            if t in ("text", "reasoning", "thinking"):
                if p.get("text"):
                    text_parts.append(p["text"])
            elif t in ("toolCall", "tool_call"):
                tool_calls.append({
                    "id": p.get("id") or f"call_{len(tool_calls)}",
                    "type": "function",
                    "function": {
                        "name": p.get("name"),
                        "arguments": json.dumps(p.get("arguments") or p.get("args") or {}),
                    },
                })
            elif t in ("toolResult", "tool_result"):
                r = p.get("result") if p.get("result") is not None else p.get("text")
                text_parts.append(r if isinstance(r, str) else json.dumps(r))
    return "\n".join(text_parts).strip(), tool_calls

def to_openai(msg, pending_ids):
    """One harness message -> one OpenAI message (or None to drop)."""
    role = msg.get("role")
    if role not in ("system", "user", "assistant", "tool"):
        return None
    text, tool_calls = norm_content(msg.get("content"))
    if role == "assistant":
        m = {"role": "assistant", "content": text}
        if tool_calls:
            m["tool_calls"] = tool_calls
            pending_ids.extend(tc["id"] for tc in tool_calls)
        return m if (text or tool_calls) else None
    if role == "tool":
        tcid = pending_ids.pop(0) if pending_ids else "call_0"
        return {"role": "tool", "tool_call_id": tcid, "content": text or "(no output)"}
    return {"role": role, "content": text} if text else None

def convert_messages(harness_msgs):
    out, pending = [], []
    for hm in harness_msgs:
        om = to_openai(hm, pending)
        if om is not None:
            out.append(om)
    return out

def iter_examples(trace_path):
    """Yield (messages, tools) pairs: context + the assistant action that followed."""
    cur_ctx, cur_tools = None, None
    with open(trace_path) as fh:
        for ln in fh:
            if '"provider_request"' not in ln and '"message_end"' not in ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            t = o.get("type")
            if t == "provider_request":
                pay = o.get("payload") or o.get("request") or {}
                cur_ctx = pay.get("messages")
                cur_tools = pay.get("tools")
            elif t == "message_end" and cur_ctx:
                action = o.get("message")
                if not isinstance(action, dict):
                    continue
                msgs = convert_messages(cur_ctx)
                act = to_openai(action, [])
                if act is None or act.get("role") != "assistant":
                    continue
                if len(msgs) < MIN_CONTEXT_MSGS:
                    continue
                yield msgs + [act], cur_tools

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-trace", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    # tokenizer (no weight load) for template validation + length filtering
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    mp = snapshot_download(MODEL)   # already cached; no re-download
    tok = AutoTokenizer.from_pretrained(mp)

    run_files = (glob.glob(str(REPO / "runs/**/run.json"), recursive=True)
                 + glob.glob(str(REPO / "evals/**/run.json"), recursive=True))
    winners = []
    for f in run_files:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if not clean_winner(d):
            continue
        rd = os.path.dirname(f)
        traces = glob.glob(os.path.join(rd, "trace*.jsonl"))
        if traces:
            brief = d.get("suite") or d.get("sentence") or ""
            winners.append((traces[0], brief))

    stats = collections.Counter()
    train, valid, holdout = [], [], []
    seen = set()
    for tr, brief in winners:
        held = is_phase4(brief)
        n_this = 0
        for msgs, tools in iter_examples(tr):
            stats["raw_pairs"] += 1
            # template render + length filter (immaculate quality)
            try:
                rendered = tok.apply_chat_template(
                    msgs, tools=tools, tokenize=True, add_generation_prompt=False)
            except Exception:
                stats["drop_template_error"] += 1
                continue
            n_tok = len(rendered)
            if n_tok > MAX_TOKENS:
                stats["drop_too_long"] += 1
                continue
            # dedup on the (last-user-or-tool + assistant action) signature
            sig = json.dumps(msgs[-2:], sort_keys=True)
            if sig in seen:
                stats["drop_dup"] += 1
                continue
            seen.add(sig)
            rec = {"messages": msgs}
            if tools:
                rec["tools"] = tools
            (holdout if held else (valid if random.random() < 0.1 else train)).append(rec)
            stats["kept"] += 1
            n_this += 1
            if args.limit_per_trace and n_this >= args.limit_per_trace:
                break

    OUTDIR.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train", train), ("valid", valid), ("holdout_phase4", holdout)):
        with open(OUTDIR / f"{name}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    print(f"winner traces: {len(winners)}  (phase-4 held out: {sum(1 for _,b in winners if is_phase4(b))})")
    print("stats:", dict(stats))
    print(f"written -> train {len(train)} | valid {len(valid)} | holdout_phase4 {len(holdout)}")
    # show one rendered sample
    if train:
        s = tok.apply_chat_template(train[0]["messages"], tools=train[0].get("tools"),
                                    tokenize=False, add_generation_prompt=False)
        print("\n=== rendered sample (first 900 chars) ===\n" + s[:900])

if __name__ == "__main__":
    main()
