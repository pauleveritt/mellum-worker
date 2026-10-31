from starlette.testclient import TestClient
from app import app
import os
import sqlite3

client = TestClient(app, follow_redirects=False)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text

def test_complaints_route():
    response = client.get("/complaints")
    assert response.status_code == 200

def test_database_schema():
    db_path = os.path.join(os.path.dirname(__file__), "..", "data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(tickets)")
    tickets_columns = [row[1] for row in cursor.fetchall()]
    assert set(tickets_columns) == {"id", "status", "archived_at", "cents"}
    
    cursor.execute("PRAGMA table_info(visits)")
    visits_columns = [row[1] for row in cursor.fetchall()]
    assert set(visits_columns) == {"id", "agent", "date", "minutes", "ticket_id"}
    
    conn.close()
