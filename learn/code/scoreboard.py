"""The scoreboard: a merge-friendly record of every measured run, and the page it publishes.

Independent of the measurement path — it only reads finished runs and records them, and
never changes how a run is produced. Each run becomes one small JSON file under
``<board>/entries/<run-id>.json`` (one file per run, so pull requests that each add a run
touch different files and never conflict). The published page is regenerated from those
files by ``consolidate`` — run it after a merge; contributors never hand-edit the page.

CLI
    uv run python learn/code/scoreboard.py record <run-dir>... [--board DIR] [--model STR]
    uv run python learn/code/scoreboard.py consolidate [--board DIR] [--page PATH]
    uv run python learn/code/scoreboard.py show [--board DIR] [--suite NAME]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_BOARD = Path(__file__).resolve().parents[2] / "evals" / "scoreboard"
DEFAULT_PAGE = Path(__file__).resolve().parents[1] / "scoreboard.md"
_TS = re.compile(r"^(\d{4})(\d{2})(\d{2})T\d{6}Z")


def _basename(path: str) -> str:
    return os.path.basename(path).removesuffix(".ts")


def stack_label(rec: dict) -> list[str]:
    """The remedy units and mellum extensions a run used, deduped and sorted (a stable key).

    The remedy names come from ``remedies``; the worker extensions from ``extensions`` (only
    the ``mellum-*`` ones, never the recorder, which is harness plumbing). Sorting makes the
    label order-independent so the same stack always groups together.
    """
    units = list(rec.get("remedies") or [])
    for ext in rec.get("extensions") or []:
        base = _basename(ext.get("path", ""))
        if base.startswith("mellum-") and "recorder" not in base and "record" != base:
            units.append(base)
    # The arm is part of the config: a `worker` run is the shipped worker, not bare, even when
    # it loads no extra remedies. Fold a non-bare arm into the label so it never reads as bare.
    arm = rec.get("arm")
    if arm and arm != "bare":
        units.append(f"arm:{arm}")
    return sorted(set(units))


def _fingerprint(rec: dict) -> str:
    """A short, stable hash of the extension shas, so an edited extension is a new version of
    the stack. The leaderboard groups by stack *name*; the page splits records by this, so an
    improved extension shows as a new version that can beat (not blend with) the old one.
    """
    import hashlib

    shas = sorted((e.get("sha256") or "") for e in rec.get("extensions") or [] if "recorder" not in _basename(e.get("path", "")))
    joined = ",".join(s for s in shas if s)
    return hashlib.sha256(joined.encode()).hexdigest()[:8] if joined else "—"


def _date_from(run_dir: Path, rid: str) -> str:
    m = _TS.match(rid)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    rj = run_dir / "run.json"
    try:
        from datetime import datetime, timezone

        return datetime.fromtimestamp(rj.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    except OSError:
        return ""


def entry_from_run(run_dir, model: str | None = None) -> dict:
    """Read a harness run dir into a flat scoreboard entry. ``model`` overrides a run that
    predates run.json carrying it (older runs have no model field)."""
    run_dir = Path(run_dir)
    rec = json.loads((run_dir / "run.json").read_text())
    rid = run_dir.name
    # An explicit --model override wins (so a vast batch can stamp A6000/<quant> even though
    # run.json carries the profile's generic model id); else run.json, else model.txt.
    mdl = model or rec.get("model")
    if mdl is None:
        mt = run_dir / "model.txt"
        mdl = mt.read_text().strip() if mt.is_file() else None
    return {
        "id": rid,
        "date": _date_from(run_dir, rid),
        "suite": rec.get("suite"),
        "model": mdl,
        "arm": rec.get("arm"),
        "stack": stack_label(rec),
        "version": _fingerprint(rec),
        "passed": bool(rec.get("passed")),
        "turns": rec.get("turns"),
        "tool_calls": rec.get("tool_calls"),
        "wall": rec.get("wall"),
        "missing": len(rec.get("missing_checks") or []),
        "machine": rec.get("machine"),
    }


def record(run_dirs, board, model: str | None = None) -> list[Path]:
    """Write one entry file per run under ``<board>/entries/``; re-recording a run overwrites
    its own file (idempotent), and no shared file is touched (merge-friendly)."""
    board = Path(board)
    entries = board / "entries"
    entries.mkdir(parents=True, exist_ok=True)
    written = []
    for d in run_dirs:
        if not (Path(d) / "run.json").is_file():
            continue  # a run that never graded (stalled before scoring) is not a scoreboard entry
        e = entry_from_run(d, model=model)
        path = entries / f"{e['id']}.json"
        path.write_text(json.dumps(e, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


def load_entries(board) -> list[dict]:
    entries = Path(board) / "entries"
    out = []
    if entries.is_dir():
        for p in sorted(entries.glob("*.json")):
            try:
                out.append(json.loads(p.read_text()))
            except (OSError, json.JSONDecodeError):
                continue
    return out


def leaderboard(entries) -> dict:
    """Group by (suite, model, stack-names); the record is the fewest-turn pass, then least wall."""
    groups: dict[tuple, list[dict]] = {}
    for e in entries:
        key = (e.get("suite"), e.get("model"), tuple(e.get("stack") or ()))
        groups.setdefault(key, []).append(e)
    board = {}
    for key, runs in groups.items():
        passes = [r for r in runs if r.get("passed")]
        best = min(passes, key=lambda r: (r.get("turns") or 1 << 30, r.get("wall") or 1e18)) if passes else None
        board[key] = {"best": best, "passed": len(passes), "total": len(runs), "runs": runs}
    return board


def _fmt_wall(w) -> str:
    return "—" if w is None else f"{round(w)}s"


def _stack_text(stack) -> str:
    if not stack:
        return "— bare —"
    return " · ".join(s.replace("tool/background-long-commands", "nonblock").replace("mellum-", "") for s in stack)


def render_page(entries) -> str:
    lines = [
        "# Scoreboard",
        "",
        "Every Mellum worker run ever measured. **Records** are the fastest pass per "
        "configuration — fewest turns, then least wall, because a shorter run is the better "
        "pass. Every run follows below.",
        "",
        "![A small robot posting run times on a leaderboard, stopwatch in hand](assets/illustrations/scoreboard.webp){ .illustration }",
        "",
        "!!! note",
        "",
        "    Generated by `learn/code/scoreboard.py consolidate`; do not edit by hand. To add a"
        " run, commit its entry file under `evals/scoreboard/entries/` — the page is rebuilt"
        " after merge.",
        "",
        f"{len(entries)} runs recorded.",
        "",
        "## Records",
        "",
        "A code change to an extension is a new **version** of the same stack, so an improvement"
        " shows as a new row that can beat the old one rather than blending into it.",
        "",
        "| suite | model | stack | version | pass | best turns | best wall |",
        "|---|---|---|---|---|---|---|",
    ]
    # Records split by version (suite, model, stack-names, version), so v2 never blends with v1.
    vgroups: dict[tuple, list[dict]] = {}
    for e in entries:
        key = (e.get("suite"), e.get("model"), tuple(e.get("stack") or ()), e.get("version") or "—")
        vgroups.setdefault(key, []).append(e)
    rows = []
    for (suite, model, stack, ver), runs in vgroups.items():
        passes = [r for r in runs if r.get("passed")]
        best = min(passes, key=lambda r: (r.get("turns") or 1 << 30, r.get("wall") or 1e18)) if passes else None
        bt = best["turns"] if best else "—"
        bw = _fmt_wall(best["wall"]) if best else "—"
        rank = best["turns"] if best else 1 << 30
        rows.append((rank, f"| {suite} | {model or '—'} | {_stack_text(stack)} | `{ver}` | {len(passes)}/{len(runs)} | {bt} | {bw} |"))
    for _, row in sorted(rows):
        lines.append(row)
    lines += [
        "",
        "## All runs",
        "",
        "Newest first. Turns and wall-clock are shown for every run.",
        "",
        "| date | suite | model | stack | result | turns | wall | run |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in sorted(entries, key=lambda e: (e.get("date") or "", e.get("id") or ""), reverse=True):
        res = "pass" if e.get("passed") else "fail"
        lines.append(
            f"| {e.get('date') or '—'} | {e.get('suite')} | {e.get('model') or '—'} | "
            f"{_stack_text(e.get('stack'))} | {res} | {e.get('turns')} | {_fmt_wall(e.get('wall'))} | `{e.get('id')}` |"
        )
    return "\n".join(lines) + "\n"


def consolidate(board, page) -> Path:
    page = Path(page)
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(render_page(load_entries(board)))
    return page


def _show(entries, suite=None) -> str:
    board = leaderboard([e for e in entries if suite is None or e.get("suite") == suite])
    out = ["Records (fastest pass per config) — turns / wall:"]
    for (s, model, stack), v in sorted(board.items()):
        best = v["best"]
        bt = f"{best['turns']}t {_fmt_wall(best['wall'])}" if best else "— (no pass)"
        out.append(f"  {s:7} {_stack_text(stack)[:46]:46} {v['passed']}/{v['total']:<3} {bt}")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mellum worker scoreboard")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="record one or more run dirs")
    r.add_argument("run_dirs", nargs="+")
    r.add_argument("--board", default=str(DEFAULT_BOARD))
    r.add_argument("--model", default=None, help="model id for runs whose run.json lacks one")
    c = sub.add_parser("consolidate", help="regenerate the published page from entries")
    c.add_argument("--board", default=str(DEFAULT_BOARD))
    c.add_argument("--page", default=str(DEFAULT_PAGE))
    s = sub.add_parser("show", help="print the leaderboard")
    s.add_argument("--board", default=str(DEFAULT_BOARD))
    s.add_argument("--suite", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "record":
        written = record(args.run_dirs, args.board, model=args.model)
        print(f"recorded {len(written)} run(s) -> {Path(args.board) / 'entries'}")
    elif args.cmd == "consolidate":
        page = consolidate(args.board, args.page)
        print(f"wrote {page} from {len(load_entries(args.board))} entries")
    elif args.cmd == "show":
        print(_show(load_entries(args.board), suite=args.suite))
    return 0


if __name__ == "__main__":
    sys.exit(main())
