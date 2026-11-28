from starlette.testclient import TestClient
from app import app
import sqlite3

client = TestClient(app, follow_redirects=False)

def test_report_endpoint_returns_correct_sums():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN status = 'open' AND archived_at IS NULL THEN cents END) AS open_total_cents,
            SUM(CASE WHEN archived_at IS NOT NULL THEN cents END) AS archived_total_cents,
            SUM(cents) AS all_time_total_cents
        FROM tickets
    """)
    row = cursor.fetchone()
    conn.close()

    open_total = row["open_total_cents"] or 0
    archived_total = row["archived_total_cents"] or 0
    all_time_total = row["all_time_total_cents"] or 0

    response = client.get("/report")
    assert response.status_code == 200
    data = response.json()
    assert data["open_total_cents"] == open_total
    assert data["archived_total_cents"] == archived_total
    assert data["all_time_total_cents"] == all_time_total

def test_backfill_resolved_at_migration():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(tickets)")
    columns = [col["name"] for col in cursor.fetchall()]
    assert "resolved_at" in columns

    cursor.execute("""
        SELECT resolved_at FROM tickets
        WHERE status = 'resolved' AND resolved_at IS NOT NULL
    """)
    rows = cursor.fetchall()
    assert len(rows) > 0, "No resolved tickets found"
    for row in rows:
        resolved_at = row["resolved_at"]
        assert resolved_at is not None
        assert "2026-01-03" in str(resolved_at)

    conn.close()

def test_create_open_tickets_view():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'view' AND name = 'open_tickets'
    """)
    view = cursor.fetchone()
    assert view is not None, "View open_tickets does not exist"

    cursor.execute("SELECT COUNT(*) FROM open_tickets")
    view_count = cursor.fetchone()["COUNT(*)"]

    cursor.execute("""
        SELECT COUNT(*) FROM tickets
        WHERE status = 'open' AND archived_at IS NULL
    """)
    direct_count = cursor.fetchone()["COUNT(*)"]
    assert view_count == direct_count

    conn.close()
