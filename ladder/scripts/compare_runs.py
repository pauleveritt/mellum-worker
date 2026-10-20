#!/usr/bin/env python3
"""Compare ladder runs mechanically: pass rate and wall time per rung.

Each argument is a run directory holding `*/run.json` records — a ladder
`--out` directory or a `docs/ladder/<record>` directory. The run.json schema is
the same for both, so old and new runs compare directly. Prints a side-by-side
table (pass/n and average wall seconds per rung) plus totals.

Usage:
  python scripts/compare_runs.py <dirA> <dirB> [<dirC> ...]
  python scripts/compare_runs.py --labels past,v7 <dirA> <dirB>
"""
import collections
import glob
import json
import os
import sys


def collect(d):
    """rung -> list of (passed: bool, wall: float|None) from every run.json under d."""
    runs = collections.defaultdict(list)
    for f in glob.glob(os.path.join(d, "*", "run.json")):
        try:
            r = json.load(open(f))
        except (OSError, json.JSONDecodeError):
            continue
        rung = r.get("rung")
        if rung is None:
            continue
        passed = bool(r.get("check", {}).get("passed"))
        wall = r.get("wall_seconds_untrusted")
        runs[rung].append((passed, wall if isinstance(wall, (int, float)) else None))
    return runs


def cell(runs):
    if not runs:
        return "—"
    p = sum(1 for ok, _ in runs if ok)
    walls = [w for _, w in runs if w is not None]
    avg = sum(walls) / len(walls) if walls else 0
    return f"{p}/{len(runs)}  {avg:.0f}s"


def main(argv):
    labels = None
    dirs = []
    i = 0
    while i < len(argv):
        if argv[i] == "--labels":
            labels = argv[i + 1].split(",")
            i += 2
        else:
            dirs.append(argv[i])
            i += 1
    if not dirs:
        print(__doc__)
        return 1
    if not labels:
        labels = [os.path.basename(os.path.normpath(d)) for d in dirs]
    data = [collect(d) for d in dirs]
    rungs = sorted({k for d in data for k in d})
    width = max(14, max((len(x) for x in labels), default=14))

    print("rung | " + " | ".join(x.ljust(width) for x in labels))
    print("-" * (7 + (width + 3) * len(labels)))
    for rung in rungs:
        print(f"  {str(rung).ljust(2)} | " + " | ".join(cell(d.get(rung, [])).ljust(width) for d in data))
    totals = []
    for d in data:
        allr = [r for rs in d.values() for r in rs]
        p = sum(1 for ok, _ in allr if ok)
        totals.append(f"{p}/{len(allr)}".ljust(width))
    print("-" * (7 + (width + 3) * len(labels)))
    print(" TOT | " + " | ".join(totals))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
