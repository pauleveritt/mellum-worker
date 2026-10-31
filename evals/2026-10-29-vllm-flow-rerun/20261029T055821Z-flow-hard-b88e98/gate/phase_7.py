from starlette.testclient import TestClient
from app import app
import sqlite3
import os

client = TestClient(app, follow_redirects=False)

def get_db_path():
    return os.path.join(os.path.dirname(__file__), "..", "data.db")

def test_add_tickets_note_migration_adds_column():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "note" in columns, "tickets table should have a note column after migration"
    # Check nullability
    cursor.execute("PRAGMA table_info(tickets)")
    for col in cursor.fetchall():
        if col[1] == "note":
            nullable = col[3] == 1  # 1 means YES
            assert nullable, "note column should be nullable"
    conn.close()

def test_visits_report_endpoint():
    # Setup: clear visits and insert test data
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure visits table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            agent TEXT NOT NULL,
            date TEXT NOT NULL,
            minutes INTEGER NOT NULL,
            ticket_id INTEGER NOT NULL
        )
    """)
    
    # Delete existing visits to have clean state
    cursor.execute("DELETE FROM visits")
    conn.commit()
    
    # Insert test visits
    visits = [
        (1, "AgentA", "2024-01-01", 30, 1),
        (2, "AgentA", "2024-01-02", 45, 2),
        (3, "AgentB", "2024-01-01", 60, 3),
        (4, "AgentB", "2024-01-03", 15, 4),
        (5, "AgentC", "2024-01-02", 100, 5),
        (6, "AgentC", "2024-01-03", 200, 6),
    ]
    cursor.executemany("INSERT INTO visits (id, agent, date, minutes, ticket_id) VALUES (?, ?, ?, ?, ?)", visits)
    conn.commit()
    conn.close()
    
    # Test default parameters
    response = client.get("/visits")
    assert response.status_code == 200
    data = response.json()
    visits_result = data.get("visits", [])
    expected_default = [
        {"agent": "AgentC", "count": 2, "total_minutes": 300, "average_minutes": 150.0},
        {"agent": "AgentA", "count": 2, "total_minutes": 75, "average_minutes": 37.5},
        {"agent": "AgentB", "count": 2, "total_minutes": 75, "average_minutes": 37.5},
    ]
    assert visits_result == expected_default
    
    # Test min_minutes filter
    response = client.get("/visits", params={"min_minutes": 100})
    assert response.status_code == 200
    data = response.json()
    visits_result = data.get("visits", [])
    expected_min_100 = [
        {"agent": "AgentC", "count": 2, "total_minutes": 300, "average_minutes": 150.0},
    ]
    assert visits_result == expected_min_100
    
    # Test date range filter
    response = client.get("/visits", params={"from": "2024-01-01", "to": "2024-01-02"})
    assert response.status_code == 200
    data = response.json()
    visits_result = data.get("visits", [])
    expected_date_range = [
        {"agent": "AgentC", "count": 1, "total_minutes": 100, "average_minutes": 100.0},
        {"agent": "AgentA", "count": 2, "total_minutes": 75, "average_minutes": 37.5},
        {"agent": "AgentB", "count": 1, "total_minutes": 60, "average_minutes": 60.0},
    ]
    assert visits_result == expected_date_range
    
    # Test limit parameter
    response = client.get("/visits", params={"limit": 2})
    assert response.status_code == 200
    data = response.json()
    visits_result = data.get("visits", [])
    assert len(visits_result) == 2
    expected_limited = [
        {"agent": "AgentC", "count": 2, "total_minutes": 300, "average_minutes": 150.0},
        {"agent": "AgentA", "count": 2, "total_minutes": 75, "average_minutes": 37.5},
    ]
    assert visits_result == expected_limited[:2]
    
    # Clean up
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visits")
    conn.commit()
    conn.close()
