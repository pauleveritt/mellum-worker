"""Phase 6 — Database report: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

ROOT = Path.cwd()
SCHEMA = """
CREATE TABLE tickets (id INTEGER PRIMARY KEY, status TEXT NOT NULL, archived_at TEXT, cents INTEGER NOT NULL);
CREATE TABLE visits (id INTEGER PRIMARY KEY, agent TEXT NOT NULL, date TEXT NOT NULL, minutes INTEGER NOT NULL, ticket_id INTEGER);
"""
ARCHIVED_AT = "2026-01-05T00:00:00"
TICKETS = [(1, "open", None, 1000), (2, "open", None, 250), (3, "open", ARCHIVED_AT, 4000),
           (4, "resolved", ARCHIVED_AT, 20000), (5, "resolved", None, 100000), (6, "archived", None, 700000)]
# Runs in a copy of the project and records every SQL statement the app sends, then each response.
DRIVER = r"""
import json, sqlite3, sys
real, seen = sqlite3.connect, []
class Cursor(sqlite3.Cursor):
    def execute(self, sql, *a): seen.append(sql); return super().execute(sql, *a)
    def executemany(self, sql, *a): seen.append(sql); return super().executemany(sql, *a)
class Connection(sqlite3.Connection):
    def cursor(self, factory=Cursor): return super().cursor(factory)
    def execute(self, sql, *a): seen.append(sql); return super().execute(sql, *a)
    def executemany(self, sql, *a): seen.append(sql); return super().executemany(sql, *a)
def connect(*a, **k):
    k.setdefault("factory", Connection)
    return real(*a, **k)
sqlite3.connect = connect
from starlette.testclient import TestClient
from app import app
out = []
with TestClient(app, raise_server_exceptions=False) as client:
    for url in json.loads(sys.argv[2]):
        del seen[:]
        r = client.get(url)
        out.append({"status": r.status_code, "text": r.text, "sql": list(seen)})
json.dump(out, open(sys.argv[1], "w"))
"""


def _env(project: Path) -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | {"PYTHONPATH": str(project)}


def _project(target: Path, tickets: list) -> Path:
    """A copy of the project on a fresh database holding these tickets, with its migrations applied."""
    project = shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(
        ".venv", ".git", "__pycache__", ".pytest_cache"))
    path = project / "data.db"
    path.unlink()
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?)", tickets)
        db.commit()
    if (project / "migrations.py").exists():
        result = subprocess.run([sys.executable, "-m", "sqlite_utils", "migrate", "data.db"], cwd=project,
                                env=_env(project), capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, f"sqlite-utils migrate failed:\n{result.stdout}{result.stderr}"
    return project


def _get(project: Path, urls: list[str]) -> list[dict]:
    out = project.parent / "out.json"
    result = subprocess.run([sys.executable, "-c", DRIVER, str(out), json.dumps(urls)], cwd=project,
                            env=_env(project), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"the app did not run:\n{result.stdout[-800:]}{result.stderr[-1200:]}"
    return json.loads(out.read_text())


def _report(tmp_path: Path, tickets: list) -> dict:
    response = _get(_project(tmp_path / "project", tickets), ["/report"])[0]
    assert response["status"] == 200, f"GET /report answered {response['status']}: {response['text'][:500]}"
    return json.loads(response["text"])


@pytest.fixture(scope="module")
def main_report(tmp_path_factory) -> dict:
    return _report(tmp_path_factory.mktemp("report"), TICKETS)


def test_open_total_covers_open_rows_with_no_archived_at(main_report):
    assert main_report["open_total_cents"] == 1250


def test_archived_total_covers_every_row_with_archived_at_whatever_its_status(main_report):
    assert main_report["archived_total_cents"] == 24000


def test_all_time_total_covers_every_row(main_report):
    assert main_report["all_time_total_cents"] == 825250


@pytest.mark.parametrize("key", ["open_total_cents", "archived_total_cents", "all_time_total_cents"])
def test_each_sum_is_an_integer_never_a_float(main_report, key):
    assert type(main_report[key]) is int, f"{key} is {main_report[key]!r}"


def test_a_status_open_row_with_archived_at_counts_as_archived_never_open(tmp_path):
    report = _report(tmp_path, [(1, "open", ARCHIVED_AT, 4000)])
    assert (report["open_total_cents"], report["archived_total_cents"], report["all_time_total_cents"]) == (0, 4000, 4000)
    assert type(report["open_total_cents"]) is int, "a sum over no rows must be the integer 0"


def test_empty_tickets_give_three_integer_zeros(tmp_path):
    report = _report(tmp_path, [])
    for key in ("open_total_cents", "archived_total_cents", "all_time_total_cents"):
        assert report[key] == 0 and type(report[key]) is int, f"{key} is {report[key]!r} over an empty table"


def test_the_sums_are_computed_in_the_database(tmp_path):
    response = _get(_project(tmp_path / "project", TICKETS), ["/report"])[0]
    sums = sum(len(re.findall(r"\bsum\s*\(", sql, re.I)) for sql in response["sql"] if "cents" in sql.lower())
    assert sums >= 3, f"expected the three sums in the SQL the app ran: {response['sql']}"


def test_the_report_changes_nothing_in_the_database(tmp_path):
    project = _project(tmp_path / "project", TICKETS)
    def snapshot():
        with closing(sqlite3.connect(project / "data.db")) as db:
            return db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall(), \
                db.execute("SELECT * FROM tickets ORDER BY id").fetchall()
    before = snapshot()
    _get(project, ["/report"])
    assert snapshot() == before
