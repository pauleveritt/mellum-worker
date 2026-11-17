"""improve — an opt-in improvement loop that carries learnings forward across runs.

It is the one producer that tries to make later runs *better*: after each rep it folds what
the run records teach (via mellum-learn) into a carried `## Mellum` section, so the next rep
starts knowing it. The shipped worker (`--arm worker`) injects that section as facts.

Independent of the measurement path by construction:
  * it runs against a **temp copy** of the suite — the real suite base is never written;
  * records go to the loop's own `MELLUM_MODE_RUNS`, not the user's default file;
  * runs land under the loop's own `--out` dir;
  * it changes no measured default — it only adds the carried facts, which the worker already
    reads. Each rep is recorded to the scoreboard like any other run.

    uv run python learn/code/improve.py --suite easy --iterations 5 \
        --suites-dir learn/code/suites --profile <profile> --out runs/improve-easy [--board evals/scoreboard]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parent
DISTILL = CODE / "improve_distill.mjs"
HARNESS = CODE / "harness.py"


def seed_suite(suites_dir: Path, suite: str, dest: Path) -> Path:
    """Copy one suite into a temp suites-dir so the loop never writes the real suite base."""
    src = suites_dir / suite
    if not src.is_dir():
        raise SystemExit(f"no such suite: {src}")
    dst = dest / suite
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def carried_path(out: Path) -> Path:
    return out / "AGENTS.carry.md"


def inject_carry(carry: Path, suite_copy: Path) -> None:
    """Write the carried AGENTS.md into the temp suite's base, where the worker reads it."""
    base_agents = suite_copy / "base" / "AGENTS.md"
    base_agents.parent.mkdir(parents=True, exist_ok=True)
    base_agents.write_text(carry.read_text() if carry.is_file() else "")


def harness_argv(suite: str, tmp_suites: Path, profile: Path, iter_out: Path, arm: str, deadline: float, stall: float,
                 remedies: str | None = None, extensions: tuple[str, ...] = ()) -> list[str]:
    argv = [
        "uv", "run", "python", str(HARNESS), "run",
        "--suite", suite, "--suites-dir", str(tmp_suites),
        "--arm", arm, "--grade", "--repeat", "1",
        "--deadline", str(deadline), "--stall", str(stall),
        "--profile", str(profile), "--runs-dir", str(iter_out),
    ]
    if remedies:
        argv += ["--remedy", remedies]
    for ext in extensions:
        argv += ["--extension", ext]
    return argv


def latest_run_dir(iter_out: Path):
    cands = [d for d in iter_out.glob("*/") if (d / "run.json").is_file()]
    return max(cands, key=lambda d: d.stat().st_mtime) if cands else None


def distill_into_carry(records: Path, carry: Path, cwd_ancestor: Path, run_json: Path | None) -> None:
    argv = ["node", str(DISTILL), "--agents", str(carry), "--records", str(records), "--cwd", str(cwd_ancestor), "--n", "50"]
    if run_json is not None and run_json.is_file():
        argv += ["--run", str(run_json)]  # the graded verdict (out_of_layout, contaminated) — reliably present
    subprocess.run(argv, check=False)


def run_loop(args) -> int:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp_suites = out / "suite"
    tmp_suites.mkdir(exist_ok=True)
    suite_copy = seed_suite(Path(args.suites_dir), args.suite, tmp_suites)
    carry = carried_path(out)
    # Seed the carried file from the suite's own base AGENTS.md (its starting facts).
    base = suite_copy / "base" / "AGENTS.md"
    if not carry.exists():
        carry.write_text(base.read_text() if base.is_file() else "")
    records = out / "records.jsonl"
    records.write_text("")  # the loop's own records file; not the user's default
    env = {**os.environ, "MELLUM_MODE_RUNS": str(records)}
    env.pop("VIRTUAL_ENV", None)

    rows = []
    for i in range(1, args.iterations + 1):
        inject_carry(carry, suite_copy)
        iter_out = out / f"iter-{i}"
        argv = harness_argv(args.suite, tmp_suites, Path(args.profile).resolve(), iter_out, args.arm, args.deadline, args.stall,
                            remedies=args.remedy, extensions=tuple(args.extension or ()))
        if args.dry_run:
            print(f"[dry-run] iter {i}: {' '.join(argv)}")
            print(f"[dry-run] carried AGENTS.md bytes: {carry.stat().st_size}; records -> {records}")
            continue
        print(f"== improve iter {i}/{args.iterations} ({args.suite}, arm={args.arm}) ==")
        subprocess.run(argv, env=env, check=False)
        rd = latest_run_dir(iter_out)
        if rd is None:
            print(f"  iter {i}: no run.json produced"); continue
        rec = json.loads((rd / "run.json").read_text())
        rows.append((i, rec.get("passed"), rec.get("turns"), round(rec.get("wall", 0)), len(rec.get("missing_checks") or [])))
        print(f"  iter {i}: {'PASS' if rec.get('passed') else 'FAIL'} turns={rec.get('turns')} wall={round(rec.get('wall',0))}s miss={len(rec.get('missing_checks') or [])}")
        # carry this run's lessons into the next iteration (mode records + the graded verdict)
        distill_into_carry(records, carry, out, rd / "run.json")
        if args.board:
            subprocess.run(["uv", "run", "python", str(CODE / "scoreboard.py"), "record", str(rd), "--board", args.board], check=False)

    if not args.dry_run:
        table = ["# improve loop — turns/wall across iterations", "", "| iter | result | turns | wall | miss |", "|---|---|---|---|---|"]
        for i, p, t, w, m in rows:
            table.append(f"| {i} | {'PASS' if p else 'FAIL'} | {t} | {w}s | {m} |")
        (out / "table.md").write_text("\n".join(table) + "\n")
        print(f"\n== wrote {out / 'table.md'} ==")
        print("Does turn-count fall across iterations as the carried facts grow? That is the signal.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="carry-forward improvement loop (independent of measurement)")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--suites-dir", default=str(CODE / "suites"))
    ap.add_argument("--iterations", type=int, default=5)
    ap.add_argument("--arm", default="worker", help="worker (facts on — the carry channel) by default")
    ap.add_argument("--remedy", default=None, help="remedy units to stack on the arm (comma-separated)")
    ap.add_argument("--extension", action="append", default=[], help="an extra extension to load (repeatable)")
    ap.add_argument("--profile", default=str(CODE / "profile"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--deadline", type=float, default=1800.0)
    ap.add_argument("--stall", type=float, default=120.0)
    ap.add_argument("--board", default=None, help="also record each rep to this scoreboard")
    ap.add_argument("--dry-run", action="store_true", help="set up the temp suite + carry and print the commands, run no model")
    return run_loop(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
