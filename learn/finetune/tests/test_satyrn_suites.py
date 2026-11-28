"""satyrn_suites: turn a satyrn-evals task into a harness suite (base, prompt, grader, expected, layout)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from satyrn_suites import convert_task  # noqa: E402


def make_task(root: Path, overlay: bool) -> Path:
    task = root / "demo-task"
    (task / "base" / "tools").mkdir(parents=True)
    (task / "base" / "pyproject.toml").write_text("[project]\nname='x'\n")
    (task / "base" / "tools" / "__init__.py").write_text("")
    manifest = {
        "name": "demo-task",
        "contract": "Task: build tools/thing.py\n\nStep 1: Failing tests",
        "expected_test_ids": ["test_thing.py::test_a", "test_thing.py::test_b"],
        "source_paths": ["tools/thing.py", "tests"],
    }
    if overlay:
        (task / "overlay").mkdir()
        (task / "overlay" / "test_thing.py").write_text("def test_a(): pass\ndef test_b(): pass\n")
        manifest["grader_overlay"] = "overlay"
    else:
        (task / "base" / "test_thing.py").write_text("def test_a(): pass\ndef test_b(): pass\n")
    (task / "manifest.json").write_text(json.dumps(manifest))
    return task


def test_overlay_task_becomes_a_suite(tmp_path):
    suite = convert_task(make_task(tmp_path, overlay=True), tmp_path / "out")
    assert suite.name == "satyrn-demo-task"
    assert (suite / "base" / "tools" / "__init__.py").is_file()
    assert (suite / "prompts" / "01.md").read_text().startswith("Task: build tools/thing.py")
    assert (suite / "grader" / "test_thing.py").is_file()
    assert json.loads((suite / "expected.json").read_text()) == [
        "grader_tests/test_thing.py::test_a", "grader_tests/test_thing.py::test_b"]
    layout = json.loads((suite / "layout.json").read_text())
    assert layout["allow"] == ["tools/thing.py", "tests/**"]


def test_hidden_oracle_never_reaches_the_workspace(tmp_path):
    suite = convert_task(make_task(tmp_path, overlay=True), tmp_path / "out")
    assert not list((suite / "base").rglob("test_thing.py"))


def test_visible_test_task_grades_from_its_base_copy(tmp_path):
    suite = convert_task(make_task(tmp_path, overlay=False), tmp_path / "out")
    assert (suite / "grader" / "test_thing.py").is_file()
    assert (suite / "base" / "test_thing.py").is_file()  # visible by design in the source task


def test_passed_ids_keep_parametrised_names_with_spaces():
    from satyrn_suites import passed_ids
    out = "PASSED grader_tests/t.py::test_x[git commit -m 'x']\nFAILED grader_tests/t.py::test_y[a b]\n"
    expected = {"grader_tests/t.py::test_x[git commit -m 'x']", "grader_tests/t.py::test_y[a b]"}
    assert passed_ids(out, expected) == {"grader_tests/t.py::test_x[git commit -m 'x']"}
