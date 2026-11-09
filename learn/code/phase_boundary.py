"""F.8: one requested phase at a time, verified at its boundary.

A phase run sends one prompt, grades the workspace on that phase and every earlier one (never a
later one), and only a trusted accepted result becomes a checkpoint the next phase can start from.
"""
from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

PHASE_MODULE = re.compile(r"test_phase(\d+)_")
MEDIATED_FILE = re.compile(r"test_(\d+)_")


def in_scope(name: str, phase: int | None) -> bool:
    """A grader module or node belongs to phase <= `phase`; one not named by phase always does."""
    match = PHASE_MODULE.search(name)
    return phase is None or match is None or int(match.group(1)) <= phase


def phase_scope(suite, phase: int):
    """The suite graded on `phase` and every earlier phase: later phases' checks are left out."""
    if phase < 1:
        raise SystemExit(f"phase must be 1 or more, not {phase}")
    return replace(suite, phase=phase,
                   expected=tuple(node for node in suite.expected if in_scope(node.split("::")[0], phase)))


def phase_prompt(suite, phase: int) -> str:
    """The brief for one phase: `prompts/NN.md`, else `phase-prompts/NN.md`, which only phase runs read."""
    from harness import _read_prompt
    for folder in ("prompts", "phase-prompts"):
        path = Path(suite.root) / folder / f"{phase:02d}.md"
        if path.is_file():
            return _read_prompt(path)
    raise SystemExit(f"suite {suite.name} has no prompt for phase {phase}")


def phase_mediated(suite, phase: int) -> list[Path]:
    """Mediated tests for phases <= `phase`: the selected bundle's file wins over the suite's by name."""
    folders = [Path(suite.root) / "mediated"]
    if suite.grader_base is not None:
        folders.append(Path(suite.grader_base).parent / "mediated")
    chosen: dict[str, Path] = {}
    for folder in folders:
        for path in sorted(folder.glob("test_*.py")) if folder.is_dir() else []:
            match = MEDIATED_FILE.match(path.name)
            if match is None:
                raise SystemExit(f"mediated test {path.name} must be named test_NN_<topic>.py")
            if int(match.group(1)) <= phase:
                chosen[path.name] = path
    return [chosen[name] for name in sorted(chosen)]


def gate_verdicts(run: Path) -> list[dict]:
    """The settle gate's verdicts for this run, in order; a line cut short by a killed session is skipped."""
    path = Path(run) / "gate.jsonl"
    verdicts = []
    for line in path.read_text(errors="replace").splitlines() if path.is_file() else []:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            verdicts.append(row)
    return verdicts


def test_functions(path: Path) -> list[str]:
    """Test functions pytest collects by default: module-level `test*`, and `test*` methods of `Test*` classes."""
    names = []
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            names.append(node.name)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            names += [item.name for item in node.body
                      if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test")]
    return names


def _function_key(nodeid: str) -> str:
    parts = nodeid.split("::")
    return f"{Path(parts[0]).name}::{re.sub(r'\[.*$', '', parts[-1])}"


def mediated_result(workspace: Path, suite, files: list[Path], grade_user: str | None = None) -> dict:
    """The mediated tests, run through the trusted grading path; every test function must pass."""
    from grading import evaluate
    record = [{"name": Path(f).name, "sha256": hashlib.sha256(Path(f).read_bytes()).hexdigest()} for f in files]
    if not files:
        return {"ran": False, "passed": True, "expected": [], "missing": [], "files": record}
    expected = [f"{Path(f).name}::{name}" for f in files for name in test_functions(f)]
    with tempfile.TemporaryDirectory(prefix="mellum-mediated-") as folder:
        for f in files:
            shutil.copyfile(f, Path(folder) / Path(f).name)
        result = evaluate(workspace, replace(suite, tests=Path(folder), expected=(), phase=None),
                          include_project=False, grade_user=grade_user)
    passed = {_function_key(node) for node, stages in result["hidden_reports"].items()
              if stages.get("call") == "passed" and all(value == "passed" for value in stages.values())}
    failed = {_function_key(node) for node, stages in result["hidden_reports"].items()
              if any(value == "failed" for value in stages.values())}
    missing = [key for key in expected if key not in passed or key in failed]
    return {"ran": result["checks_ran"], "passed": bool(result["checks_ran"] and expected and not missing),
            "expected": expected, "missing": missing, "files": record}


def decide(run: Path | None, suite, *, ending: str, evaluation: dict, quality_ok: bool, contaminated: bool | None,
           record_failures: list[str], mediated: dict, armed: bool) -> dict:
    """The boundary verdict. Accepted needs a strict pass (hidden checks up to this phase, the project's
    tests, the lint gate, no contamination or record failure) and every mediated test up to this phase.
    The in-session gate is recorded beside it; an unverified exit is graded, never trusted."""
    verdicts = gate_verdicts(run) if armed and run is not None else []
    last = verdicts[-1].get("status") if verdicts else None
    project = evaluation["project_tests"]
    reasons = []
    if not evaluation["hidden_passed"]:
        reasons.append("hidden checks failed: " + (", ".join(evaluation["missing"]) or "they did not run"))
    if not project["passed"]:
        violations = project.get("integrity_violations") or []
        reasons.append("project tests failed" + (f"; supplied tests changed: {', '.join(violations)}" if violations else ""))
    if not quality_ok:
        reasons.append("lint gate failed")
    if contaminated:
        reasons.append("contaminated: the session reached the grader")
    if record_failures:
        reasons.append("record failures: " + "; ".join(record_failures))
    if not mediated["passed"]:
        reasons.append("mediated tests failed: " + (", ".join(mediated["missing"]) or "they did not run"))
    strict = bool(evaluation["hidden_passed"] and project["passed"] and quality_ok and not contaminated and not record_failures)
    return {"phase": suite.phase, "ending": ending,
            "gate": {"armed": armed, "last": last, "verdicts": len(verdicts), "verified": last == "green"},
            "hidden_passed": evaluation["hidden_passed"], "project_passed": project["passed"],
            "integrity_ok": project.get("integrity_ok", True), "quality_ok": quality_ok,
            "contaminated": "not_checked" if contaminated is None else contaminated,
            "record_failures": record_failures, "mediated": mediated,
            "strict": strict, "accepted": strict and mediated["passed"], "reasons": reasons}


def tree_hashes(tree: Path) -> dict[str, str]:
    """Every file of a checkpoint's tree with its sha256, leaving out the checkpoint's own git store."""
    from harness import file_hashes
    return {rel: digest for rel, digest in file_hashes(tree).items() if not rel.startswith(".git/")}


def accept_saved(workspace: Path, suite, *, trace: Path | None = None, grade_user: str | None = None) -> dict:
    """The boundary verdict for a build with no session: a saved workspace, or a checkpoint's tree.
    Contamination is read from the build's trace when there is one, else recorded `not_checked`."""
    from grading import evaluate
    from harness import grade
    if suite.phase is None:
        raise SystemExit("accepting a saved build needs a phase scope")
    evaluation = evaluate(Path(workspace), suite, grade_user=grade_user)
    quality_ok = all(ok for name, ok, _ in grade(Path(workspace), suite) if name in {"ruff", "complexipy"})
    contaminated = None
    if trace is not None and Path(trace).is_file():
        text = Path(trace).read_text(errors="ignore")
        contaminated = bool((suite.canary and suite.canary in text) or f"suites/{suite.name}" in text)
    mediated = mediated_result(Path(workspace), suite, phase_mediated(suite, suite.phase), grade_user)
    return decide(None, suite, ending="saved", evaluation=evaluation, quality_ok=quality_ok,
                  contaminated=contaminated, record_failures=[], mediated=mediated, armed=False)


def write_checkpoint(workspace: Path, suite, boundary: dict, out: Path) -> dict:
    """An accepted phase's checkpoint: the build with the trusted project config, committed with the
    flow's checkpoint machinery, and a manifest of its files, grader and verdict. Nothing else qualifies."""
    if not boundary.get("accepted"):
        raise SystemExit("only an accepted phase becomes a checkpoint")
    from flow_run import _git, git_checkpoint, git_init_workspace
    from grader_history import grader_identity
    from grading import _application, _base
    out, tree = Path(out), Path(out) / "tree"
    out.mkdir(parents=True)
    # The same copy grading makes: no .git, .venv or caches, and the suite's own pyproject.toml/uv.lock.
    _application(Path(workspace), tree, _base(suite))
    git_init_workspace(tree)
    git_checkpoint(tree, f"{suite.name} phase {suite.phase} accepted")
    manifest = {"suite": suite.name, "phase": suite.phase, "grader": grader_identity(suite),
                "commit": _git(tree, "rev-parse", "HEAD").stdout.strip(), "files": tree_hashes(tree),
                "boundary": boundary}
    (out / "checkpoint.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def verify_checkpoint(path: Path, suite, phase: int, grade_user: str | None = None) -> dict:
    """Refuse, before any session or token, a checkpoint that is not this suite's accepted phase N-1,
    whose files changed, or that today's acceptance of phases 1..N-1 rejects."""
    path = Path(path)
    try:
        manifest = json.loads((path / "checkpoint.json").read_text())
    except (OSError, json.JSONDecodeError):
        raise SystemExit(f"{path} is not a checkpoint: no readable checkpoint.json")
    if manifest.get("suite") != suite.name:
        raise SystemExit(f"checkpoint {path} is for suite {manifest.get('suite')}, not {suite.name}")
    if manifest.get("phase") != phase - 1:
        raise SystemExit(f"checkpoint {path} holds phase {manifest.get('phase')}; phase {phase} starts from phase {phase - 1}")
    if tree_hashes(path / "tree") != manifest.get("files"):
        raise SystemExit(f"checkpoint {path} has changed since it was accepted")
    verdict = accept_saved(path / "tree", phase_scope(suite, phase - 1), grade_user=grade_user)
    if not verdict["accepted"]:
        raise SystemExit(f"checkpoint {path} is no longer accepted at phase {phase - 1}: " + "; ".join(verdict["reasons"]))
    return manifest


def seed(path: Path, workspace: Path) -> None:
    """Start a workspace from a checkpoint's tree, without the checkpoint's git store."""
    shutil.copytree(Path(path) / "tree", workspace, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))
