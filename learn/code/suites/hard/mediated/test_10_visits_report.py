"""Phase 7 — Visits report: the request's acceptance test, written from `specs/roadmap.md`.

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
from urllib.parse import quote

import pytest

ROOT = Path.cwd()
SCHEMA = """
CREATE TABLE tickets (id INTEGER PRIMARY KEY, status TEXT NOT NULL, archived_at TEXT, cents INTEGER NOT NULL);
CREATE TABLE visits (id INTEGER PRIMARY KEY, agent TEXT NOT NULL, date TEXT NOT NULL, minutes INTEGER NOT NULL, ticket_id INTEGER);
"""
# March 2026 holds the report's cases; dates just outside it must never count. May holds 12 agents.
VISITS = [
    ("alice", "2026-03-01", 40), ("alice", "2026-03-15", 20),
    ("bob", "2026-03-31", 90),
    ("carol", "2026-03-10", 30), ("carol", "2026-03-11", 15), ("carol", "2026-03-12", 15),
    ("frank", "2026-03-03", 10), ("frank", "2026-03-04", 15),
    ("eve", "2026-03-02", 5),
    ("dan", "2026-02-28", 500), ("dan", "2026-04-01", 500),
    *[(f"g{n:02d}", day, 25) for n in range(12) for day in ("2026-05-10", "2026-05-11")],
]
MARCH = "from=2026-03-01&to=2026-03-31"
MAY = "from=2026-05-01&to=2026-05-31"
URLS = {
    "march": f"/visits?{MARCH}",
    "min20": f"/visits?{MARCH}&min_minutes=20",
    "limit1": f"/visits?{MARCH}&limit=1",
    "may": f"/visits?{MAY}",
    "may_limit3": f"/visits?{MAY}&limit=3",
    "day": "/visits?from=2026-03-31&to=2026-03-31",
    "injected": "/visits?from=2026-03-01&to=" + quote("2026-03-31' OR '1'='1"),
    "bound": f"/visits?from=2026-03-02&to=2026-03-30&min_minutes=37",
}
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


@pytest.fixture(scope="module")
def responses(tmp_path_factory) -> dict[str, dict]:
    """Each URL answered by a copy of the project running on a fresh database."""
    scratch = tmp_path_factory.mktemp("visits")
    project = shutil.copytree(ROOT, scratch / "project", ignore=shutil.ignore_patterns(
        ".venv", ".git", "__pycache__", ".pytest_cache"))
    path = project / "data.db"
    path.unlink()
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO visits (agent, date, minutes) VALUES (?, ?, ?)", VISITS)
        db.commit()
    if (project / "migrations.py").exists():
        result = subprocess.run([sys.executable, "-m", "sqlite_utils", "migrate", "data.db"], cwd=project,
                                env=_env(project), capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, f"sqlite-utils migrate failed:\n{result.stdout}{result.stderr}"
    out = scratch / "out.json"
    result = subprocess.run([sys.executable, "-c", DRIVER, str(out), json.dumps(list(URLS.values()))], cwd=project,
                            env=_env(project), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"the app did not run:\n{result.stdout[-800:]}{result.stderr[-1200:]}"
    return dict(zip(URLS, json.loads(out.read_text())))


def _visits(responses, key: str) -> list[dict]:
    response = responses[key]
    assert response["status"] == 200, f"GET {URLS[key]} answered {response['status']}: {response['text'][:500]}"
    body = json.loads(response["text"])
    assert set(body) >= {"visits"} and isinstance(body["visits"], list), body
    return body["visits"]


def _row(agent: str, count: int, total: int, average: float) -> dict:
    return {"agent": agent, "count": count, "total_minutes": total, "average_minutes": average}


def _check(entries: list[dict], expected: list[dict]) -> None:
    assert [e["agent"] for e in entries] == [e["agent"] for e in expected]
    for entry, want in zip(entries, expected):
        assert {"agent", "count", "total_minutes", "average_minutes"} <= set(entry), entry
        assert entry["count"] == want["count"] and type(entry["count"]) is int, entry
        assert entry["total_minutes"] == want["total_minutes"] and type(entry["total_minutes"]) is int, entry
        assert type(entry["average_minutes"]) is float, f"average_minutes must be a float: {entry}"
        assert entry["average_minutes"] == pytest.approx(want["average_minutes"]), entry


def test_a_range_is_inclusive_grouped_by_agent_and_sorted_by_total_then_agent(responses):
    _check(_visits(responses, "march"), [_row("bob", 1, 90, 90.0), _row("alice", 2, 60, 30.0),
                                         _row("carol", 3, 60, 20.0), _row("frank", 2, 25, 12.5),
                                         _row("eve", 1, 5, 5.0)])


def test_a_single_day_range_keeps_visits_on_that_day(responses):
    _check(_visits(responses, "day"), [_row("bob", 1, 90, 90.0)])


def test_min_minutes_keeps_only_visits_with_at_least_that_many_minutes(responses):
    # alice's 20 is kept at the boundary, carol's 15s and frank's and eve's visits are dropped.
    _check(_visits(responses, "min20"), [_row("bob", 1, 90, 90.0), _row("alice", 2, 60, 30.0),
                                         _row("carol", 1, 30, 30.0)])


def test_limit_holds_at_most_that_many_entries_after_sorting(responses):
    _check(_visits(responses, "limit1"), [_row("bob", 1, 90, 90.0)])


def test_the_default_limit_is_ten_agents_not_ten_rows(responses):
    entries = _visits(responses, "may")
    assert [e["agent"] for e in entries] == [f"g{n:02d}" for n in range(10)]
    assert all(e["count"] == 2 and e["total_minutes"] == 50 for e in entries), entries


def test_a_smaller_limit_applies_to_agents(responses):
    assert [e["agent"] for e in _visits(responses, "may_limit3")] == ["g00", "g01", "g02"]


def test_filter_values_are_not_concatenated_into_the_sql(responses):
    for sql in responses["bound"]["sql"]:
        for value in ("2026-03-02", "2026-03-30"):
            assert value not in sql, f"{value} was concatenated into: {sql}"
        assert not re.search(r"\b37\b", sql), f"min_minutes was concatenated into: {sql}"
    assert responses["bound"]["status"] == 200


def test_an_injected_date_is_treated_as_a_value_and_never_widens_the_range(responses):
    response = responses["injected"]
    assert response["status"] < 500, f"an injected date made the server fail: {response['text'][:300]}"
    if response["status"] == 200:
        agents = [e["agent"] for e in json.loads(response["text"])["visits"]]
        assert "dan" not in agents, "an injected date widened the range"
        assert not any(a.startswith("g") for a in agents), "an injected date widened the range"
