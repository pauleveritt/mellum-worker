"""Pair sets on disk: one file per section and part, every file under GitHub's size limit.

A split ("train", "valid") is written as `<split>.<section>.<NN>.jsonl`. The section is the pair kind (phase,
step, outside, unused, shell, idiom), so each kind can be read and checked on its own; a section bigger than `MAX_BYTES` is
cut into numbered parts. Each row carries its position (`i`), so reading puts the rows back in exactly the order
they were written and a training run that shuffles them with a fixed seed is reproducible. Older sets stored as
one `<split>.jsonl` are read as they are.
"""
import json
from collections import defaultdict
from pathlib import Path

MAX_BYTES = 45_000_000  # under GitHub's 50 MB warning, well under its 100 MB refusal
KINDS = ("step", "outside", "unused", "shell", "reread", "cleanup", "idiom")


def section(row):
    kind = row["phase"].rsplit(":", 1)[-1]
    return kind if kind in KINDS else "phase"


def write_pairs(out_dir, split, rows, max_bytes=MAX_BYTES):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = defaultdict(list)
    for i, row in enumerate(rows):
        line = json.dumps({**row, "i": i}) + "\n"
        if len(line.encode()) > max_bytes:
            raise ValueError(f"row {i} is {len(line.encode())} bytes, over the {max_bytes}-byte file limit")
        lines[section(row)].append(line)
    for name, chunk in lines.items():
        part, size, buf = 1, 0, []
        for line in chunk + [None]:
            n = len(line.encode()) if line else 0
            if buf and (line is None or size + n > max_bytes):
                path = out_dir / f"{split}.{name}.{part:02d}.jsonl"
                if path.exists():
                    raise FileExistsError(path)
                path.write_text("".join(buf))
                part, size, buf = part + 1, 0, []
            if line:
                buf.append(line); size += n


def read_pairs(data_dir, split):
    data_dir = Path(data_dir)
    single = data_dir / f"{split}.jsonl"
    if single.is_file():
        return [json.loads(line) for line in open(single) if line.strip()]
    rows = [json.loads(line) for p in sorted(data_dir.glob(f"{split}.*.jsonl")) for line in open(p) if line.strip()]
    rows.sort(key=lambda r: r["i"])
    for r in rows:
        del r["i"]
    return rows
