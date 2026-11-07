"""The nine ladder rungs: fixture, user sentence, test command, and pass check."""

from __future__ import annotations

import ast
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
PYTEST = ["uv", "run", "--offline", "pytest", "-q"]
COMMAND_TIMEOUT = 300
IGNORED = shutil.ignore_patterns(
    ".venv", "__pycache__", ".pytest_cache", "node_modules"
)


def copy_fixture(fixture: str, dest: Path) -> Path:
    """Copy a fixture to ``dest`` without any environment or cache directories."""
    shutil.copytree(FIXTURES / fixture, dest, ignore=IGNORED)
    return dest


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    tests_unchanged: bool
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Rung:
    number: int
    fixture: str
    sentence: str
    test_cmd: list[str]
    check: Callable[[Path, Path], CheckResult]


def _same(ws: Path, base: Path, name: str) -> bool:
    """Byte-identical to the baseline; a missing or renamed file counts as changed."""
    try:
        return (ws / name).read_bytes() == (base / name).read_bytes()
    except FileNotFoundError:
        return False


def _run(cmd: list[str], ws: Path) -> subprocess.CompletedProcess | None:
    """Run a check command; a hang past COMMAND_TIMEOUT is reported as no result."""
    try:
        return subprocess.run(
            cmd,
            cwd=ws,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None


def _tests_pass(cmd: list[str], ws: Path) -> bool:
    proc = _run(cmd, ws)
    return proc is not None and proc.returncode == 0


def _collect(ws: Path) -> set[str]:
    proc = _run(["uv", "run", "--offline", "pytest", "--collect-only", "-q"], ws)
    out = proc.stdout if proc is not None else ""
    return {line.strip() for line in out.splitlines() if "::" in line}


def check_calculator(ws: Path, base: Path) -> CheckResult:
    unchanged = _same(ws, base, "calculator.test.js")
    passed = _tests_pass(["node", "--test", "calculator.test.js"], ws)
    return CheckResult(passed and unchanged, unchanged)


def check_ledger(ws: Path, base: Path) -> CheckResult:
    base_ids, ws_ids = _collect(base), _collect(ws)
    kept = base_ids <= ws_ids
    new = any("balance" in i for i in ws_ids - base_ids)
    passed = _tests_pass(PYTEST, ws) and kept and new
    return CheckResult(passed, kept, {"new_tests": sorted(ws_ids - base_ids)})


def check_rename(ws: Path, base: Path) -> CheckResult:
    unchanged = _same(ws, base, "test_report.py")
    leftover = any(
        "fetch_rows" in p.read_text()
        for p in ws.glob("*.py")
        if p.name != "test_report.py"
    )
    both = not _same(ws, base, "rows.py") and not _same(ws, base, "report.py")
    passed = _tests_pass(PYTEST, ws) and unchanged and not leftover and both
    return CheckResult(passed, unchanged, {"leftover": leftover, "both_changed": both})


def check_feature(ws: Path, base: Path) -> CheckResult:
    unchanged = _same(ws, base, "test_export.py")
    changed = sum(
        not _same(ws, base, n) for n in ("export.py", "totals.py", "render.py")
    )
    passed = _tests_pass(PYTEST, ws) and unchanged and changed >= 2
    return CheckResult(passed, unchanged, {"source_files_changed": changed})


def check_edge(ws: Path, base: Path) -> CheckResult:
    unchanged = _same(ws, base, "test_export.py")
    decoy = _same(ws, base, "exports_legacy.py")
    passed = _tests_pass(PYTEST, ws) and unchanged and decoy
    return CheckResult(passed, unchanged, {"decoy_untouched": decoy})


AGENTCLINIC_FACTS_CMD = [
    "uv",
    "run",
    "--offline",
    "python",
    "-m",
    "pytest",
    "tests",
    "-q",
]
AGENTCLINIC_ALLOWED = ("app.py", "models.py", "templates/", "tests/")
HIDDEN_DIR = FIXTURES / "agentclinic-hidden"
_NOT_TEST_DIRS = {"__pycache__", ".pytest_cache"}


GIT_STATUS_FAILED = "<git status failed>"


def outside_write_list(ws: Path, allowed: tuple[str, ...]) -> list[str]:
    """Paths git reports as new, modified or deleted that the write-list does not cover.

    An entry ending in ``/`` allows everything beneath that directory; any other
    entry allows exactly that file. Ignored paths (``.venv/``) never show up
    because git honours the workspace's ``.gitignore``.

    Fails closed: when ``git status`` cannot run, fails or times out (for example
    the worker removed ``.git``), the result is ``[GIT_STATUS_FAILED]``, so the
    rung cannot pass and the record says why.
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "-z",
                "--untracked-files=all",
                "--no-renames",
            ],
            cwd=ws,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except OSError, subprocess.TimeoutExpired:
        return [GIT_STATUS_FAILED]
    if proc.returncode != 0:
        return [GIT_STATUS_FAILED]
    paths = [entry[3:] for entry in proc.stdout.split("\0") if len(entry) > 3]
    return sorted(
        path
        for path in paths
        if not any(
            path.startswith(entry) if entry.endswith("/") else path == entry
            for entry in allowed
        )
    )


def _test_segments(path: Path) -> dict[str, tuple[str | None, ...]] | None:
    """Qualified name -> source segment (decorators included) of each pytest-collected test.

    Collected means module-level ``test*`` functions (``def`` or ``async def``)
    and ``test*`` methods of module-level ``Test*`` classes, named ``func`` and
    ``Class.method``. ``None`` when the file is missing or does not parse.
    """
    try:
        source = path.read_bytes().decode()
        tree = ast.parse(source)
    except OSError, SyntaxError, ValueError:
        return None

    def segment(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str | None, ...]:
        return tuple(
            ast.get_source_segment(source, part)
            for part in (*node.decorator_list, node)
        )

    funcs = (ast.FunctionDef, ast.AsyncFunctionDef)
    found: dict[str, tuple[str | None, ...]] = {}
    for node in tree.body:
        if isinstance(node, funcs) and node.name.startswith("test"):
            found[node.name] = segment(node)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for member in node.body:
                if isinstance(member, funcs) and member.name.startswith("test"):
                    found[f"{node.name}.{member.name}"] = segment(member)
    return found


def existing_tests_kept(ws: Path, base: Path) -> bool:
    """No existing test is removed or edited; additions are allowed (rungs 6-9, rule 3).

    For every ``tests/**/*.py`` in the starting fixture ``base``: the file still
    exists in ``ws`` and parses, and each pytest-collected test it held is still
    there under the same qualified name with a byte-identical source segment.
    New tests, in old or new files, are allowed; non-``.py`` files do not count.
    """
    for path in sorted((base / "tests").rglob("*.py")):
        if _NOT_TEST_DIRS & set(path.parts):
            continue
        name = path.relative_to(base)
        start = _test_segments(path)
        if start is None:
            if not _same(ws, base, str(name)):
                return False
            continue
        now = _test_segments(ws / name)
        if now is None or any(now.get(test) != code for test, code in start.items()):
            return False
    return True


def check_agentclinic(phase: int) -> Callable[[Path, Path], CheckResult]:
    """Score an AgentClinic rung: facts command, hidden tests of phases 1..phase, existing tests kept (additions allowed), write-list kept."""

    def check(ws: Path, base: Path) -> CheckResult:
        # Before anything is copied in: the write-list and any hidden-file collision.
        outside = outside_write_list(ws, AGENTCLINIC_ALLOWED)
        hidden = [f"_hidden_p{k}.py" for k in range(1, phase + 1)]
        collision = sorted(name for name in hidden if (ws / name).exists())
        for name in hidden:
            shutil.copy(HIDDEN_DIR / name, ws / name)
        facts_pass = _tests_pass(AGENTCLINIC_FACTS_CMD, ws)
        hidden_pass = _tests_pass(
            ["uv", "run", "--offline", "python", "-m", "pytest", *hidden, "-q"], ws
        )
        unchanged = existing_tests_kept(ws, base)
        return CheckResult(
            facts_pass and hidden_pass and unchanged and not outside,
            unchanged,
            {
                "facts_cmd_pass": facts_pass,
                "hidden_pass": hidden_pass,
                "outside_write_list": outside,
                "hidden_collision": collision,
            },
        )

    return check


RUNGS: dict[int, Rung] = {
    1: Rung(
        1,
        "calculator",
        "the cart total ignores quantity, fix it",
        ["node", "--test", "calculator.test.js"],
        check_calculator,
    ),
    2: Rung(
        2,
        "ledger",
        "add a balance() that sums the entries, with a test",
        PYTEST,
        check_ledger,
    ),
    3: Rung(
        3, "rename", "rename fetch_rows to load_rows everywhere", PYTEST, check_rename
    ),
    4: Rung(4, "feature", "make the failing test pass", PYTEST, check_feature),
    5: Rung(5, "edge", "the export is missing the totals row", PYTEST, check_edge),
    **{
        5 + phase: Rung(
            5 + phase,
            f"agentclinic-p{phase}",
            f"Implement specs/{spec}.md",
            AGENTCLINIC_FACTS_CMD,
            check_agentclinic(phase),
        )
        for phase, spec in enumerate(
            (
                "phase-1-home",
                "phase-2-board",
                "phase-3-add",
                "phase-4-resolve-reopen",
                "phase-5-archive",
                "phase-6-report",
                "phase-7-sum",
            ),
            start=1,
        )
    },
}
