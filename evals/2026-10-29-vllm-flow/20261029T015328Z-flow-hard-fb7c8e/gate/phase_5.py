from starlette.testclient import TestClient
from app import app
import sqlite3
try:
    from models import audit as audit_log
except ImportError:
    audit_log = None
from models import complaints as model_complaints

client = TestClient(app, follow_redirects=False)

def test_archive_complaint_when_resolved():
    # Create a complaint
    response = client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint for archive"})
    assert response.status_code == 303
    # Get the id of the newly created complaint
    assert len(model_complaints) >= 1
    new_id = model_complaints[-1].id
    # Resolve the complaint
    response = client.post(f"/complaints/{new_id}/resolve", follow_redirects=False)
    assert response.status_code == 303
    # Archive the complaint
    response = client.post(f"/complaints/{new_id}/archive", follow_redirects=False)
    assert response.status_code == 303
    # Check that the complaint status is now archived in the model
    complaint = next(c for c in model_complaints if c.id == new_id)
    assert complaint.status == "archived"
    # Check that the archived complaint is hidden from GET /complaints
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Test complaint for archive" not in response.text
    # Ensure the complaint is still in the model list (not removed)
    assert any(c.id == new_id for c in model_complaints)

def test_archive_complaint_when_not_resolved_returns_400():
    # Create a complaint
    response = client.post("/complaints", data={"agent_name": "TestAgent2", "text": "Test complaint not resolved"})
    assert response.status_code == 303
    assert len(model_complaints) >= 1
    new_id = model_complaints[-1].id
    # Try to archive without resolving
    response = client.post(f"/complaints/{new_id}/archive", follow_redirects=False)
    assert response.status_code == 400
    # Status should still be open
    complaint = next(c for c in model_complaints if c.id == new_id)
    assert complaint.status == "open"

def test_get_stats_returns_open_count():
    # Get current open count
    response = client.get("/stats")
    assert response.status_code == 200
    import json
    stats = response.json()
    open_count_before = stats.get("open", 0)
    # Create a new open complaint
    client.post("/complaints", data={"agent_name": "StatsAgent", "text": "Stats complaint"})
    # Get open count again
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    open_count_after = stats.get("open", 0)
    assert open_count_after == open_count_before + 1

def test_audit_trail_records_actions():
    # Create a complaint
    response = client.post("/complaints", data={"agent_name": "AuditAgent", "text": "Audit complaint"})
    assert response.status_code == 303
    assert len(model_complaints) >= 1
    new_id = model_complaints[-1].id
    # Resolve
    client.post(f"/complaints/{new_id}/resolve", follow_redirects=False)
    # Reopen
    client.post(f"/complaints/{new_id}/reopen", follow_redirects=False)
    # Archive
    client.post(f"/complaints/{new_id}/archive", follow_redirects=False)
    # Check audit log exists
    assert audit_log is not None, "audit_log not found in models"
    # Filter entries for this complaint
    entries = [entry for entry in audit_log if entry["id"] == new_id]
    assert len(entries) == 3
    actions = [entry["action"] for entry in entries]
    assert actions == ["resolve", "reopen", "archive"]
    # Check seq is strictly increasing overall
    seqs = [entry["seq"] for entry in audit_log]
    assert seqs == sorted(seqs)
    assert seqs == list(range(1, len(seqs) + 1))

def test_migration_index_exists():
    # Connect to the database
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    # Check index idx_tickets_status_archived exists on tickets table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tickets' AND name='idx_tickets_status_archived'")
    index_exists = cursor.fetchone() is not None
    conn.close()
    assert index_exists, "Index idx_tickets_status_archived does not exist on tickets table"
