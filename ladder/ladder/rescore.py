"""Recompute the ``score`` block of every run.json in a directory from its trace.

The baseline line counts come from ``baseline_lines`` in run.json.

    uv run python -m ladder.rescore ../evals/baseline/2026-10-09-phase0-baseline

With ``--existing-tests-kept`` it instead recomputes only rule 3 of the
AgentClinic rungs (6 to 9), "no existing test is removed or edited; additions
are allowed", from each run's retained workspace, and writes the result next to
the recorded ``check`` as ``check_rescored``. Nothing is re-run and
``table.md`` stays as recorded.

    uv run python -m ladder.rescore --existing-tests-kept ../evals/<phase>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .run_ladder import HEADER, read_events, table_row
from .rungs import FIXTURES, RUNGS, existing_tests_kept
from .score import score


def rescore_dir(directory: Path) -> int:
    changed = 0
    rows = []
    for run_json in sorted(Path(directory).glob("*/run.json")):
        record = json.loads(run_json.read_text())
        lines = record["baseline_lines"]
        new = score(
            read_events(run_json.with_name("trace.jsonl")), set(lines), lines
        ).as_row()
        if new != record.get("score"):
            record["score"] = new
            changed += 1
        run_json.write_text(json.dumps(record, indent=2, default=str))
        if "check" in record and "stop_reason" in record:
            rows.append((record["rung"], record["repeat"], table_row(record)))
    if rows:
        Path(directory, "table.md").write_text(
            HEADER + "".join(r for _, _, r in sorted(rows))
        )
    return changed


RESCORE_RULE = "existing-tests-kept"
AGENTCLINIC_RUNGS = range(6, 10)
CARRIED_GATES = ("facts_cmd_pass", "hidden_pass")


def _not_rescorable(reason: str) -> dict:
    return {
        "passed": None,
        "tests_unchanged": None,
        "rule": RESCORE_RULE,
        "rescorable": False,
        "reason": reason,
    }


def rescore_existing_tests(directory: Path) -> dict[str, str]:
    """Write ``check_rescored`` into every rung 6 to 9 run.json; return run name -> outcome.

    Only ``tests_unchanged`` is recomputed (new rule 3, against the rung's fixture).
    ``passed`` combines it with the recorded ``facts_cmd_pass``, ``hidden_pass``
    and an empty ``outside_write_list``. A run whose workspace is gone, or whose
    recorded details lack those fields, is marked not rescorable, never re-run.
    """
    outcomes: dict[str, str] = {}
    for run_json in sorted(Path(directory).glob("*/run.json")):
        name = run_json.parent.name
        record = json.loads(run_json.read_text())
        rung = record.get("rung")
        if rung not in AGENTCLINIC_RUNGS:
            outcomes[name] = f"skipped: rung {rung} keeps its own check"
            continue
        details = record.get("check", {}).get("details", {})
        ws = Path(record.get("workspace", ""))
        if not ws.is_dir():
            reason = "workspace missing"
        elif not all(k in details for k in (*CARRIED_GATES, "outside_write_list")):
            reason = "recorded check details incomplete"
        else:
            reason = ""
        if reason:
            record["check_rescored"] = _not_rescorable(reason)
            outcomes[name] = f"not rescorable: {reason}"
        else:
            kept = existing_tests_kept(ws, FIXTURES / RUNGS[rung].fixture)
            record["check_rescored"] = {
                "passed": bool(
                    kept
                    and all(details[k] is True for k in CARRIED_GATES)
                    and details["outside_write_list"] == []
                ),
                "tests_unchanged": kept,
                "rule": RESCORE_RULE,
            }
            outcomes[name] = "rescored"
        run_json.write_text(json.dumps(record, indent=2, default=str))
    return outcomes


def main(argv: list[str]) -> None:
    if argv and argv[0] == "--existing-tests-kept":
        for arg in argv[1:]:
            for name, outcome in rescore_existing_tests(Path(arg)).items():
                print(f"{arg}/{name}: {outcome}")
        return
    for arg in argv:
        print(f"{arg}: {rescore_dir(Path(arg))} run.json files rescored")


if __name__ == "__main__":
    main(sys.argv[1:])
