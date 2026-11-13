"""Summarise a ladder output directory: pass counts per rung and non-zero pathology columns.

uv run python -m ladder.summarize ../evals/baseline/2026-10-09-phase0-baseline [more dirs...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PATHOLOGY_COLUMNS = (
    "tool_errors",
    "edit_anchor_failures",
    "noop_edits",
    "write_existing",
    "write_shrink",
    "bash_file_mutations",
)
STREAK_THRESHOLD = 5


def load_records(directory: Path) -> list[dict]:
    return [
        json.loads(p.read_text()) for p in sorted(Path(directory).glob("*/run.json"))
    ]


def summarize(directory: Path) -> dict:
    records = load_records(directory)
    rungs: dict[int, dict] = {}
    nonzero: dict[str, int] = {}
    for record in records:
        entry = rungs.setdefault(
            record["rung"],
            {"runs": 0, "passed": 0, "deadline_hits": 0, "largest_prompt_chars": 0},
        )
        entry["runs"] += 1
        entry["passed"] += bool(record["check"]["passed"])
        entry["deadline_hits"] += bool(record.get("deadline_hit"))
        entry["largest_prompt_chars"] = max(
            entry["largest_prompt_chars"], record["score"]["largest_prompt_chars"]
        )
        for column in PATHOLOGY_COLUMNS:
            if record["score"].get(column):
                nonzero[column] = nonzero.get(column, 0) + 1
        if record["score"].get("loop_breaker_would_block"):
            nonzero["loop_breaker_would_block"] = (
                nonzero.get("loop_breaker_would_block", 0) + 1
            )
        if record.get("deadline_hit"):
            nonzero["deadline_hit"] = nonzero.get("deadline_hit", 0) + 1
        if "final_text_chars" in record and not record["final_text_chars"]:
            nonzero["empty_final"] = nonzero.get("empty_final", 0) + 1
        if record["score"].get("nudges"):
            nonzero["nudges"] = nonzero.get("nudges", 0) + 1
        if record.get("thinking_reentries"):
            nonzero["thinking_reentries"] = nonzero.get("thinking_reentries", 0) + 1
        parent = record.get("parent")
        if "stop_reason" in record and record["stop_reason"] != "stop":
            nonzero["stop_reason!=stop"] = nonzero.get("stop_reason!=stop", 0) + 1
    return {
        "directory": str(directory),
        "records": len(records),
        "rungs": dict(sorted(rungs.items())),
        "nonzero": nonzero,
    }


def comparison_table(summaries: dict[str, dict]) -> str:
    names = list(summaries)
    rung_numbers = sorted({n for s in summaries.values() for n in s["rungs"]})
    lines = ["| rung | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for n in rung_numbers:
        cells = []
        for name in names:
            entry = summaries[name]["rungs"].get(n)
            cells.append(f"{entry['passed']}/{entry['runs']}" if entry else "—")
        lines.append(f"| {n} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    dirs = [Path(a) for a in (argv if argv is not None else sys.argv[1:])]
    summaries = {d.name: summarize(d) for d in dirs}
    for name, summary in summaries.items():
        print(f"## {name}: {summary['records']} runs")
        for n, entry in summary["rungs"].items():
            print(
                f"rung {n}: {entry['passed']}/{entry['runs']} pass, deadline hits {entry['deadline_hits']}, largest prompt {entry['largest_prompt_chars']} chars"
            )
        print("non-zero columns:", summary["nonzero"] or "none")
    if len(summaries) > 1:
        print(comparison_table(summaries))


if __name__ == "__main__":
    main()
