"""Run ladder/fixtures/acceptance/test_medium.py against every medium witness build.

The witness builds (one known-good build plus named edits, and two saved run builds)
are Paul's, from `learn/code/qualify_matrix.py` on pauleveritt/mellum-worker
`andre-integration`. They are read from that git ref, never merged. No model runs.

    git fetch upstream andre-integration
    uv run python docs/superpowers/research/2026-11-13-test-medium-qualified/qualify.py

Exits non-zero if any witness is classified against its expected verdict. One
departure from Paul's labels: `newest_first` (the board shown newest first) is
expected to be rejected, because our 18-check hidden grader rejects it and the
acceptance test must be a superset of that grader.
"""
import argparse, io, os, re, shutil, subprocess, sys, tarfile, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OVERRIDE = {"newest_first": "defect"}


def extract(ref: str, into: Path) -> Path:
    paths = ["learn/code/qualify_matrix.py", "learn/code/suites/medium/fixtures"]
    tar = subprocess.run(["git", "archive", ref, *paths], cwd=REPO, capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(into, filter="data")
    return into


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="upstream/andre-integration")
    ap.add_argument("--test", default=str(REPO / "ladder/fixtures/acceptance/test_medium.py"))
    args = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="qualify-medium-"))
    paul = extract(args.ref, work / "paul")
    src = (paul / "learn/code/qualify_matrix.py").read_text()
    ns: dict = {}
    exec(src[src.index("OPEN_BADGE"):src.index("EASY_VALID")], ns)  # the witness edit tables only
    fixtures = paul / "learn/code/suites/medium/fixtures"

    def build(name, edits):
        root = work / "builds" / name
        shutil.copytree(REPO / "learn/code/suites/medium/base", root)
        shutil.copytree(fixtures / ("witnesses/" + edits if isinstance(edits, str) else "known-good"), root, dirs_exist_ok=True)
        for path, old, new in ([] if isinstance(edits, str) else edits):
            target = root / path
            assert old in target.read_text(), (name, path, old)
            target.write_text(target.read_text().replace(old, new))
        return root

    def run(item):
        name, kind, edits = item
        root = build(name, edits)
        env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "VIRTUAL_ENV")}
        env.update(PYTHONPATH=str(root), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        r = subprocess.run(["uv", "run", "--frozen", "--offline", "python", "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider", args.test],
                           cwd=root, env=env, capture_output=True, text=True, timeout=240)
        assert r.returncode in (0, 1), r.stdout[-2000:] + r.stderr[-2000:]
        failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) \S+::(\w+)", r.stdout, re.M)))
        verdict = "reject" if r.returncode else "pass"
        expected = OVERRIDE.get(name, kind)
        return name, kind, verdict, (verdict == "pass") == (expected == "valid"), failed

    items = ([(n, "valid", e) for n, e in ns["MEDIUM_VALID"].items()]
             + [(n, "defect", e) for n, e in ns["MEDIUM_DEFECT"].items()]
             + [(n, "defect", n) for n in ("base-r02", "base-r03")])
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(run, items))
    print("| witness | Paul's label | verdict | as expected | failing tests |\n|---|---|---|---|---|")
    for name, kind, verdict, ok, failed in rows:
        print(f"| {name} | {kind} | {verdict} | {'yes' if ok else 'NO'} | {', '.join(failed)} |")
    good = sum(r[3] for r in rows)
    print(f"\n{good}/{len(rows)} as expected")
    shutil.rmtree(work, ignore_errors=True)
    return 0 if good == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
