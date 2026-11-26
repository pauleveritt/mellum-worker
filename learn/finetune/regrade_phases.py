#!/usr/bin/env python3
"""Grade every phase of a recorded multi-phase run on its OWN end state.

Replays the trace's successful write/edit calls on the suite's base files
(replay.py), checks the replayed final state grades exactly like the recorded run
(bash edits are not replayed, so a mismatch means the replay can't be trusted),
then grades each phase's snapshot with the hidden grader and writes
`phase_grades.json` beside run.json: {"verified": bool, "phases": {N: missing==0 for
that phase's module}}.
"""
import argparse, glob, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "learn" / "code"))
import harness  # noqa: E402
from replay import phase_snapshots  # noqa: E402

SKIP = {".venv", "__pycache__", ".pytest_cache", "grader_tests"}


def read_base(base):
    out = {}
    for p in base.rglob("*"):
        if p.is_file() and not SKIP & set(p.relative_to(base).parts):
            try:
                out[str(p.relative_to(base))] = p.read_text()
            except UnicodeDecodeError:
                pass
    return out


def grade_module(files, suite, n):
    """Missing expected ids of phase n's own grader module (a later module may import
    code the phase hasn't written yet, which would fail the whole collection)."""
    import shutil, subprocess, os
    mod = [t for t in suite.expected if f"test_phase{n}_" in t]
    if not mod:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        for rel, text in files.items():
            (ws / rel).parent.mkdir(parents=True, exist_ok=True)
            (ws / rel).write_text(text)
        shutil.copytree(suite.tests, ws / "grader_tests")
        out = subprocess.run(["uv", "run", "--with", "pytest", "pytest", "-q", "-rA", mod[0].split("::")[0]],
                             cwd=ws, capture_output=True, text=True,
                             env={**os.environ, "PYTHONPATH": str(ws)})
        text = out.stdout + out.stderr
    return {t for t in mod if f"PASSED {t}" not in text}


def find_regressions(own, passes):
    """{phase m: [earlier phases k it broke]}: k passed at its own end but fails on m's end state."""
    return {m: [k for k in sorted(own) if k < m and own[k] and not passes(m, k)] for m in sorted(own) if m > 1}


def grade(files, suite):
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        for rel, text in files.items():
            (ws / rel).parent.mkdir(parents=True, exist_ok=True)
            (ws / rel).write_text(text)
        for lock in (suite.root / "base").glob("uv.lock"):
            (ws / "uv.lock").write_bytes(lock.read_bytes())
        _ok, _tail, missing, _ran = harness.score_workspace_details(ws, suite)
    return set(missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--regressions", action="store_true",
                    help="for runs already graded and verified, also record which earlier phases each phase broke "
                         "(phase_regressions.json)")
    a = ap.parse_args()
    suites = {}
    for root in a.roots:
        for f in sorted(glob.glob(f"{root}/**/run.json", recursive=True)):
            run = json.load(open(f)); d = Path(f).parent
            name = run.get("suite")
            done = d / ("phase_regressions.json" if a.regressions else "phase_grades.json")
            if not name or not (d / "trace.jsonl").is_file() or done.is_file():
                continue
            if a.regressions:
                pg = d / "phase_grades.json"
                graded = json.loads(pg.read_text()) if pg.is_file() else {}
                if not graded.get("verified"):
                    continue
            if name not in suites:
                try:
                    suites[name] = harness.load_suite(ROOT / "learn" / "code" / "suites", name)
                except Exception:
                    suites[name] = None
            suite = suites[name]
            if suite is None or len(suite.prompts) < 2:
                continue
            rows = [json.loads(line) for line in open(d / "trace.jsonl") if line.strip()]
            snaps = phase_snapshots(read_base(suite.root / "base"), rows, str(d / "workspace"))
            recorded = set(run.get("missing_checks") or [])
            if a.regressions:
                own = {int(k): v for k, v in graded["phases"].items()}

                def passes(m, k):
                    if m == len(snaps):
                        return not (set(t for t in suite.expected if f"test_phase{k}_" in t) & recorded)
                    return not grade_module(snaps[m - 1], suite, k)
                regressed = find_regressions(own, passes)
                done.write_text(json.dumps({"verified": True, "regressed": regressed}) + "\n")
                print(f"{d.name}: regressed={regressed}", flush=True)
                continue
            final = grade(snaps[-1], suite) if snaps else None
            verified = final == recorded and bool(run.get("checks_ran"))
            phases = {}
            if verified:
                for i, snap in enumerate(snaps[:-1], start=1):
                    missing = grade_module(snap, suite, i)
                    if missing is not None:
                        phases[i] = not missing
                mod = [t for t in suite.expected if f"test_phase{len(snaps)}_" in t]
                phases[len(snaps)] = bool(mod) and not (set(mod) & recorded)
            (d / "phase_grades.json").write_text(json.dumps({"verified": verified, "phases": phases}) + "\n")
            print(f"{d.name}: verified={verified} phases={phases}", flush=True)


if __name__ == "__main__":
    main()
