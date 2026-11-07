import sqlite3
import subprocess


def _connect():
    return sqlite3.connect("data.db")


def test_all_migrations_are_recorded():
    con = _connect()
    try:
        rows = list(con.execute(
            "select name from _sqlite_migrations where migration_set = 'agentclinic' order by id"))
    finally:
        con.close()
    assert [row[0] for row in rows] == [
        "add_tickets_status_archived_index",
        "backfill_resolved_at",
        "create_open_tickets_view",
        "add_tickets_note",
    ]


def test_index_exists():
    con = _connect()
    try:
        names = {row[0] for row in con.execute(
            "select name from sqlite_master where type = 'index'")}
    finally:
        con.close()
    assert "idx_tickets_status_archived" in names


def test_resolved_at_is_backfilled():
    con = _connect()
    try:
        rows = list(con.execute(
            "select resolved_at from tickets where status = 'resolved'"))
    finally:
        con.close()
    assert rows and all(row[0] == "2026-01-03T00:00:00" for row in rows)


def test_open_tickets_view():
    con = _connect()
    try:
        rows = list(con.execute("select id, status, archived_at from open_tickets"))
    finally:
        con.close()
    assert all(status == "open" and archived is None for _, status, archived in rows)


def test_note_column():
    con = _connect()
    try:
        columns = [row[1] for row in con.execute("pragma table_info(tickets)")]
    finally:
        con.close()
    assert "note" in columns


def test_rerunning_migrations_is_a_noop():
    con = _connect()
    try:
        before = list(con.execute("select id, name from _sqlite_migrations order by id"))
    finally:
        con.close()
    subprocess.run(
        ["uv", "run", "--frozen", "sqlite-utils", "migrate", "data.db"],
        check=True, capture_output=True, text=True,
    )
    con = _connect()
    try:
        after = list(con.execute("select id, name from _sqlite_migrations order by id"))
    finally:
        con.close()
    assert after == before
