#!/usr/bin/env python3
"""How cleanly runs call their tools, counted from each run's trace.

    uv run python tool_score.py ../../runs/<group> [../../runs/<group> ...]

A fault is a call the model got wrong, never a red test or the environment:

- a non-bash call that errored (an edit that matched nothing, a read of a missing file);
- a bash command broken by its own shape (`shell_shape`: quoting, a `python -c` that can't parse, a flag this
  shell lacks);
- a search or listing aimed outside the workspace (`scope_command`), whether or not it errored.

The score is faults per 100 calls, per group, so a tune is judged on its calls as well as its passes. The same
rules build the training pairs, so this counts exactly what the tool pairs try to remove.
"""
import collections
import glob
import json
import sys
from pathlib import Path

from pathology_pairs import scope_command, shell_shape
from phase_pairs import ENV_ERRORS


def _text(row):
    return "".join(p.get("text", "") for p in row.get("content") or [] if isinstance(p, dict))


def faults(rows, workspace):
    """{"calls", "faults", "kinds"} for one trace's rows."""
    calls, kinds = {}, collections.Counter()
    for row in rows:
        if row.get("type") == "tool_call":
            calls[row.get("toolCallId")] = row
            cmd = (row.get("input") or {}).get("command") if row.get("toolName") == "bash" else None
            if isinstance(cmd, str) and scope_command(cmd, workspace):
                kinds["outside"] += 1
        elif row.get("type") == "tool_result" and row.get("isError"):
            text = _text(row)
            if any(x in text for x in ENV_ERRORS):
                continue
            if row.get("toolName") != "bash":
                kinds[row.get("toolName")] += 1
            elif shape := shell_shape(text):
                kinds[shape] += 1
    return {"calls": len(calls), "faults": sum(kinds.values()), "kinds": dict(kinds)}


def score(root):
    total, kinds, runs = collections.Counter(), collections.Counter(), 0
    for trace in sorted(glob.glob(f"{root}/**/trace.jsonl", recursive=True)):
        rows = [json.loads(line) for line in open(trace) if line.strip()]
        got = faults(rows, str(Path(trace).parent / "workspace"))
        runs += 1
        total.update(calls=got["calls"], faults=got["faults"])
        kinds.update(got["kinds"])
    rate = 100 * total["faults"] / total["calls"] if total["calls"] else 0.0
    return {"runs": runs, "calls": total["calls"], "faults": total["faults"], "per_100": round(rate, 1),
            "kinds": dict(kinds.most_common())}


def main():
    for root in sys.argv[1:]:
        s = score(root)
        print(f"{Path(root).name}: {s['runs']} runs, {s['calls']} calls, {s['faults']} faults "
              f"= {s['per_100']} per 100 calls  {s['kinds']}")


if __name__ == "__main__":
    main()
