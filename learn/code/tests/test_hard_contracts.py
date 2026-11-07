"""Real alternate builds exercise the Hard archive, SQL and migration oracle."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

SUITE = Path(__file__).resolve().parents[1] / "suites/hard"
LATER_MODULES = ["test_phase5.py", "test_phase6.py", "test_visits.py", "test_migrations.py"]


def _workspace(path):
    ignored = shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache")
    shutil.copytree(SUITE / "base", path, dirs_exist_ok=True, ignore=ignored)
    shutil.copytree(SUITE / "fixtures/known-good", path, dirs_exist_ok=True, ignore=ignored)
    shutil.copytree(SUITE / "grader", path / "grader_tests", ignore=ignored)
    return path


def _change(path, filename, old, new):
    target = path / filename
    source = target.read_text()
    assert old in source, (filename, old)
    target.write_text(source.replace(old, new))


def _grade(path, selector):
    env = os.environ.copy()
    env.update(PYTHONPATH=str(path), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    env.pop("VIRTUAL_ENV", None)
    result = subprocess.run(
        ["uv", "run", "--frozen", "--project", str(SUITE / "base"), "python", "-m", "pytest",
         "-q", "--noconftest", "-p", "no:cacheprovider", *selector],
        cwd=path, env=env, capture_output=True, text=True, timeout=90,
    )
    output = result.stdout + result.stderr
    assert "ERROR collecting" not in output, output
    return result.returncode, output


CASES = [
    ("blank-archived-at", "app.py", 'where archived_at is not null',
     "where archived_at is not null and archived_at != ''", "test_phase6.py::test_archived_defined_by_archived_at"),
    ("archive-display-reordering", "app.py", 'visible = [c for c in complaints if c.status != "archived"]',
     'visible = [c for c in complaints if c.status != "archived"]\n    if any(c.status == "archived" for c in complaints):\n        visible.reverse()', "test_phase5.py::test_archive_hides_from_board_but_keeps_the_record"),
    ("rejection-audits", "app.py", 'if complaint.status != "resolved":',
     'if complaint.status != "resolved":\n                models.record(complaint_id, "archive")', "test_phase5.py::test_archive_only_when_resolved"),
    ("rejection-mutates-other", "app.py", 'if complaint.status != "resolved":',
     'if complaint.status != "resolved":\n                complaints[0].text += "changed"', "test_phase5.py::test_archive_only_when_resolved"),
    ("repeated-archive", "app.py", 'if complaint.status != "resolved":',
     'if complaint.status == "open":', "test_phase5.py::test_archive_only_when_resolved"),
    ("wrong-location", "app.py", 'models.record(complaint_id, "archive")\n            return RedirectResponse("/complaints", status_code=303)',
     'models.record(complaint_id, "archive")\n            return RedirectResponse("/elsewhere", status_code=303)', "test_phase5.py::test_archive_hides_from_board_but_keeps_the_record"),
    ("archive-mutates-other", "app.py", 'complaint.status = "archived"',
     'complaint.status = "archived"\n            complaints[0].text += "changed"', "test_phase5.py::test_archive_hides_from_board_but_keeps_the_record"),
    ("missing-archive-event", "app.py", 'models.record(complaint_id, "archive")',
     'pass', "test_phase5.py::test_audit_records_each_transition_in_order_with_monotonic_seq"),
    ("wrong-audit-id", "models.py", '"id": complaint_id',
     '"id": "wrong"', "test_phase5.py::test_audit_records_each_transition_in_order_with_monotonic_seq"),
    ("float-seq", "models.py", '"seq": next(_seq)',
     '"seq": float(next(_seq))', "test_phase5.py::test_audit_records_each_transition_in_order_with_monotonic_seq"),
    ("extra-audit-event", "models.py", 'audit.append({"id": complaint_id, "action": action, "seq": next(_seq)})',
     'audit.append({"id": complaint_id, "action": action, "seq": next(_seq)})\n    if action == "reopen":\n        audit.append({"id": complaint_id, "action": "unexpected", "seq": next(_seq)})', "test_phase5.py::test_audit_records_each_transition_in_order_with_monotonic_seq"),
    ("float-ids", "models.py", 'id: int = field(default_factory=lambda: next(_ids))',
     'id: int = field(default_factory=lambda: float(next(_ids)))', "test_phase5.py::test_ids_are_never_reused_after_archive"),
    ("reuse-after-archive", "app.py", 'complaint.status = "archived"',
     'complaint.status = "archived"\n            from itertools import count\n            models._ids = count(1)', "test_phase5.py::test_ids_are_never_reused_after_archive"),
    ("constant-report", "app.py", 'def report():',
     'def report():\n    return {"open_total_cents": 500, "archived_total_cents": 1000, "all_time_total_cents": 2099}\n', "test_phase6.py::test_report_exact_sums"),
    ("bool-report", "app.py", 'def report():',
     'def report():\n    return {"open_total_cents": True, "archived_total_cents": True, "all_time_total_cents": True}\n', "test_phase6.py::test_totals_are_integers"),
    ("python-report-sums", "app.py", 'def report():',
     '''def report():
    with sqlite3.connect("data.db") as connection:
        rows = connection.execute("select status, archived_at, cents from tickets").fetchall()
    return {"open_total_cents": sum(c for s,a,c in rows if s == "open" and a is None),
            "archived_total_cents": sum(c for s,a,c in rows if a is not None),
            "all_time_total_cents": sum(c for s,a,c in rows)}
''', "test_phase6.py::test_report_exact_sums"),
    ("wrong-visits-defaults", "app.py", 'min_minutes: int = 0,\n    limit: int = 10,',
     'min_minutes: int = 100000,\n    limit: int = 0,', "test_visits.py::test_visits_filter_sort_and_limit"),
    ("integer-averages", "app.py", 'float(average)',
     'float(average) if average % 1 else int(average)', "test_visits.py::test_visits_range_is_inclusive_and_minutes_bound"),
    ("string-counts", "app.py", '"count": int(count)',
     '"count": str(count)', "test_visits.py::test_visits_filter_sort_and_limit"),
    ("unbound-filters", "app.py", '"where date >= ? and date <= ? and minutes >= ? group by agent",\n            (from_, to, min_minutes),',
     'f"where date >= \'{from_}\' and date <= \'{to}\' and minutes >= {min_minutes} group by agent",', "test_visits.py::test_visits_range_is_inclusive_and_minutes_bound"),
    ("wrong-index", "migrations.py", 'on tickets(status, archived_at)',
     'on visits(agent)', "test_migrations.py::test_index_exists"),
    ("no-index-migration", "migrations.py", 'create index if not exists idx_tickets_status_archived ',
     'create index if not exists some_other_index ', "test_migrations.py::test_index_exists"),
    ("empty-view", "migrations.py", "where status = 'open' and archived_at is null",
     'where 0', "test_migrations.py::test_open_tickets_view"),
    ("table-for-view", "migrations.py", 'create view if not exists open_tickets as ',
     'create table if not exists open_tickets as ', "test_migrations.py::test_open_tickets_view"),
    ("not-null-note", "migrations.py", 'add column note text',
     "add column note text not null default ''", "test_migrations.py::test_note_column"),
    ("wrong-backfill", "migrations.py", '2026-01-03T00:00:00',
     '2099-01-01T00:00:00', "test_migrations.py::test_resolved_at_is_backfilled"),
    ("backfill-alters-money", "migrations.py", 'update tickets set resolved_at = ? where status',
     'update tickets set cents = cents + 1, resolved_at = ? where status', "test_migrations.py::test_resolved_at_is_backfilled"),
    ("rerun-alters-data", "migrations.py", 'migrations = Migrations("agentclinic")',
     '''migrations = Migrations("agentclinic")

import sqlite3
with sqlite3.connect("data.db") as connection:
    connection.execute("update tickets set cents = cents + 1")
''', "test_migrations.py::test_rerunning_migrations_is_a_noop"),
    ("rerun-alters-schema", "migrations.py", 'migrations = Migrations("agentclinic")',
     '''migrations = Migrations("agentclinic")

import sqlite3
with sqlite3.connect("data.db") as connection:
    n = len(connection.execute("pragma table_info(visits)").fetchall())
    connection.execute(f"alter table visits add column surprise_{n} text")
''', "test_migrations.py::test_rerunning_migrations_is_a_noop"),
]


@pytest.mark.parametrize("name,filename,old,new,check", CASES, ids=[c[0] for c in CASES])
def test_hard_oracle_rejects_contract_violation(tmp_path, name, filename, old, new, check):
    workspace = _workspace(tmp_path)
    _change(workspace, filename, old, new)
    code, output = _grade(workspace, ["grader_tests/" + check])
    assert code == 1 and "failed" in output, f"survived {name}:\n{output}"


@pytest.mark.parametrize("alternate", [False, True, "shared", "state"], ids=["known-good", "valid-alternative", "shared-connection", "app-state-connection"])
def test_hard_later_phases_accept_complete_builds(tmp_path, alternate):
    workspace = _workspace(tmp_path)
    if alternate:
        _change(workspace, "app.py", 'visible = [c for c in complaints if c.status != "archived"]',
                'visible = [c for c in complaints if c.status != "archived"][::-1]')
        _change(workspace, "app.py", 'date >= ? and date <= ? and minutes >= ?',
                'date between :start and :end and minutes >= :minimum')
        _change(workspace, "app.py", '(from_, to, min_minutes),',
                '{"start": from_, "end": to, "minimum": min_minutes},')
        _change(workspace, "app.py", 'import sqlite3',
                'import sqlite3\nfrom sqlite3 import connect as database_connection')
        _change(workspace, "app.py", 'sqlite3.connect("data.db")',
                'database_connection("data.db")')
        _change(workspace, "migrations.py", "on tickets(status, archived_at)",
                'ON tickets([status], [archived_at])')
        _change(workspace, "migrations.py", "select * from tickets where status",
                "select cents, id, archived_at, status, resolved_at from tickets where status")
    if alternate:
        _change(workspace, "app.py", 'templates = Jinja2Templates(directory="templates")',
                'templates = Jinja2Templates(directory="templates")\nfrom itertools import count\nrender_counter = count()\ntemplates.env.globals["render_count"] = lambda: next(render_counter)')
        _change(workspace, "templates/complaints.html", '{% block content %}',
                '{% block content %}<!-- render {{ render_count() }} -->')
    if alternate == "shared":
        _change(workspace, "app.py", 'app = FastAPI()',
                'shared_connection = sqlite3.connect("data.db", check_same_thread=False)\napp = FastAPI()')
        _change(workspace, "app.py", 'con = database_connection("data.db")',
                'con = shared_connection')
        _change(workspace, "app.py", 'con.close()', 'pass')
    if alternate == "state":
        _change(workspace, "app.py", 'app = FastAPI()',
                'app = FastAPI()\napp.state.db = sqlite3.connect("data.db", check_same_thread=False)')
        _change(workspace, "app.py", 'con = database_connection("data.db")',
                'con = app.state.db')
        _change(workspace, "app.py", 'con.close()', 'pass')
    selectors = ["grader_tests/" + module for module in reversed(LATER_MODULES)]
    code, output = _grade(workspace, selectors)
    assert code == 0, output
