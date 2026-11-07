#!/usr/bin/env python3
"""Print the suite evidence table from scored run.json files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SUITES = ("easy", "medium", "hard")
ARMS = ("vanilla", "bare", "worker", "strip-thinking")
COLUMNS = ("Passes", "Turns", "Failed checks", "Tool errors", "Context",
           "Wall", "Output tokens", "Nudges")


def load(runs_dir: Path) -> list[dict]:
    records = []
    for path in sorted(Path(runs_dir).glob("*/run.json")):
        record = json.loads(path.read_text())
        record["_path"] = path
        records.append(record)
    return records


def _mean(records: list[dict], field: str) -> float | None:
    values = [row[field] for row in records
              if isinstance(row.get(field), (int, float))]
    return sum(values) / len(values) if values else None


def _cell(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}"


def _ordered(values: set[str], preferred: tuple[str, ...]) -> list[str]:
    known = [value for value in preferred if value in values]
    return known + sorted(values - set(known))


def render(runs_dir: Path, *, suite: str | None = None,
           arm: str | None = None) -> str:
    records = load(runs_dir)
    if suite is not None:
        records = [row for row in records if row.get("suite") == suite]
    if arm is not None:
        records = [row for row in records if row.get("arm") == arm]
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in records:
        groups.setdefault((row.get("suite", "?"), row.get("arm", "?")), []).append(row)
    lines = [
        "| Suite | Arm | " + " | ".join(COLUMNS) + " |",
        "| --- | --- | " + " | ".join("---" for _ in COLUMNS) + " |",
    ]
    suites = _ordered({key[0] for key in groups}, SUITES)
    arms = _ordered({key[1] for key in groups}, ARMS)
    for suite_name in suites:
        for arm_name in arms:
            rows = groups.get((suite_name, arm_name))
            if not rows:
                continue
            passed = sum(row.get("passed") is True for row in rows)
            values = [f"{passed}/{len(rows)}"]
            values += [_cell(_mean(rows, field)) for field in
                       ("turns", "failed_checks", "tool_errors", "context",
                        "wall", "output_tokens", "nudges")]
            lines.append(f"| {suite_name} | {arm_name} | " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("--suite")
    parser.add_argument("--arm")
    args = parser.parse_args(argv)
    print(render(args.runs_dir, suite=args.suite, arm=args.arm), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
