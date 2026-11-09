"""Migration `create_open_tickets_view`: the request's acceptance test, written from `specs/roadmap.md`.

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
NAME = "create_open_tickets_view"
SCHEMA = """
CREATE TABLE tickets (id INTEGER PRIMARY KEY, status TEXT NOT NULL, archived_at TEXT, cents INTEGER NOT NULL);
CREATE TABLE visits (id INTEGER PRIMARY KEY, agent TEXT NOT NULL, date TEXT NOT NULL, minutes INTEGER NOT NULL, ticket_id INTEGER);
"""
TICKETS = [(1, "open", None, 100), (2, "open", "2026-01-02T00:00:00", 200), (3, "resolved", None, 300),
           (4, "resolved", "2026-01-02T00:00:00", 400), (5, "archived", None, 500), (6, "open", None, 600)]


def _recorded(path: Path) -> list[str]:
    with closing(sqlite3.connect(path)) as db:
        try:
            rows = db.execute("SELECT name FROM _sqlite_migrations WHERE migration_set = 'agentclinic' ORDER BY rowid")
            return [row[0] for row in rows]
        except sqlite3.OperationalError:
            return []


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


def _rows(db: sqlite3.Connection, sql: str) -> list[dict]:
    db.row_factory = sqlite3.Row
    return [dict(row) for row in db.execute(sql)]


@pytest.mark.parametrize("target", ["the project's data.db", "a clean database"])
def test_the_view_holds_exactly_the_open_unarchived_tickets_and_it_is_recorded(target, clean):
    path = ROOT / "data.db" if target == "the project's data.db" else clean
    with closing(sqlite3.connect(path)) as db:
        kind = db.execute("SELECT type FROM sqlite_master WHERE name = 'open_tickets'").fetchone()
        assert kind == ("view",), f"{target}: open_tickets is not a view: {kind}"
        wanted = _rows(db, "SELECT * FROM tickets WHERE status = 'open' AND archived_at IS NULL ORDER BY id")
        held = _rows(db, "SELECT * FROM open_tickets ORDER BY id")
    assert [r["id"] for r in held] == [r["id"] for r in wanted], f"{target}: wrong rows in open_tickets"
    if held:
        assert {"id", "status", "archived_at", "cents"} <= set(held[0]), f"{target}: the view lacks ticket columns"
    for row, ticket in zip(held, wanted):
        assert all(row[k] == ticket[k] for k in row if k in ticket), f"{target}: {row} differs from {ticket}"
    assert NAME in _recorded(path), f"{target}: {NAME} is not recorded in _sqlite_migrations"


def test_the_view_tracks_the_table_and_no_ticket_row_changed(clean):
    with closing(sqlite3.connect(clean)) as db:
        rows = db.execute("SELECT id, status, archived_at, cents FROM tickets ORDER BY id").fetchall()
        assert rows == TICKETS
        db.execute("INSERT INTO tickets (id, status, archived_at, cents) VALUES (100, 'open', NULL, 1)")
        ids = [row[0] for row in db.execute("SELECT id FROM open_tickets")]
        db.rollback()
    assert 100 in ids, "open_tickets must be a view over tickets, not a copy"
