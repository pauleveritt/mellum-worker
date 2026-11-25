#!/usr/bin/env python3
"""DPO pairs from multi-phase harness runs (e.g. `harness.py run --suite medium`).

Each run is cut into per-phase segments (phase_pairs.py). Within a phase, a segment
whose grader module passed is `chosen`, one whose module failed is `rejected`. Only the
phase's own assistant turns are scored; earlier phases are context.

Held out:
- phase 1 never enters the set (`--exclude 1`): the Easy screen IS phase 1, so the
  model is never trained on the task it is judged on;
- validation is held out BY TRAJECTORY on `--valid-phase` (default 4), so validation
  accuracy measures generalisation, not memorised partners.

Over-budget segments are dropped, never truncated. Output rows match
dpo_native_train.py: phase, chosen, chosen_mask, rejected, rejected_mask.
"""
import argparse, collections, glob, json, os, random, statistics as st
from pathlib import Path

from mlx_lm import load
from phase_pairs import (phase_outcomes, render_segment, render_step, scored_span, segment_trace, step_pairs,
                         trusted_outcomes, worked, grader_seen, best_outcomes)

ap = argparse.ArgumentParser()
ap.add_argument("--source", action="append", default=[], help="run-record root(s) to mine")
ap.add_argument("--model", required=True, help="tokenizer/template source: the MLX model you train")
ap.add_argument("--budget", type=int, default=41000, help="max tokens per side")
ap.add_argument("--head", type=int, default=400)
ap.add_argument("--tail", type=int, default=200)
ap.add_argument("--exclude", type=int, action="append", default=[1],
                help="phases dropped from --source roots (phase 1 = the Easy task)")
ap.add_argument("--source-all-phases", action="append", default=[],
                help="roots whose every phase is kept (single-phase tasks that are not the Easy task)")
ap.add_argument("--valid-key", action="append", default=None,
                help="suite:pN keys held out by trajectory (default medium:p4)")
ap.add_argument("--valid-win", type=int, default=2)
ap.add_argument("--valid-loss", type=int, default=3)
ap.add_argument("--max-pairs-per-phase", type=int, default=60)
ap.add_argument("--steps", action="store_true",
                help="also emit step pairs: a failed tool call against the call that recovered from it")
ap.add_argument("--valid-step-every", type=int, default=10,
                help="every Nth run's step pairs go to validation (held out by trajectory)")
ap.add_argument("--out", required=True)
args = ap.parse_args()
random.seed(0)
_, tok = load(args.model, lazy=True)
hf = tok._tokenizer
AST, END = "<|im_start|>assistant\n", "<|im_end|>"


def cap(text):
    if len(text) <= args.head + args.tail + 40:
        return text
    return text[:args.head] + f"\n...[{len(text) - args.head - args.tail} chars elided]...\n" + text[-args.tail:]


def encode(msgs, scored, tools, calls_only=False):
    text = tok.apply_chat_template(msgs, tools=tools, tokenize=False)
    spans, pos = [], 0
    while (s := text.find(AST, pos)) >= 0:
        b = s + len(AST); e = text.find(END, b)
        if e < 0:
            return None
        spans.append((b, e + len(END))); pos = e
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    if len(spans) != len(ast):
        return None
    keep = [scored_span(text, *spans[ast.index(i)], calls_only) for i in scored]
    enc = hf(text, add_special_tokens=False, return_offsets_mapping=True)
    mask = [int(any(a <= o[0] < b for a, b in keep)) for o in enc["offset_mapping"]]
    return {"ids": enc["input_ids"], "mask": mask}


win, loss, why = collections.defaultdict(list), collections.defaultdict(list), collections.Counter()
step_train, step_valid, n_runs = [], [], 0


def emit_steps(seg, key, src, to_valid):
    for bad, fix in step_pairs(seg):
        r = render_step(seg, bad, fix, cap=cap)
        if r is None:
            why["step-misaligned"] += 1; continue
        recs = [encode(m, [max(i for i, x in enumerate(m) if x["role"] == "assistant")], seg["payload"].get("tools"),
                       calls_only=True) for m in r]
        if None in recs or max(len(x["ids"]) for x in recs) > args.budget:
            why["step-dropped"] += 1; continue
        (step_valid if to_valid else step_train).append(
            {"phase": key + ":step", "chosen": recs[0]["ids"], "chosen_mask": recs[0]["mask"],
             "rejected": recs[1]["ids"], "rejected_mask": recs[1]["mask"], "src": [f"{src}@{bad}"] * 2})
        why["step-ok"] += 1
for root, keep_all in [(r, False) for r in args.source] + [(r, True) for r in args.source_all_phases]:
    for f in sorted(glob.glob(f"{root}/**/run.json", recursive=True)):
        run = json.load(open(f)); trace = Path(f).with_name("trace.jsonl")
        if run.get("contaminated") and trace.is_file():
            canary_file = Path(__file__).resolve().parents[1] / "code" / "suites" / str(run.get("suite")) / "grader" / "canary"
            canary = canary_file.read_text().strip() if canary_file.is_file() else None
            if not grader_seen(trace.read_text(errors="ignore"), run.get("suite"), canary):
                run = {**run, "contaminated": False}; why["base-path-flag-cleared"] += 1
        outcome = phase_outcomes(run)
        if run.get("contaminated") or not trace.is_file():
            why["contaminated-or-no-trace"] += 1; continue
        rows = [json.loads(line) for line in open(trace) if line.strip()]
        segs = segment_trace(rows)
        if args.steps:
            n_runs += 1
            for seg in segs:
                if keep_all or seg["phase"] not in args.exclude:
                    emit_steps(seg, f"{run.get('suite')}:p{seg['phase']}", Path(f).parent.name,
                               n_runs % args.valid_step_every == 0)
        if not outcome:
            why["no-grade"] += 1; continue
        pg = Path(f).with_name("phase_grades.json")
        graded = json.loads(pg.read_text()) if pg.is_file() else None
        why["phase-graded"] += bool(graded and graded.get("verified"))
        outcome = best_outcomes(outcome, graded, reached=len(segs))
        for seg in segs:
            p = seg["phase"]
            if (not keep_all and p in args.exclude) or p not in outcome:
                continue
            if not outcome[p] and not worked(seg):
                why["rejected-never-wrote"] += 1; continue  # cut off while reading: not a fair loser
            rendered = render_segment(seg, cap=cap)
            if rendered is None:
                why["misaligned"] += 1; continue
            rec = encode(*rendered, seg["payload"].get("tools"))
            if rec is None:
                why["span-mismatch"] += 1; continue
            if len(rec["ids"]) > args.budget:
                why["over-budget"] += 1; continue
            key = f"{run.get('suite')}:p{p}"  # pairs only ever compare runs of the same task and phase
            rec["src"] = f"{Path(f).parent.name}#{key}"
            (win if outcome[p] else loss)[key].append(rec); why["ok"] += 1

print("segments:", dict(why))
train, valid, per = [], [], {}
for p in sorted(set(win) | set(loss)):
    W, L = win[p][:], loss[p][:]
    random.shuffle(W); random.shuffle(L)
    hw, hl = (W[:args.valid_win], L[:args.valid_loss]) if p in (args.valid_key or ["medium:p4"]) else ([], [])
    tw, tl = W[len(hw):], L[len(hl):]
    cand = [(a, b) for a in tw for b in tl]; random.shuffle(cand)
    cand = cand[:args.max_pairs_per_phase]
    mk = lambda a, b: {"phase": p, "chosen": a["ids"], "chosen_mask": a["mask"],
                       "rejected": b["ids"], "rejected_mask": b["mask"], "src": [a["src"], b["src"]]}
    train += [mk(a, b) for a, b in cand]
    valid += [mk(a, b) for a in hw for b in hl]
    lens = [len(r["ids"]) for r in W + L]
    per[p] = {"win": len(W), "loss": len(L), "train_pairs": len(cand), "valid_pairs": len(hw) * len(hl),
              "median_tokens": int(st.median(lens)) if lens else 0}
train += step_train; valid += step_valid
per["steps"] = {"train": len(step_train), "valid": len(step_valid)}
random.shuffle(train)
os.makedirs(args.out, exist_ok=True)
for name, rows in (("train", train), ("valid", valid)):
    with open(f"{args.out}/{name}.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
print("per phase:", json.dumps(per))
print(f"train {len(train)}  valid {len(valid)}  -> {args.out}")
