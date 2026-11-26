#!/usr/bin/env python3
"""Version-aware Python feature tasks: does the model find out which Python a project uses, and use it well?

Every task lives in `suites/py-features/<name>/` and declares its feature version in `task.json`:

    {"python": "3.15", "kind": "new-api", "pep": "PEP 661"}

- `new-api`: the project is pinned to `python`; only the new feature passes the hidden tests. The prompt
  describes behaviour and never names the version or the feature: the model has to check the project.
- `trap`:    the same kind of request in a project pinned to the version BEFORE `python`; the new feature
  crashes there, so reaching for the newest idiom without checking the version fails.
- `fix`:     code that broke on `python` (a removed API, a new SyntaxError); the model diagnoses and fixes it.

Nothing here names a version, so a new Python release is new tasks, not new code:

    uv python install 3.16
    uv run python py_features.py new <name> --python 3.16 --kind new-api --pep "PEP ..."
    ...write base/, prompts/01.md, grader/, fixtures/reference/, fixtures/workaround/, expected.json...
    uv run python py_features.py check

`check` proves each task before any model run: the reference passes on the pinned version, the workaround and
the untouched base fail there, and (for `new-api`) the reference fails on the version before, so the task
really needs the feature. A task that fails any direction is not a test of anything.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "suites" / "py-features"
IGNORE = [".venv/**", "__pycache__/**", "*.pyc", ".pytest_cache/**", "grader_tests/**", "uv.lock"]
AGENTS = """# {name}

A small Python project.

- Test command: uv run python -m pytest tests
- Run Python commands with uv run.
- Keep changes scoped to the task; do not weaken existing tests.
- Before reporting completion, run the test command and report its result.
"""


def predecessor(version, explicit=None):
    """The minor release before `version` (3.16 -> 3.15). A major bump has no rule, so it must be given."""
    if explicit:
        return explicit
    major, minor = (int(x) for x in version.split("."))
    if minor == 0:
        raise ValueError(f"no rule for the release before {version}; set \"predecessor\" in task.json")
    return f"{major}.{minor - 1}"


def pinned(meta):
    """The Python a task's project is pinned to: its feature version, or the one before for a trap."""
    if meta["kind"] == "trap":
        return predecessor(meta["python"], meta.get("predecessor"))
    return meta["python"]


def _pin(project, version):
    (project / ".python-version").write_text(f"{version}\n")
    name = project.parent.name if project.name == "base" else project.name
    (project / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\nrequires-python = "=={version}.*"\n'
        f'dependencies = []\n\n[dependency-groups]\ndev = ["pytest"]\n')


def scaffold(root, name, python, kind, pep):
    """Create an empty task, pinned and laid out, for the author to fill in."""
    meta = {"python": python, "kind": kind, "pep": pep}
    version = pinned(meta)
    task = Path(root) / (f"py{version}-{name}-of-{python}" if kind == "trap" else f"py{version}-{name}")
    for part in ("base/tests", "prompts", "grader", "fixtures/reference", "fixtures/workaround"):
        (task / part).mkdir(parents=True, exist_ok=True)
    (task / "task.json").write_text(json.dumps(meta, indent=2) + "\n")
    _pin(task / "base", version)
    (task / "base" / "AGENTS.md").write_text(AGENTS.format(name=task.name))
    (task / "base" / "tests" / "__init__.py").write_text("")
    (task / "prompts" / "01.md").write_text("TODO: describe the behaviour. Never name the Python version or the feature.\n")
    (task / "layout.json").write_text(json.dumps({"allow": ["*.py", "**/*.py", "tests/**"], "ignore": IGNORE},
                                                 indent=2) + "\n")
    (task / "expected.json").write_text("[]\n")
    return task


def discover(root=ROOT):
    """Every task, of every version, in name order."""
    return sorted(p.parent for p in Path(root).glob("*/task.json"))


def grade(task, overlay, version):
    """Expected ids that pass with `overlay` copied over the base, run on Python `version`."""
    expected = json.loads((task / "expected.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / task.name
        shutil.copytree(task / "base", ws)
        if overlay:
            shutil.copytree(overlay, ws, dirs_exist_ok=True)
        _pin(ws, version)
        shutil.copytree(task / "grader", ws / "grader_tests")
        env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PYTHON")}
        env["PYTHONPATH"] = str(ws)
        done = subprocess.run(
            ["uv", "run", "--python", version, "--with", "pytest", "python", "-m", "pytest", "-rA",
             "-p", "no:cacheprovider", "grader_tests"],
            cwd=ws, capture_output=True, text=True, env=env)
    output = done.stdout + done.stderr
    return {test_id for test_id in expected if f"PASSED {test_id}" in output}, output


def check(task):
    """Prove a task in every direction; `ok` only when each one comes out as it must."""
    task = Path(task)
    meta = json.loads((task / "task.json").read_text())
    expected = set(json.loads((task / "expected.json").read_text()))
    version = pinned(meta)
    fixtures = task / "fixtures"

    def colour(overlay, on):
        passed, _ = grade(task, overlay, on)
        return "green" if expected and passed == expected else "red"

    verdict = {"pinned": version, "expected": len(expected),
               "reference_on_target": colour(fixtures / "reference", version),
               "workaround_on_target": colour(fixtures / "workaround", version),
               "base_on_target": colour(None, version)}
    want = {"reference_on_target": "green", "workaround_on_target": "red", "base_on_target": "red"}
    if meta["kind"] == "new-api":
        verdict["reference_on_predecessor"] = colour(fixtures / "reference",
                                                     predecessor(version, meta.get("predecessor")))
        want["reference_on_predecessor"] = "red"
    verdict["ok"] = bool(expected) and all(verdict[k] == v for k, v in want.items())
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT, help="the task folder (default: the eval suite)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    new = sub.add_parser("new")
    new.add_argument("name")
    new.add_argument("--python", required=True)
    new.add_argument("--kind", choices=["new-api", "trap", "fix"], required=True)
    new.add_argument("--pep", required=True)
    chk = sub.add_parser("check")
    chk.add_argument("--root", type=Path, default=argparse.SUPPRESS)
    chk.add_argument("tasks", nargs="*")
    a = ap.parse_args()
    if a.cmd == "new":
        print(scaffold(a.root, a.name, a.python, a.kind, a.pep))
        return
    tasks = [a.root / t for t in a.tasks] or discover(a.root)
    bad = 0
    for task in tasks:
        v = check(task)
        bad += not v["ok"]
        detail = ", ".join(f"{k}={v[k]}" for k in v if k not in ("ok",))
        print(f"{'PASS' if v['ok'] else 'FAIL'}  {task.name}: {detail}", flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
