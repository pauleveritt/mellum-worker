"""The submitted project's pytest/dependency policy cannot set its hidden grade."""
from dataclasses import replace
import importlib
from pathlib import Path
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness


def case(tmp_path, hidden='from answer import answer\ndef test_answer():\n    assert answer == 42\n'):
    root = tmp_path / 'suite'
    (root / 'grader').mkdir(parents=True)
    (root / 'grader/test_answer.py').write_text(hidden)
    (root / 'base').mkdir()
    app = tmp_path / 'submission'
    app.mkdir()
    (app / 'answer.py').write_text('answer = 0\n')
    suite = harness.Suite('generic', ['Implement it'], root / 'grader', None,
                          ('grader_tests/test_answer.py::test_answer',), root=root)
    return suite, app


def evaluate(app, suite):
    assert (harness.CODE / 'grading.py').exists(), 'trusted runner is missing'
    return importlib.import_module('grading').evaluate(app, suite)


def test_workspace_conftest_cannot_replace_hidden_checks(tmp_path):
    suite, app = case(tmp_path)
    (app / 'conftest.py').write_text('def pytest_collection_modifyitems(items):\n    for item in items:\n        item.runtest = lambda: None\n')
    assert not harness.score_workspace(app, suite)[0]


def test_workspace_metadata_and_pytest_options_cannot_deselect_hidden(tmp_path, monkeypatch):
    suite, app = case(tmp_path)
    (app / 'pyproject.toml').write_text('deliberately invalid metadata')
    (app / 'uv.lock').write_text('deliberately invalid lock')
    (app / 'pytest.ini').write_text('[pytest]\naddopts = --deselect=grader_tests/test_answer.py::test_answer\n')
    monkeypatch.setenv('PYTEST_ADDOPTS', '--deselect=grader_tests/test_answer.py::test_answer')
    passed, tail, missing, ran = harness.score_workspace_details(app, suite)
    assert not passed
    assert ran, tail
    assert missing == list(suite.expected)


def test_forged_stdout_does_not_make_skipped_check_pass(tmp_path):
    suite, app = case(tmp_path, 'import pytest\ndef test_answer():\n    print("PASSED grader_tests/test_answer.py::test_answer")\n    pytest.skip("not executed")\n')
    passed, _, missing, _ = harness.score_workspace_details(app, suite)
    assert not passed
    assert missing == list(suite.expected)


def test_hidden_tests_never_enter_submission_and_mutations_are_disposable(tmp_path):
    suite, app = case(tmp_path, 'from pathlib import Path\ndef test_answer():\n    Path("answer.py").write_text("changed")\n')
    before = harness.file_hashes(app)
    assert harness.score_workspace(app, suite)[0]
    assert harness.file_hashes(app) == before
    assert not (app / 'grader_tests').exists()


def test_checks_each_start_with_pristine_state(tmp_path):
    suite, app = case(tmp_path, 'from pathlib import Path\ndef test_answer():\n    Path("state").write_text("dirty")\ndef test_clean():\n    assert not Path("state").exists()\n')
    suite = replace(suite, expected=(*suite.expected, 'grader_tests/test_answer.py::test_clean'))
    assert harness.score_workspace(app, suite)[0]


def test_added_failing_project_test_fails_overall_but_hidden_passes(tmp_path):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (app / 'tests').mkdir()
    (app / 'tests/test_added.py').write_text('def test_added():\n    assert False\n')
    result = evaluate(app, suite)
    assert result['hidden_passed']
    assert not result['project_tests']['passed']
    assert not result['passed']
    assert not harness.score_workspace(app, suite)[0]


def test_project_conftest_works_with_trusted_config(tmp_path):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (app / 'tests').mkdir()
    (app / 'tests/conftest.py').write_text('import pytest\n@pytest.fixture\ndef value():\n    return 7\n')
    (app / 'tests/test_added.py').write_text('def test_added(value):\n    assert value == 7\n')
    result = evaluate(app, suite)
    assert result['passed'], result['tail']
    assert result['project_tests']['passed']


@pytest.mark.parametrize('change', ['delete', 'weaken'])
def test_required_starter_tests_cannot_disappear_or_change(tmp_path, change):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (suite.root / 'base/tests').mkdir()
    required = suite.root / 'base/tests/test_required.py'
    required.write_text('def test_required():\n    assert False\n')
    if change == 'weaken':
        (app / 'tests').mkdir()
        (app / 'tests/test_required.py').write_text('def test_required():\n    pass\n')
    result = evaluate(app, suite)
    assert result['hidden_passed']
    assert not result['project_tests']['integrity_ok']
    assert not result['passed']


def test_layout_reports_deleted_paths(tmp_path):
    (tmp_path / 'required.txt').write_text('original')
    before = harness.file_hashes(tmp_path)
    (tmp_path / 'required.txt').unlink()
    result = harness.layout_report(tmp_path, before, {'allow': []})
    assert result['deleted'] == ['required.txt']
    assert result['out_of_layout'] == ['required.txt']


def test_forged_stdout_cannot_satisfy_an_uncollected_expected_check(tmp_path):
    suite, app = case(tmp_path, 'def test_answer():\n    print("PASSED grader_tests/test_answer.py::test_missing")\n')
    suite = replace(suite, expected=(*suite.expected, 'grader_tests/test_answer.py::test_missing'))
    passed, _, missing, _ = harness.score_workspace_details(app, suite)
    assert not passed
    assert missing == ['grader_tests/test_answer.py::test_missing']


def test_workspace_hooks_cannot_weaken_unchanged_required_tests(tmp_path):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (suite.root / 'base/tests').mkdir()
    (app / 'tests').mkdir()
    text = 'def test_required():\n    assert False\n'
    (suite.root / 'base/tests/test_required.py').write_text(text)
    (app / 'tests/test_required.py').write_text(text)
    (app / 'conftest.py').write_text('def pytest_collection_modifyitems(items):\n    for item in items:\n        item.runtest = lambda: None\n')
    result = evaluate(app, suite)
    assert result['project_tests']['integrity_ok']
    assert not result['passed']


def test_optional_quality_ignores_submission_policy_and_keeps_source_unchanged(tmp_path):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = missing_name\n')
    (app / 'pyproject.toml').write_text('[tool.ruff.lint.per-file-ignores]\n"*.py" = ["F821"]\n')
    before = harness.file_hashes(app)
    results = {name: ok for name, ok, _ in harness.grade(app)}
    assert not results['ruff']
    assert harness.file_hashes(app) == before


def _grading():
    return importlib.import_module('grading')


def test_a_grading_user_gets_its_own_copy_of_the_worker_and_no_secrets(tmp_path, monkeypatch):
    grading = _grading()
    monkeypatch.setenv('RUNPOD_API_KEY', 'not-for-the-submission')
    base = tmp_path / 'base'
    base.mkdir()
    (base / 'pyproject.toml').write_text('[project]\nname = "x"\nversion = "0"\n')
    trusted = tmp_path / 'trusted'
    trusted.mkdir()
    command, env = grading._command(trusted, base)
    command, env = grading.as_grade_user(command, env, trusted, user='mellum-grade', home='/home/mellum-grade')
    assert 'RUNPOD_API_KEY' not in env
    assert env['HOME'] == '/home/mellum-grade' and env['USER'] == 'mellum-grade'
    assert env['UV_PROJECT_ENVIRONMENT'].startswith('/home/mellum-grade/')
    assert env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
    assert command[-1] == str(trusted / 'grading_worker.py') and Path(command[-1]).is_file()


class _Finished:
    pid, returncode = 4242, 0

    def communicate(self, timeout=None):
        return '', ''

    def poll(self):
        return 0


def test_a_grading_user_owns_the_copies_and_runs_the_submission(tmp_path, monkeypatch):
    grading = _grading()
    started, owned, opened = {}, [], []
    monkeypatch.setattr(harness, 'start_child', lambda argv, **kwargs: started.update(kwargs) or _Finished())
    monkeypatch.setattr(harness, 'sweep_group', lambda pid: None)
    monkeypatch.setattr(harness, 'drop_privileges', lambda user: {'user': user})
    monkeypatch.setattr(harness, 'chown_tree', lambda path, user: owned.append((path, user)))
    monkeypatch.setattr(grading, '_own_directory', lambda path, user: opened.append((path, user)))
    app, trusted = tmp_path / 'app', tmp_path / 'trusted'
    grading._run(['x'], {}, 'collect', app, trusted, tmp_path / 'out.json', user='mellum-grade')
    assert started['user'] == 'mellum-grade'
    assert (app, 'mellum-grade') in owned and (trusted, 'mellum-grade') in owned
    assert opened == [(tmp_path, 'mellum-grade')], 'the worker must be able to write its result'


def test_grading_runs_as_the_harness_itself_without_a_grading_user(tmp_path, monkeypatch):
    grading = _grading()
    started = {}
    monkeypatch.setattr(harness, 'start_child', lambda argv, **kwargs: started.update(kwargs) or _Finished())
    monkeypatch.setattr(harness, 'sweep_group', lambda pid: None)
    grading._run(['x'], {}, 'collect', tmp_path / 'app', tmp_path / 'trusted', tmp_path / 'out.json')
    assert 'user' not in started


def test_a_grading_user_needs_a_run_as_root(capsys):
    with pytest.raises(SystemExit):
        harness.main(['run', '--suite', 'easy', '--grade-user', 'mellum-grade'])
    assert '--grade-user needs a run as root' in capsys.readouterr().err
