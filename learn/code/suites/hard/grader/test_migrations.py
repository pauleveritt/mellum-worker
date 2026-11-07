"""Migrations must build the promised schema from pristine data and be inert on rerun."""
import sqlite3

import pytest

from grader_tests._database import TICKETS, VISITS, database_snapshot, pristine_migrations, run_migrations


@pytest.fixture
def migrated(tmp_path):
    return pristine_migrations(tmp_path / "application")


def test_all_migrations_are_recorded(migrated):
    with sqlite3.connect(migrated) as connection:
        rows = list(connection.execute(
            "select name from _sqlite_migrations where migration_set = 'agentclinic' order by id"))
    assert [row[0] for row in rows] == [
        "add_tickets_status_archived_index", "backfill_resolved_at",
        "create_open_tickets_view", "add_tickets_note",
    ]


def test_index_exists(migrated):
    with sqlite3.connect(migrated) as connection:
        indexes = {row[1]: row for row in connection.execute("pragma index_list(tickets)")}
        assert "idx_tickets_status_archived" in indexes
        columns = list(connection.execute("pragma index_info(idx_tickets_status_archived)"))
    assert [row[2] for row in columns] == ["status", "archived_at"]


def test_resolved_at_is_backfilled(migrated):
    with sqlite3.connect(migrated) as connection:
        columns = {row[1]: row for row in connection.execute("pragma table_info(tickets)")}
        assert "resolved_at" in columns and columns["resolved_at"][3] == 0
        rows = list(connection.execute("select id,status,archived_at,cents,resolved_at from tickets order by id"))
        visits = list(connection.execute("select * from visits order by id"))
    assert [row[:4] for row in rows] == TICKETS
    assert [row[4] for row in rows] == ["2026-01-03T00:00:00" if status == "resolved" else None
                                      for _, status, _, _ in TICKETS]
    assert visits == sorted(VISITS)


def test_open_tickets_view(migrated):
    with sqlite3.connect(migrated) as connection:
        assert connection.execute("select type from sqlite_master where name = 'open_tickets'").fetchone() == ("view",)
        # The view precedes note in the migration sequence; explicit projection
        # and a different column order are valid alternatives to SELECT *.
        fields = "id,status,archived_at,cents,resolved_at"
        rows = list(connection.execute(f"select {fields} from open_tickets order by id"))
        expected = list(connection.execute(
            f"select {fields} from tickets where status = 'open' and archived_at is null order by id"))
    assert expected and rows == expected


def test_note_column(migrated):
    with sqlite3.connect(migrated) as connection:
        columns = {row[1]: row for row in connection.execute("pragma table_info(tickets)")}
        assert "note" in columns and columns["note"][3] == 0
        connection.execute("update tickets set note = null")
        assert all(row[0] is None for row in connection.execute("select note from tickets"))


def test_rerunning_migrations_is_a_noop(migrated):
    with sqlite3.connect(migrated) as connection:
        connection.execute("update tickets set note = 'keep this note' where id = 11")
    before = database_snapshot(migrated)
    run_migrations(migrated.parent)
    assert database_snapshot(migrated) == before
