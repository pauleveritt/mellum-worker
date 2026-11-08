"""R.1's batch runner: interleaved Easy sessions through the real harness, and the report.

    uv run python scripts/r1_batch.py run ARMS.json N OUT --host-card CARD [--pi-binary PI]
    uv run python scripts/r1_batch.py report OUT [--checks 13]

ARMS.json maps an arm's label to its harness flags, e.g. {"vanilla": ["--arm", "vanilla"]}.
Sessions run round-robin (round 1 of every arm, then round 2, ...) so drift in the host hits
every arm alike; each goes to OUT/<arm>-r<NN>/, and a session whose run.json exists is skipped,
so a killed batch resumes. The report counts as the R.1 preregistration fixes
(docs/superpowers/research/2026-11-07-r1-preregistration.md): mean checks and full passes over
every session; budget medians over the sessions that neither stalled nor were censored.
"""
import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "learn" / "code" / "harness.py"


def plan_sessions(arms: dict[str, list[str]], n: int) -> list[tuple[int, str]]:
    return [(k, arm) for k in range(1, n + 1) for arm in arms]


def session_dir(out: Path, arm: str, k: int) -> Path:
    return out / f"{arm}-r{k:02d}"


def harness_argv(flags: list[str], runs_dir: Path, *, host_card: Path, pi_binary: str) -> list[str]:
    return ["uv", "run", "python", str(HARNESS), "run", "--suite", "easy", "--grade", "--stall", "180",
            "--host-card", str(host_card), "--pi-binary", pi_binary, "--runs-dir", str(runs_dir), *flags]


def finished(runs_dir: Path) -> bool:
    return any(runs_dir.glob("*/run.json"))


def run_batch(sessions: list[tuple[int, str]], out: Path, argv_for) -> None:
    for k, arm in sessions:
        target = session_dir(out, arm, k)
        if finished(target):
            continue
        target.mkdir(parents=True, exist_ok=True)
        print(f"[r1_batch] {arm} round {k}", flush=True)
        subprocess.run(argv_for(arm, target), cwd=REPO, check=False)


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize(out: Path, *, checks: int) -> dict[str, dict]:
    rows: dict[str, list[dict]] = {}
    for path in sorted(out.glob("*-r[0-9][0-9]/*/run.json")):
        arm = path.parent.parent.name.rsplit("-r", 1)[0]
        rows.setdefault(arm, []).append(json.loads(path.read_text()))
    stats = {}
    for arm, runs in rows.items():
        passed = [checks - r["failed_checks"] if r.get("checks_ran") else 0 for r in runs]
        clean = [r for r in runs if r.get("completion") != "stalled" and not r.get("censored")]
        spent = [r.get("budget", {}).get("spent", {}) for r in clean]
        stats[arm] = {
            "n": len(runs),
            "mean_checks": sum(passed) / len(runs),
            "full_passes": sum(1 for p in passed if p == checks),
            "stalled": sum(1 for r in runs if r.get("completion") == "stalled"),
            "censored": sum(1 for r in runs if r.get("censored")),
            "budget_endings": sum(1 for r in runs if r.get("completion") == "budget"),
            "median_requests": _median([s["requests"] for s in spent if "requests" in s]),
            "median_output_tokens": _median([s["output_tokens"] for s in spent if "output_tokens" in s]),
        }
    return stats


def table(stats: dict[str, dict]) -> str:
    head = ("| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings "
            "| Median requests | Median output tokens |\n|---|---|---|---|---|---|---|---|---|\n")
    fmt = lambda v: "—" if v is None else (f"{v:.2f}" if isinstance(v, float) and not v.is_integer() else f"{v:g}")
    return head + "".join(
        f"| {arm} | {s['n']} | {fmt(s['mean_checks'])} | {s['full_passes']} | {s['stalled']} | {s['censored']} "
        f"| {s['budget_endings']} | {fmt(s['median_requests'])} | {fmt(s['median_output_tokens'])} |\n"
        for arm, s in stats.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("arms", type=Path)
    run.add_argument("n", type=int)
    run.add_argument("out", type=Path)
    run.add_argument("--host-card", type=Path, required=True)
    run.add_argument("--pi-binary", default=str(Path.home() / ".local" / "bin" / "pi"))
    report = sub.add_parser("report")
    report.add_argument("out", type=Path)
    report.add_argument("--checks", type=int, default=13)
    args = parser.parse_args(argv)
    if args.command == "run":
        arms = json.loads(args.arms.read_text())
        run_batch(plan_sessions(arms, args.n), args.out,
                  lambda arm, target: harness_argv(arms[arm], target, host_card=args.host_card,
                                                   pi_binary=args.pi_binary))
    else:
        text = table(summarize(args.out, checks=args.checks))
        (args.out / "table.md").write_text(text)
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
