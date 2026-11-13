#!/usr/bin/env python3
"""DPO preference set in the model's NATIVE format, scoring only what it generated.

Each sequence is a real phase trajectory re-rendered exactly as llama-server saw
it (the final provider_request payload is already OpenAI-shaped), with every
assistant turn restored to what the model generated: its recorded reasoning as
`reasoning_content` plus its native `tool_calls`. Tool results are capped (head +
tail) so a pair fits two forward passes; that is the one deliberate deviation
from the inference context, and it is identical for chosen/rejected and for
policy/reference.

The mask is 1 only on assistant-generated tokens (each assistant turn, through its
<|im_end|>); system, brief and tool results are context (0). Over-budget
sequences are DROPPED, never truncated. Within a phase, a clean winner is
`chosen`, a graded failure that actually worked the task is `rejected`.

Fixes over build_dpo.py: (1) make_sft's to_openai dropped every history assistant
turn (tool_calls live at message level in the payload, not in content parts);
(2) the old set used an invented `<tool:...>` text format and dropped tool
results; (3) pairs were truncated at train time instead of dropped.
"""
import json, glob, os, collections, random, argparse, statistics as st
from pathlib import Path
from mlx_lm import load

REPO = str(Path(__file__).resolve().parents[2])
ap = argparse.ArgumentParser()
ap.add_argument("--budget", type=int, default=0, help="max tokens per side; 0 = measure only")
ap.add_argument("--head", type=int, default=400)
ap.add_argument("--tail", type=int, default=200)
ap.add_argument("--max-pairs-per-phase", type=int, default=60)
ap.add_argument("--valid", type=int, default=12)
ap.add_argument("--source", action="append",
                help="run-record root(s) to mine, relative to the repo (default: runs/ and evals/); "
                     "pass the on-policy sampling dir to keep the set on one model")
ap.add_argument("--out", default=f"{REPO}/learn/finetune/data_dpo_native")
ap.add_argument("--model", default="mlx-community/Mellum2-12B-A2.5B-Thinking-4bit",
                help="tokenizer/template source; must be the model you train (Mellum2 != Mellum2.1)")
args = ap.parse_args()
random.seed(0)
_, tok = load(args.model, lazy=True)
hf = tok._tokenizer
AST = "<|im_start|>assistant\n"; END = "<|im_end|>"

def clean_winner(d):
    ck = d.get("check") or {}; det = ck.get("details") or {}
    return bool(det.get("hidden_pass") and ck.get("passed")
                and not (det.get("outside_write_list") or []) and ck.get("tests_unchanged"))

def graded_failure(d):
    ck = d.get("check") or {}; det = ck.get("details") or {}
    return isinstance(ck, dict) and bool(ck) and not det.get("hidden_pass")

def phase_key(s):
    s = (s or "").lower().replace("_", "-")
    for p in ("phase-1","phase-2","phase-3","phase-4","phase-5","phase-6","phase-7"):
        if p in s: return p
    return None

def cap(text):
    if not isinstance(text, str): text = json.dumps(text)
    if len(text) <= args.head + args.tail + 40: return text
    return text[:args.head] + f"\n...[{len(text)-args.head-args.tail} chars elided]...\n" + text[-args.tail:]

def parts(action, kind):
    return "\n".join(p.get("text","") for p in (action.get("content") or [])
                     if isinstance(p, dict) and p.get("type") in kind and p.get("text"))

def build(trace):
    ctx = tools = None; acts = []
    for ln in open(trace):
        if '"provider_request"' not in ln and '"message_end"' not in ln: continue
        try: o = json.loads(ln)
        except Exception: continue
        if o.get("type") == "provider_request":
            p = o.get("payload") or o.get("request") or {}
            if p.get("messages"): ctx = p["messages"]; tools = p.get("tools")
        elif o.get("type") == "message_end":
            m = o.get("message")
            if isinstance(m, dict) and m.get("role") == "assistant": acts.append(m)
    if not ctx or not acts: return None, "no-ctx"
    hist = [i for i, m in enumerate(ctx) if m.get("role") == "assistant"]
    if len(hist) + 1 != len(acts): return None, "misaligned"
    msgs = []
    k = 0
    for m in ctx:
        m = dict(m)
        if m.get("role") == "assistant":
            a = acts[k]; k += 1
            names_h = [t["function"]["name"] for t in (m.get("tool_calls") or [])]
            names_a = [p.get("name") for p in (a.get("content") or []) if isinstance(p, dict) and p.get("type") == "toolCall"]
            if names_h != names_a: return None, "name-mismatch"
            r = parts(a, ("thinking", "reasoning"))
            if r: m["reasoning_content"] = r
            m["content"] = parts(a, ("text",)) or ""
        elif m.get("role") == "tool":
            m["content"] = cap(m.get("content"))
        msgs.append(m)
    fa = acts[-1]
    last = {"role": "assistant", "content": parts(fa, ("text",)) or ""}
    r = parts(fa, ("thinking", "reasoning"))
    if r: last["reasoning_content"] = r
    tcs = [{"id": p.get("id") or f"call_{i}", "type": "function",
            "function": {"name": p.get("name"), "arguments": json.dumps(p.get("arguments") or {})}}
           for i, p in enumerate(p for p in (fa.get("content") or []) if isinstance(p, dict) and p.get("type") == "toolCall")]
    if tcs: last["tool_calls"] = tcs
    msgs.append(last)
    n_ast = sum(1 for m in msgs if m["role"] == "assistant")
    text = tok.apply_chat_template(msgs, tools=tools, tokenize=False)
    # assistant spans: after each "<|im_start|>assistant\n" through its "<|im_end|>"
    spans = []; pos = 0
    while True:
        s = text.find(AST, pos)
        if s < 0: break
        b = s + len(AST); e = text.find(END, b)
        if e < 0: return None, "unterminated"
        spans.append((b, e + len(END))); pos = e
    if len(spans) != n_ast: return None, f"span-count {len(spans)}!={n_ast}"
    enc = hf(text, add_special_tokens=False, return_offsets_mapping=True)
    ids = enc["input_ids"]; offs = enc["offset_mapping"]
    mask = [0] * len(ids); si = 0
    for t, (a, _) in enumerate(offs):
        while si < len(spans) and a >= spans[si][1]: si += 1
        if si < len(spans) and spans[si][0] <= a < spans[si][1]: mask[t] = 1
    return {"ids": ids, "mask": mask, "n_scored": sum(mask), "n_ast": n_ast}, "ok"

runs = [f for root in (args.source or ["runs", "evals"]) for f in glob.glob(f"{REPO}/{root}/**/run.json", recursive=True)]
win = collections.defaultdict(list); loss = collections.defaultdict(list); why = collections.Counter()
for f in runs:
    try: d = json.load(open(f))
    except Exception: continue
    k = phase_key(d.get("suite") or d.get("sentence"))
    trs = glob.glob(os.path.join(os.path.dirname(f), "trace*.jsonl"))
    if not k or not trs: continue
    w = clean_winner(d); l = (not w) and graded_failure(d)
    if not (w or l): why["ungraded/unclean-pass"] += 1; continue
    rec, r = build(trs[0]); why[r] += 1
    if rec is None: continue
    if rec["n_ast"] < 2: why["loser<2 turns" if l else "winner<2 turns"] += 1; continue
    (win if w else loss)[k].append(rec)

print("build outcomes:", dict(why))
allw = [r["ids"] for v in win.values() for r in v]; alll = [r["ids"] for v in loss.values() for r in v]
print(f"{'phase':8s} win(n,med,max)            loss(n,med,max)")
for k in sorted(set(win) | set(loss)):
    W = [len(r["ids"]) for r in win[k]]; L = [len(r["ids"]) for r in loss[k]]
    f_ = lambda x: f"{len(x):2d} med{int(st.median(x)) if x else 0:6d} max{max(x) if x else 0:6d}"
    print(f"{k:8s} {f_(W)}   {f_(L)}")
for b in (4096, 6144, 8192, 12288, 16384):
    print(f"  <= {b:5d}: winners {sum(len(x)<=b for x in allw)}/{len(allw)}  losers {sum(len(x)<=b for x in alll)}/{len(alll)}")
sc = [r["n_scored"]/len(r["ids"]) for v in list(win.values())+list(loss.values()) for r in v]
print(f"scored-token fraction: median {st.median(sc):.2f}")
if not args.budget: raise SystemExit(0)

def mk(k, a, b):
    return {"phase": k, "chosen": a["ids"], "chosen_mask": a["mask"],
            "rejected": b["ids"], "rejected_mask": b["mask"]}
# Valid is held out BY TRAJECTORY (phase-4: 2 winners + 3 losers never trained on),
# so val accuracy measures generalisation, not memorised cartesian partners.
train, valid = [], []; per = {}
for k in sorted(set(win) & set(loss)):
    W = [r for r in win[k] if len(r["ids"]) <= args.budget]
    L = [r for r in loss[k] if len(r["ids"]) <= args.budget]
    random.shuffle(W); random.shuffle(L)
    hw, hl = (W[:2], L[:3]) if k == "phase-4" else ([], [])
    tw, tl = W[len(hw):], L[len(hl):]
    cand = [(a, b) for a in tw for b in tl]; random.shuffle(cand)
    cand = cand[:args.max_pairs_per_phase]
    train += [mk(k, a, b) for a, b in cand]
    valid += [mk(k, a, b) for a in hw for b in hl]
    per[k] = {"win": len(W), "loss": len(L), "train_pairs": len(cand), "valid_pairs": len(hw) * len(hl)}
random.shuffle(train)
pairs = train + valid
os.makedirs(args.out, exist_ok=True)
for name, rows in (("train", train), ("valid", valid)):
    with open(f"{args.out}/{name}.jsonl", "w") as fh:
        for r in rows: fh.write(json.dumps(r) + "\n")
print(f"\nbudget {args.budget}: per phase (win,loss,pairs):", dict(per))
print(f"TOTAL pairs {len(pairs)}  train {len(train)}  valid {len(valid)}  -> {args.out}")
