"""Independent-review witnesses: false passes, valid alternatives and provenance."""
import inspect
import json
from pathlib import Path
import sys

import pytest
from test_easy_contracts import workspace as easy_workspace, change, grade_check
from test_shared_suite_contracts import _workspace, _replace, _grade
from test_hard_contracts import _workspace as hard_workspace, _grade as hard_grade
from test_grading import case

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grading
import harness
import scoreboard


def test_title_override_can_replace_the_entire_title_element(tmp_path):
    app = easy_workspace(tmp_path)
    change(app, 'templates/base.html', '<title>{% block title %}AgentClinic{% endblock %}</title>',
           '{% block browser_caption %}<title>AgentClinic</title>{% endblock %}')
    passed, tail, _, _ = grade_check(app, 'test_extending_page_can_override_layout_title')
    assert passed, tail


def test_hidden_descendants_do_not_supply_visible_welcome(tmp_path):
    app = easy_workspace(tmp_path)
    change(app, 'templates/home.html', '<p class="lead">Welcome', '<p class="lead"><span hidden>Welcome')
    change(app, 'templates/home.html', 'get their gripes off their chests.</p>', 'get their gripes off their chests.</span></p>')
    assert not grade_check(app, 'test_home_has_hero_and_welcoming_paragraph')[0]


@pytest.mark.parametrize('suite', ['medium', 'hard'])
@pytest.mark.parametrize('control', ['input', 'textarea'])
def test_required_complaint_fields_must_be_editable(tmp_path, suite, control):
    app = _workspace(tmp_path, suite)
    _replace(app, 'templates/complaints.html', f'<{control} ', f'<{control} readonly ')
    result = _grade(app, 'test_phase3_add.py::test_complaints_board_renders_add_complaint_form')
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize('suite', ['medium', 'hard'])
def test_status_label_cannot_negate_the_expected_state(tmp_path, suite):
    app = _workspace(tmp_path, suite)
    for state in ('Open', 'Resolved'):
        _replace(app, 'templates/complaints.html', f'>{state}</span>', f'>Not {state}</span>')
    result = _grade(app, 'test_phase4_resolve_reopen.py::test_resolve_route_marks_complaint_resolved_and_redirects')
    assert result.returncode == 1, result.stdout + result.stderr


def test_parameterized_date_objects_are_valid_sql_bindings(tmp_path):
    app = hard_workspace(tmp_path)
    _replace(app, 'app.py', 'import sqlite3', 'import sqlite3\nfrom datetime import date')
    _replace(app, 'app.py', 'from_: str = Query(..., alias="from"),\n    to: str = Query(...),',
             'from_: date = Query(..., alias="from"),\n    to: date = Query(...),')
    code, output = hard_grade(app, ['grader_tests/test_visits.py'])
    assert code == 0, output


def test_exact_database_computation_does_not_require_named_sum_function(tmp_path):
    app = hard_workspace(tmp_path)
    source = (app / 'app.py').read_text()
    begin = source.index('    con = sqlite3.connect("data.db")', source.index('def report():'))
    end = source.index('\n\n@app.get("/visits")', begin)
    body = '''    with sqlite3.connect("data.db") as connection:
        def total(predicate):
            query = """WITH RECURSIVE applicable AS (SELECT id, cents FROM tickets WHERE """ + predicate + """),
              accumulation(id, cents) AS (
                SELECT MIN(id), 0 FROM applicable
                UNION ALL
                SELECT (SELECT MIN(id) FROM applicable WHERE id > accumulation.id),
                       accumulation.cents + (SELECT cents FROM applicable WHERE id = accumulation.id)
                  FROM accumulation WHERE id IS NOT NULL
              )
              SELECT cents FROM accumulation WHERE id IS NULL"""
            return connection.execute(query).fetchone()[0]
        return {"open_total_cents": total("archived_at IS NULL AND status = 'open'"),
                "archived_total_cents": total("archived_at IS NOT NULL"),
                "all_time_total_cents": total("1")}
'''
    (app / 'app.py').write_text(source[:begin] + body + source[end:])
    code, output = hard_grade(app, ['grader_tests/test_phase6.py'])
    assert code == 0, output


@pytest.mark.parametrize('hook', ['ignore', 'deselect', 'noop', 'callhook', 'late'])
def test_project_hooks_cannot_hide_failing_added_tests(tmp_path, hook):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (app / 'tests').mkdir()
    (app / 'tests/test_added.py').write_text('def test_added():\n    assert False\n')
    (app / 'tests/test_ok.py').write_text('def test_ok():\n    assert True\n')
    text = {
        'ignore': 'collect_ignore = ["tests/test_added.py"]\n',
        'deselect': 'def pytest_collection_modifyitems(items):\n    items[:] = [i for i in items if i.name != "test_added"]\n',
        'noop': 'def pytest_collection_modifyitems(items):\n    for item in items:\n        item.runtest = lambda: None\n',
        'callhook': 'def pytest_pyfunc_call(pyfuncitem):\n    return True\n',
        'late': 'import pytest\n@pytest.hookimpl(trylast=True)\ndef pytest_collection_finish(session):\n    for item in session.items:\n        item.runtest = lambda: None\n',
    }[hook]
    (app / 'conftest.py').write_text(text)
    result = grading.evaluate(app, suite)
    assert result['hidden_passed']
    assert not result['passed']


def test_project_fixture_parameterization_remains_supported(tmp_path):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (app / 'tests').mkdir()
    (app / 'conftest.py').write_text('def pytest_generate_tests(metafunc):\n    if "value" in metafunc.fixturenames:\n        metafunc.parametrize("value", [2, 4], ids=["two", "four"])\n')
    (app / 'tests/test_added.py').write_text('def test_added(value):\n    assert value % 2 == 0\n')
    assert grading.evaluate(app, suite)['passed']


def test_original_integrity_uses_the_trusted_prepared_brief_baseline(tmp_path):
    suite, app = case(tmp_path)
    (app / 'answer.py').write_text('answer = 42\n')
    (suite.root / 'base/tests').mkdir()
    (suite.root / 'base/tests/test_required.py').write_text('def test_required():\n    assert True\n')
    variant = suite.root / 'spec-variants/original'
    (variant / 'prompts').mkdir(parents=True)
    (variant / 'prompts/01.md').write_text('Implement the original brief.\n')
    (variant / 'delete.json').write_text(json.dumps(['tests/test_required.py']))
    (app / 'tests').mkdir()
    (app / 'tests/test_own.py').write_text('def test_own():\n    assert True\n')
    kwargs = {'variant': 'original'} if 'variant' in inspect.signature(grading.evaluate).parameters else {}
    result = grading.evaluate(app, suite, **kwargs)
    assert result['passed'], result['tail']
    assert not grading.evaluate(app, suite)['passed'], 'without the trusted variant, a deletion still fails'
    (suite.root / 'base/answer.py').write_text('answer = 42\n')
    (variant / 'tests').mkdir()
    (variant / 'tests/test_own.py').write_text('def test_own():\n    assert True\n')
    run = harness.run_suite(suite, runs_dir=tmp_path / 'runs', profile=harness.PROFILE,
                           pi_binary=str(harness.CODE / 'tests/fixtures/fake-pi.sh'), specs='original')
    passed, tail, _, _ = harness.score_details(run, suite)
    assert passed, tail


def test_scoreboard_retains_and_separates_assertion_identity(tmp_path):
    entries = []
    for index, revision in enumerate(('current', 'bc5db20', None)):
        run = tmp_path / str(index)
        run.mkdir()
        identity = {'revision': revision, 'assertion_digest': f'digest-{index}', 'execution_policy': 'trusted-copy-v1'} if revision else None
        (run / 'run.json').write_text(json.dumps({'suite': 'easy', 'model': 'same', 'arm': 'vanilla',
            'passed': True, 'turns': 1, 'wall': 1, 'grader': identity}))
        entry = scoreboard.entry_from_run(run)
        assert entry.get('grader') == identity
        entries.append(entry)
    assert len(scoreboard.leaderboard(entries)) == 3
    assert len(scoreboard._record_rows(entries)) == 3
    page = scoreboard.render_page(entries)
    assert 'unknown' in page.casefold() and 'bc5db20' in page
    # Identical assertion inputs still aggregate; no old record is relabeled.
    assert len(scoreboard.leaderboard([entries[0], dict(entries[0], id='another')])) == 1
