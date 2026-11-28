#!/usr/bin/env python3
"""Turn satyrn-evals tasks into harness suites, for recording on-policy training runs.

A satyrn task has `base/` (the starting repo), a written `contract`, a hidden oracle
(`overlay/`, or a visible test in `base/` for the smallest tasks), `expected_test_ids`
and `source_paths`. The harness suite gets:

- `base/`        the starting repo (the hidden oracle never goes in);
- `prompts/01.md` the contract, verbatim;
- `grader/`      the oracle tests, copied to `grader_tests/` at grading time;
- `expected.json` every expected test id, under `grader_tests/`;
- `layout.json`  `source_paths` as the allow list (a directory becomes `dir/**`);
- `fixtures/`    the task's known-good / known-broken patches, for `--check`.

`--check` proves each converted suite in both directions before any model run: the
grader passes every expected test on base + known-good, and fails on base + known-broken.
"""
import argparse
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from grading import passed_tests  # noqa: E402

IGNORE = [".venv/**", "__pycache__/**", "*.pyc", "*.log", "*.db", ".git/**",
          ".pytest_cache/**", "grader_tests/**"]


def convert_task(task: Path, out_root: Path) -> Path:
    manifest = json.loads((task / "manifest.json").read_text())
    suite = out_root / f"satyrn-{manifest['name']}"
    if suite.exists():
        shutil.rmtree(suite)
    shutil.copytree(task / "base", suite / "base")
    (suite / "prompts").mkdir(parents=True)
    (suite / "prompts" / "01.md").write_text(manifest["contract"].rstrip() + "\n")
    files = sorted({tid.split("::")[0] for tid in manifest["expected_test_ids"]})
    src = task / manifest["grader_overlay"] if manifest.get("grader_overlay") else task / "base"
    (suite / "grader").mkdir()
    for rel in files:
        dest = suite / "grader" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, dest)
    (suite / "expected.json").write_text(json.dumps(
        [f"grader_tests/{tid}" for tid in manifest["expected_test_ids"]], indent=2) + "\n")
    allow = [p if Path(p).suffix else f"{p.rstrip('/')}/**" for p in manifest["source_paths"]]
    (suite / "layout.json").write_text(json.dumps({"allow": allow, "ignore": IGNORE}, indent=2) + "\n")
    if (task / "fixtures").is_dir():
        shutil.copytree(task / "fixtures", suite / "fixtures")
    return suite


def passed_ids(output: str, expected: set[str]) -> set[str]:
    """Expected ids reported PASSED, matched whole as the harness does (ids may hold spaces)."""
    return passed_tests(output, expected)


def grade(workspace: Path, suite: Path) -> set[str]:
    """Expected ids that pass, graded the way the harness grades (grader_tests/, -rA)."""
    expected = set(json.loads((suite / "expected.json").read_text()))
    shutil.copytree(suite / "grader", workspace / "grader_tests", dirs_exist_ok=True)
    cmd = (["uv", "run", "--with", "pytest", "pytest", "-q", "-rA", "grader_tests"]
           if (workspace / "pyproject.toml").is_file() else ["uvx", "pytest", "-q", "-rA", "grader_tests"])
    out = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True,
                         env={"PATH": __import__("os").environ["PATH"], "HOME": str(Path.home()),
                              "PYTHONPATH": str(workspace)}).stdout
    return passed_ids(out, expected)


def check(suite: Path) -> tuple[bool, str]:
    expected = set(json.loads((suite / "expected.json").read_text()))
    verdict = {}
    for kind in ("known-good", "known-broken"):
        patch = (suite / "fixtures" / f"{kind}.patch").resolve()
        if not patch.is_file():
            return False, f"no {kind}.patch"
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            shutil.copytree(suite / "base", ws)
            applied = subprocess.run(["git", "apply", "--unsafe-paths", str(patch)], cwd=ws,
                                     capture_output=True, text=True)
            if applied.returncode:
                applied = subprocess.run(["patch", "-p1", "-i", str(patch)], cwd=ws, capture_output=True, text=True)
            if applied.returncode:
                return False, f"{kind} patch does not apply: {applied.stderr.strip()[:200]}"
            verdict[kind] = grade(ws, suite) >= expected
    ok = verdict["known-good"] and not verdict["known-broken"]
    return ok, f"good={'green' if verdict['known-good'] else 'RED'} broken={'red' if not verdict['known-broken'] else 'GREEN'}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, required=True, help="satyrn-evals src/satyrn_evals/tasks")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", action="append", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for name in a.only:
        suite = convert_task(a.tasks / name, a.out)
        line = f"{suite.name}: converted"
        if a.check:
            ok, why = check(suite)
            line += f", check {'PASS' if ok else 'FAIL'} ({why})"
        print(line, flush=True)
