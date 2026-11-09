"""Migration `add_tickets_note`, and the four migrations together: the request's acceptance test,
written from `specs/roadmap.md`.

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
ALL_FOUR = ["add_tickets_status_archived_index", "backfill_resolved_at", "create_open_tickets_view", "add_tickets_note"]
SCHEMA = """
CREATE TABLE tickets (id INTEGER PRIMARY KEY, status TEXT NOT NULL, archived_at TEXT, cents INTEGER NOT NULL);
CREATE TABLE visits (id INTEGER PRIMARY KEY, agent TEXT NOT NULL, date TEXT NOT NULL, minutes INTEGER NOT NULL, ticket_id INTEGER);
"""
TICKETS = [(1, "open", None, 100), (2, "open", "2026-01-02T00:00:00", 200), (3, "resolved", None, 300),
           (4, "resolved", "2026-01-02T00:00:00", 400), (5, "archived", None, 500)]


def _copy(target: Path) -> Path:
    return shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__", ".pytest_cache"))


def _migrate(project: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH")}
    return subprocess.run([sys.executable, "-m", "sqlite_utils", "migrate", "data.db"], cwd=project, env=env,
                          capture_output=True, text=True, timeout=60)


def _dump(path: Path) -> tuple[list, dict]:
    """Everything that defines the database: its schema, and every row of every table."""
    with closing(sqlite3.connect(path)) as db:
        schema = db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        tables = [row[1] for row in schema if row[0] == "table" and not row[1].startswith("sqlite_")]
        return schema, {t: db.execute(f'SELECT * FROM "{t}" ORDER BY rowid').fetchall() for t in tables}


def _recorded(path: Path) -> list[str]:
    with closing(sqlite3.connect(path)) as db:
        try:
            rows = db.execute("SELECT name FROM _sqlite_migrations WHERE migration_set = 'agentclinic' ORDER BY rowid")
            return [row[0] for row in rows]
        except sqlite3.OperationalError:
            return []


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> Path:
    """A copy of the project on a fresh database, with the project's migrations applied to it."""
    project = _copy(tmp_path_factory.mktemp("clean") / "project")
    path = project / "data.db"
    path.unlink()
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?)", TICKETS)
        db.commit()
    result = _migrate(project)
    assert result.returncode == 0, f"sqlite-utils migrate failed:\n{result.stdout}{result.stderr}"
    return project


@pytest.mark.parametrize("target", ["the project's data.db", "a clean database"])
def test_note_is_a_nullable_column_and_the_migration_is_recorded(target, clean):
    path = ROOT / "data.db" if target == "the project's data.db" else clean / "data.db"
    with closing(sqlite3.connect(path)) as db:
        columns = {row[1]: row[3] for row in db.execute("PRAGMA table_info(tickets)")}
    assert "note" in columns, f"{target}: tickets has no note column"
    assert columns["note"] == 0, f"{target}: note must be nullable"
    assert "add_tickets_note" in _recorded(path), f"{target}: add_tickets_note is not recorded"


@pytest.mark.parametrize("target", ["the project's data.db", "a clean database"])
def test_the_four_migrations_are_recorded_in_order(target, clean):
    path = ROOT / "data.db" if target == "the project's data.db" else clean / "data.db"
    assert _recorded(path) == ALL_FOUR


def test_no_ticket_row_changes_beyond_the_backfill(clean):
    with closing(sqlite3.connect(clean / "data.db")) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(row) for row in db.execute("SELECT * FROM tickets ORDER BY id")]
    assert [(r["id"], r["status"], r["archived_at"], r["cents"]) for r in rows] == TICKETS
    for row in rows:
        assert row["note"] is None, row
        assert row["resolved_at"] == ("2026-01-03T00:00:00" if row["status"] == "resolved" else None), row


@pytest.mark.parametrize("target", ["the project's data.db", "a clean database"])
def test_migrating_again_changes_nothing(target, clean, tmp_path):
    project = _copy(tmp_path / "project") if target == "the project's data.db" else clean
    before = _dump(project / "data.db")
    result = _migrate(project)
    assert result.returncode == 0, f"sqlite-utils migrate failed:\n{result.stdout}{result.stderr}"
    assert _dump(project / "data.db") == before
