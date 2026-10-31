from starlette.testclient import TestClient
from app import app
import sqlite3
import os

client = TestClient(app, follow_redirects=False)

def get_db_path():
    return os.path.join(os.path.dirname(__file__), "..", "data.db")

def test_report_endpoint_sums():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(cents) FROM tickets WHERE archived_at IS NULL AND status = 'open'")
    open_total_cents = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(cents) FROM tickets WHERE archived_at IS NOT NULL")
    archived_total_cents = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(cents) FROM tickets")
    all_time_total_cents = cursor.fetchone()[0] or 0
    
    conn.close()
    
    response = client.get("/report")
    assert response.status_code == 200
    data = response.json()
    assert data["open_total_cents"] == open_total_cents
    assert data["archived_total_cents"] == archived_total_cents
    assert data["all_time_total_cents"] == all_time_total_cents

def test_backfill_resolved_at_migration():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "resolved_at" in columns, "resolved_at column missing"
    
    cursor.execute("""
        SELECT COUNT(*) FROM tickets 
        WHERE status = 'resolved' AND resolved_at IS NULL
    """)
    null_resolved_count = cursor.fetchone()[0]
    assert null_resolved_count == 0, f"{null_resolved_count} resolved tickets missing resolved_at"
    
    cursor.execute("""
        SELECT COUNT(*) FROM tickets 
        WHERE status = 'resolved' AND resolved_at != '2026-01-03T00:00:00'
    """)
    wrong_value_count = cursor.fetchone()[0]
    assert wrong_value_count == 0, f"{wrong_value_count} resolved tickets have wrong resolved_at"
    
    conn.close()

def test_create_open_tickets_view_migration():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='view' AND name='open_tickets'
    """)
    view_info = cursor.fetchone()
    assert view_info is not None, "open_tickets view does not exist"
    view_sql = view_info[0]
    assert "status = 'open'" in view_sql
    assert "archived_at IS NULL" in view_sql
    
    conn.close()
