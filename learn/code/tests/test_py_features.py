"""py_features: version-aware Python feature tasks, proved before any model run, open to every future release."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import py_features  # noqa: E402
from py_features import check, predecessor, scaffold  # noqa: E402


def test_predecessor_is_derived_for_any_future_minor():
    assert predecessor("3.15") == "3.14"
    assert predecessor("3.16") == "3.15"
    assert predecessor("3.20") == "3.19"


def test_a_major_bump_needs_an_explicit_predecessor():
    with pytest.raises(ValueError):
        predecessor("4.0")
    assert predecessor("4.0", explicit="3.19") == "3.19"


def test_scaffold_pins_the_project_to_the_task_version(tmp_path):
    task = scaffold(tmp_path, "pinned", python="3.16", kind="new-api", pep="PEP 999")
    assert task.name == "py3.16-pinned"
    meta = json.loads((task / "task.json").read_text())
    assert meta == {"python": "3.16", "kind": "new-api", "pep": "PEP 999"}
    assert (task / "base" / ".python-version").read_text().strip() == "3.16"
    assert 'requires-python = "==3.16.*"' in (task / "base" / "pyproject.toml").read_text()
    for part in ("prompts/01.md", "grader", "fixtures/reference", "fixtures/workaround", "layout.json"):
        assert (task / part).exists(), part


def test_a_trap_task_is_pinned_to_the_version_before(tmp_path):
    task = scaffold(tmp_path, "trap", python="3.15", kind="trap", pep="PEP 999")
    assert task.name == "py3.14-trap-of-3.15"
    assert (task / "base" / ".python-version").read_text().strip() == "3.14"


def make_tstring_task(root):
    """A real 3.14 task: render a t-string; a 3.13 project can't even parse the reference."""
    task = scaffold(root, "tstring", python="3.14", kind="new-api", pep="PEP 750")
    (task / "base" / "render.py").write_text("def render(template):\n    raise NotImplementedError\n")
    (task / "grader" / "test_render.py").write_text(
        "from render import render\n\n"
        "def test_upper_interpolations():\n    name = 'ada'\n    assert render(t'hi {name}') == 'hi ADA'\n")
    (task / "fixtures" / "reference" / "render.py").write_text(
        "from string.templatelib import Interpolation\n\n"
        "def render(template):\n"
        "    return ''.join(p.value.upper() if isinstance(p, Interpolation) else p for p in template)\n")
    (task / "fixtures" / "workaround" / "render.py").write_text(
        "def render(template):\n    return str(template).upper()\n")
    (task / "expected.json").write_text(json.dumps(["grader_tests/test_render.py::test_upper_interpolations"]))
    return task


def test_check_proves_a_task_in_every_direction(tmp_path):
    verdict = check(make_tstring_task(tmp_path))
    assert verdict["reference_on_target"] == "green"
    assert verdict["reference_on_predecessor"] == "red"
    assert verdict["workaround_on_target"] == "red"
    assert verdict["base_on_target"] == "red"
    assert verdict["ok"] is True


def test_check_fails_a_task_whose_workaround_passes(tmp_path):
    task = make_tstring_task(tmp_path)
    (task / "fixtures" / "workaround" / "render.py").write_text(
        (task / "fixtures" / "reference" / "render.py").read_text())
    verdict = check(task)
    assert verdict["workaround_on_target"] == "green" and verdict["ok"] is False


def test_discover_finds_every_task_of_every_version(tmp_path):
    for py in ("3.14", "3.15", "3.16"):
        scaffold(tmp_path, "x", python=py, kind="new-api", pep="PEP 1")
    assert [t.name for t in py_features.discover(tmp_path)] == ["py3.14-x", "py3.15-x", "py3.16-x"]


TRAIN = Path(py_features.__file__).resolve().parent / "suites" / "py-features-train"


def test_training_tasks_are_kept_apart_from_the_eval():
    # the eval stays held out: no training task shares a name, a prompt or a grader with an eval task
    evals, trains = py_features.discover(), py_features.discover(TRAIN)
    assert trains, "no training tasks"
    assert not {t.name for t in evals} & {t.name for t in trains}
    texts = lambda tasks, part: {p.read_text() for t in tasks for p in (t / part).glob("*")}  # noqa: E731
    for part in ("prompts", "grader"):
        assert not texts(evals, part) & texts(trains, part), part


def test_main_checks_another_root(tmp_path, capsys):
    task = scaffold(tmp_path, "empty", python="3.14", kind="new-api", pep="PEP 999")
    with pytest.raises(SystemExit) as done:
        sys.argv = ["py_features.py", "check", "--root", str(tmp_path), task.name]
        py_features.main()
    assert done.value.code == 1 and "FAIL  py3.14-empty" in capsys.readouterr().out
