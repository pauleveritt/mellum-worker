"""Migration `backfill_resolved_at`: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

ROOT = Path.cwd()
NAME = "backfill_resolved_at"
STAMP = "2026-01-03T00:00:00"
SCHEMA = """
CREATE TABLE tickets (id INTEGER PRIMARY KEY, status TEXT NOT NULL, archived_at TEXT, cents INTEGER NOT NULL);
CREATE TABLE visits (id INTEGER PRIMARY KEY, agent TEXT NOT NULL, date TEXT NOT NULL, minutes INTEGER NOT NULL, ticket_id INTEGER);
"""
TICKETS = [(1, "open", None, 100), (2, "open", "2026-01-02T00:00:00", 200), (3, "resolved", None, 300),
           (4, "resolved", "2026-01-02T00:00:00", 400), (5, "archived", None, 500)]


def _recorded(path: Path) -> list[str]:
    with closing(sqlite3.connect(path)) as db:
        try:
            rows = db.execute("SELECT name FROM _sqlite_migrations WHERE migration_set = 'agentclinic' ORDER BY rowid")
            return [row[0] for row in rows]
        except sqlite3.OperationalError:
            return []


def _rows(path: Path) -> list[dict]:
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM tickets ORDER BY id")]


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> Path:
    """A fresh database with the project's migrations applied to it, in a copy of the project."""
    project = shutil.copytree(ROOT, tmp_path_factory.mktemp("clean") / "project", ignore=shutil.ignore_patterns(
        ".venv", ".git", "__pycache__", ".pytest_cache"))
    path = project / "data.db"
    path.unlink()
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?)", TICKETS)
        db.commit()
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH")}
    result = subprocess.run([sys.executable, "-m", "sqlite_utils", "migrate", "data.db"], cwd=project, env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"sqlite-utils migrate failed:\n{result.stdout}{result.stderr}"
    return path


@pytest.mark.parametrize("target", ["the project's data.db", "a clean database"])
def test_resolved_at_is_nullable_every_resolved_row_is_backfilled_and_it_is_recorded(target, clean):
    path = ROOT / "data.db" if target == "the project's data.db" else clean
    with closing(sqlite3.connect(path)) as db:
        columns = {row[1]: row[3] for row in db.execute("PRAGMA table_info(tickets)")}
    assert "resolved_at" in columns, f"{target}: tickets has no resolved_at column"
    assert columns["resolved_at"] == 0, f"{target}: resolved_at must be nullable"
    for row in _rows(path):
        if row["status"] == "resolved":
            assert row["resolved_at"] == STAMP, f"{target}: {row}"
    assert NAME in _recorded(path), f"{target}: {NAME} is not recorded in _sqlite_migrations"


def test_only_resolved_rows_get_a_resolved_at_and_no_other_ticket_data_changes(clean):
    rows = _rows(clean)
    assert [(r["id"], r["status"], r["archived_at"], r["cents"]) for r in rows] == TICKETS
    for row in rows:
        assert row["resolved_at"] == (STAMP if row["status"] == "resolved" else None), row
