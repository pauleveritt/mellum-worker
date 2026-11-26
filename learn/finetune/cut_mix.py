#!/usr/bin/env python3
"""Cut a raw pair set (build_dpo_phases.py output) to a fixed mix.

    cut_mix.py --raw data_dpo_raw_v2 --per-phase 20 --steps 60 --out data_dpo_<name>

- phase pairs: `--per-phase` for each listed phase, round-robin over distinct rejected runs, so no one losing
  run dominates;
- step pairs (`...:step`): `--steps` sampled at random;
- pathology pairs (`...:outside`, `...:unused`): all kept, there are few.

Validation is copied unchanged. Seeded (0), so the same raw set always cuts the same way.
"""
import argparse
import json
import os
import random
import sys
from collections import defaultdict

PHASES = ["medium:p2", "medium:p3", "medium:p4"]
PATHOLOGIES = ("outside", "unused")


def cut(rows, per_phase=20, phases=PHASES, steps=60, seed=0):
    rng = random.Random(seed)
    out = []
    for p in phases:
        by_loser = defaultdict(list)
        for r in rows:
            if r["phase"] == p:
                by_loser[r["src"][1]].append(r)
        queues = [by_loser[k][:] for k in sorted(by_loser)]
        for q in queues:
            rng.shuffle(q)
        rng.shuffle(queues)
        picked = []
        while len(picked) < per_phase and any(queues):
            for q in queues:
                if q and len(picked) < per_phase:
                    picked.append(q.pop())
        out += picked
    step_rows = [r for r in rows if r["phase"].endswith(":step")]
    out += rng.sample(step_rows, min(steps, len(step_rows)))
    out += [r for r in rows if r["phase"].rsplit(":", 1)[-1] in PATHOLOGIES]
    rng.shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--per-phase", type=int, default=20)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"{a.out} already exists; cut into a new versioned folder instead of overwriting it")
    rows = [json.loads(line) for line in open(f"{a.raw}/train.jsonl")]
    train = cut(rows, a.per_phase, PHASES, a.steps)
    os.makedirs(a.out)
    with open(f"{a.out}/train.jsonl", "w") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in train)
    with open(f"{a.raw}/valid.jsonl") as src, open(f"{a.out}/valid.jsonl", "w") as dst:
        dst.write(src.read())
    counts = defaultdict(int)
    for r in train:
        counts[r["phase"].rsplit(":", 1)[-1] if r["phase"].count(":") > 1 else r["phase"]] += 1
    print(f"train {len(train)} {dict(counts)} -> {a.out}")


if __name__ == "__main__":
    main()
