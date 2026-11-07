"""Private SQLite controls: real queries, varied data, and pristine migrations."""
from contextlib import contextmanager
from functools import cache
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from weakref import WeakSet

# Deliberately unlike the public database; include each archive/status combination.
TICKETS = [
    (11, "open", None, 137),
    (24, "resolved", None, 299),
    (38, "open", "2031-02-04T12:00:00", 503),
    (42, "resolved", "2031-02-05T12:00:00", 701),
    (56, "open", None, 887),
]
VISITS = [
    (1, "Zed", "2031-04-10", 9, 11),
    (2, "Ada", "2031-04-10", 20, 24),
    (3, "Ada", "2031-04-12", 21, 24),
    (4, "Bea", "2031-04-11", 41, 38),
    (5, "Zed", "2031-04-12", 32, 11),
    (6, "Outside", "2031-04-09", 999, 11),
    (7, "Outside", "2031-04-13", 999, 11),
    *[(20 + i, f"Visitor {i:02}", "2031-04-11", i + 1, None) for i in range(12)],
]


@contextmanager
def table_rows(table, columns, rows):
    """Restore data even when a check fails; do not constrain extra nullable columns."""
    with sqlite3.connect("data.db") as connection:
        previous = list(connection.execute(f"select * from {table}"))
        names = [row[1] for row in connection.execute(f"pragma table_info({table})")]
        connection.execute(f"delete from {table}")
        connection.executemany(
            f"insert into {table} ({','.join(columns)}) values ({','.join('?' for _ in columns)})", rows,
        )
    try:
        yield
    finally:
        with sqlite3.connect("data.db") as connection:
            connection.execute(f"delete from {table}")
            connection.executemany(
                f"insert into {table} values ({','.join('?' for _ in names)})", previous,
            )


_capture = None
_connections = WeakSet()
_original_connect = sqlite3.connect
_installed = False


def _record(sql, parameters, connection):
    if _capture is not None:
        calls, _ = _capture
        values = tuple(parameters.values()) if isinstance(parameters, dict) else tuple(parameters)
        calls.append((sql, values))
        # Observe SQLite computation rather than prescribing aggregate names.
        # EXPLAIN compiles the same bound query without executing its data effects.
        if not sql.lstrip().casefold().startswith("explain"):
            operations = {row[1] for row in sqlite3.Connection.execute(connection, "EXPLAIN " + sql, parameters)}
            if operations & {"AggStep", "AggFinal", "AggValue"}:
                _capture[1].add("database-aggregate")
            if {"Add", "InitCoroutine", "Yield"} <= operations:
                _capture[1].add("database-aggregate")


class _CursorRecording:
    def execute(self, sql, parameters=()):
        _record(sql, parameters, self.connection)
        return super().execute(sql, parameters)


class _ConnectionRecording:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._application_authorizer = None
        _connections.add(self)
        self._refresh_authorizer()

    def _authorize(self, action, first, second, database, source):
        if _capture is not None and action == sqlite3.SQLITE_FUNCTION:
            _capture[1].add((second or first).casefold())
        if self._application_authorizer:
            return self._application_authorizer(action, first, second, database, source)
        return sqlite3.SQLITE_OK

    def _refresh_authorizer(self):
        super().set_authorizer(self._authorize)

    def set_authorizer(self, callback):
        self._application_authorizer = callback
        self._refresh_authorizer()

    def execute(self, sql, parameters=()):
        _record(sql, parameters, self)
        return super().execute(sql, parameters)

    def cursor(self, factory=sqlite3.Cursor):
        return super().cursor(factory=_cursor_type(factory))


@cache
def _cursor_type(factory):
    return type("RecordedCursor", (_CursorRecording, factory), {})


@cache
def _connection_type(factory):
    return type("RecordedConnection", (_ConnectionRecording, factory), {})


def install_sql_recording():
    """Install before app imports so startup connections stay real and observable."""
    global _installed
    if _installed:
        return

    def connect(*args, **kwargs):
        if len(args) > 5:
            args = (*args[:5], _connection_type(args[5]), *args[6:])
        else:
            kwargs["factory"] = _connection_type(kwargs.get("factory", sqlite3.Connection))
        return _original_connect(*args, **kwargs)

    sqlite3.connect = sqlite3.dbapi2.connect = connect
    _installed = True


@contextmanager
def sql_calls():
    """Capture real SQL and database functions without inspecting application objects."""
    global _capture
    previous, _capture = _capture, ([], set())
    # Refresh also invalidates cached statements, so SQLite reports their functions.
    for connection in list(_connections):
        try:
            connection._refresh_authorizer()
        except sqlite3.ProgrammingError:  # an explicitly closed connection
            pass
    try:
        yield _capture
    finally:
        _capture = previous


def run_migrations(path):
    env = os.environ.copy()
    env.update(UV_PROJECT_ENVIRONMENT=sys.prefix, UV_NO_SYNC="1")
    result = subprocess.run(
        ["uv", "run", "--frozen", "sqlite-utils", "migrate", "data.db"],
        cwd=path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def pristine_migrations(path):
    """Exercise the submitted migrations through their documented CLI, from no ledger."""
    shutil.copytree(
        Path.cwd(), path, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "data.db*", ".git"),
    )
    with sqlite3.connect(path / "data.db") as connection:
        connection.executescript(
            "create table tickets(id integer primary key, status text not null, archived_at text, cents integer not null);"
            "create table visits(id integer primary key, agent text not null, date text not null, minutes integer not null, ticket_id integer);"
        )
        connection.executemany("insert into tickets values (?,?,?,?)", TICKETS)
        connection.executemany("insert into visits values (?,?,?,?,?)", VISITS)
    run_migrations(path)
    return path / "data.db"


def database_snapshot(path):
    """Logical schema and every table's data, including the complete migration ledger."""
    with sqlite3.connect(path) as connection:
        schema = tuple(connection.execute(
            "select type, name, tbl_name, sql from sqlite_master order by type, name"))
        tables = [name for kind, name, _, _ in schema if kind == "table"]
        rows = {
            name: sorted(connection.execute('select * from "' + name.replace('"', '""') + '"'), key=repr)
            for name in tables
        }
    return schema, rows
