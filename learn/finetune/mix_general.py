#!/usr/bin/env python3
"""Blend ~15% general coding-instruct data into the adherence set.

Small models over-specialise ("syrup" problem): train them only on one niche and
they lose general coherence. A 10-20% blend of general instruction data acts as a
regulariser. We use a general coding-instruct set (CodeAlpaca) so the regulariser
stays in-domain (code) while still being OFF our eval (not AgentClinic).
"""
import json, random
from pathlib import Path
from huggingface_hub import hf_hub_download

OUT = Path("./data")
SHARE = 0.15                      # general share of the final mix
random.seed(0)

def load(p): return [json.loads(l) for l in open(p)]
train = load(OUT / "train.jsonl")
valid = load(OUT / "valid.jsonl")

# pull a general coding-instruct file (single json, no datasets lib needed)
candidates = [
    ("sahil2801/CodeAlpaca-20k", "code_alpaca_20k.json"),
    ("HuggingFaceH4/CodeAlpaca_20K", "data/train-00000-of-00001.parquet"),
]
raw = None
for repo, fn in candidates:
    try:
        p = hf_hub_download(repo, fn, repo_type="dataset")
        if fn.endswith(".json"):
            raw = json.load(open(p)); src = repo
            break
    except Exception as e:
        print(f"  skip {repo}/{fn}: {e}")
if raw is None:
    raise SystemExit("could not fetch a general set; adjust candidates")
print(f"general source: {src}  rows: {len(raw)}")
random.shuffle(raw)

def to_msg(r):
    instr = (r.get("instruction") or "").strip()
    inp = (r.get("input") or "").strip()
    out = (r.get("output") or "").strip()
    user = instr + (("\n\n" + inp) if inp else "")
    if not user or not out:
        return None
    return {"messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": out}],
            "_src": "general"}

def n_for(base):   # count that makes general == SHARE of (base + count)
    return round(SHARE / (1 - SHARE) * base)

need_t, need_v = n_for(len(train)), n_for(len(valid))
gen = []
for r in raw:
    m = to_msg(r)
    if m:
        gen.append(m)
    if len(gen) >= need_t + need_v:
        break
gt, gv = gen[:need_t], gen[need_t:need_t + need_v]

train2 = train + gt
valid2 = valid + gv
random.shuffle(train2); random.shuffle(valid2)
with open(OUT / "train.jsonl", "w") as f:
    for r in train2: f.write(json.dumps(r) + "\n")
with open(OUT / "valid.jsonl", "w") as f:
    for r in valid2: f.write(json.dumps(r) + "\n")

print(f"train: {len(train)} adherence + {len(gt)} general = {len(train2)} "
      f"({len(gt)/len(train2)*100:.1f}% general)")
print(f"valid: {len(valid)} adherence + {len(gv)} general = {len(valid2)} "
      f"({len(gv)/len(valid2)*100:.1f}% general)")
