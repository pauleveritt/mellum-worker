from starlette.testclient import TestClient
from app import app
import sqlite3
from collections import defaultdict

client = TestClient(app, follow_redirects=False)

def test_visits_endpoint_aggregates_correctly():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM visits")
    row = cursor.fetchone()
    min_date = row["min_date"]
    max_date = row["max_date"]
    
    cursor.execute("SELECT agent, minutes FROM visits WHERE date BETWEEN ? AND ?", (min_date, max_date))
    all_visits = cursor.fetchall()
    
    agg = defaultdict(lambda: {"count": 0, "total_minutes": 0})
    for visit in all_visits:
        agent = visit["agent"]
        minutes = visit["minutes"]
        if minutes >= 0:
            agg[agent]["count"] += 1
            agg[agent]["total_minutes"] += minutes
    
    result_list = []
    for agent, data in agg.items():
        avg = data["total_minutes"] / data["count"] if data["count"] > 0 else 0
        result_list.append({
            "agent": agent,
            "count": data["count"],
            "total_minutes": data["total_minutes"],
            "average_minutes": avg
        })
    
    result_list.sort(key=lambda x: (-x["total_minutes"], x["agent"]))
    limited_result = result_list[:10]
    
    response = client.get(f"/visits?from={min_date}&to={max_date}&min_minutes=0&limit=10")
    assert response.status_code == 200
    response_data = response.json()
    assert "visits" in response_data
    response_visits = response_data["visits"]
    
    assert len(response_visits) == len(limited_result)
    for resp, exp in zip(response_visits, limited_result):
        assert resp["agent"] == exp["agent"]
        assert resp["count"] == exp["count"]
        assert resp["total_minutes"] == exp["total_minutes"]
        assert abs(resp["average_minutes"] - exp["average_minutes"]) < 0.001
    
    conn.close()
    
    # Test min_minutes filter excludes all visits
    high_min = 1000000
    response = client.get(f"/visits?from={min_date}&to={max_date}&min_minutes={high_min}&limit=10")
    assert response.status_code == 200
    assert response.json()["visits"] == []
    
    # Test limit parameter
    response = client.get(f"/visits?from={min_date}&to={max_date}&min_minutes=0&limit=1")
    assert response.status_code == 200
    assert len(response.json()["visits"]) == 1

def test_add_tickets_note_migration_exists_and_adds_column():
    with open("migrations.py", "r") as f:
        content = f.read()
    assert "add_tickets_note" in content
    assert "note" in content
    
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "note" in columns
    
    cursor.execute("PRAGMA table_info(tickets) WHERE colname = 'note'")
    note_row = cursor.fetchone()
    assert note_row is not None
    # notnull column: 0 = nullable, 1 = NOT NULL
    assert note_row[3] == 0
    conn.close()
