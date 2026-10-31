#!/usr/bin/env python
"""Convert dataset.jsonl into an mlx-lm LoRA data directory.

mlx-lm wants a directory with train.jsonl / valid.jsonl; each line a record it
understands. Our examples already carry a chat `messages` list, so we keep just
that (dropping the `task` tag) and split deterministically.

  uv run python learn/code/lora/convert_data.py dataset.jsonl <out-dir>
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: convert_data.py <dataset.jsonl> <out-dir>", file=sys.stderr)
        return 2
    src, out = Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    recs = [{"messages": r["messages"]} for r in rows]
    random.seed(0)
    random.shuffle(recs)
    n_val = max(1, len(recs) // 5)
    valid, train = recs[:n_val], recs[n_val:]
    (out / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    (out / "valid.jsonl").write_text("\n".join(json.dumps(r) for r in valid) + "\n")
    print(f"train={len(train)} valid={len(valid)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
