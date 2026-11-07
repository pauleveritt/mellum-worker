from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_archive_complaint_when_resolved():
    # Resolve complaint 1 first
    response = client.post("/complaints/1/resolve")
    assert response.status_code == 303
    # Archive it
    response = client.post("/complaints/1/archive")
    assert response.status_code == 303
    # Check it's hidden from complaints page
    response = client.get("/complaints")
    assert response.status_code == 200
    # The archived complaint should not appear
    from models import complaints
    assert not any(c.id == 1 and c.status != "archived" for c in complaints)
    # Actually, status should be archived
    c = next((c for c in complaints if c.id == 1), None)
    assert c is not None
    assert c.status == "archived"
    # Check audit
    from models import audit
    assert any(entry for entry in audit if entry["id"] == 1 and entry["action"] == "archive")

def test_archive_complaint_when_not_resolved():
    response = client.post("/complaints/2/archive")
    assert response.status_code == 400
    from models import complaints
    c = next((c for c in complaints if c.id == 2), None)
    assert c.status == "open"

def test_stats_counts_only_open():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["open"] == 3  # initial open count
    # Resolve one
    client.post("/complaints/1/resolve")
    response = client.get("/stats")
    data = response.json()
    assert data["open"] == 2
    # Archive the resolved one
    client.post("/complaints/1/archive")
    response = client.get("/stats")
    data = response.json()
    assert data["open"] == 2  # archived not counted

def test_audit_entries_for_status_changes():
    from models import audit, audit_seq
    initial_len = len(audit)
    initial_seq = audit_seq
    # Resolve
    client.post("/complaints/1/resolve")
    # Reopen
    client.post("/complaints/1/reopen")
    # Archive (after ensuring resolved)
    client.post("/complaints/1/resolve")
    client.post("/complaints/1/archive")
    assert len(audit) == initial_len + 3
    # Check entries
    entries = audit[initial_len:]
    assert entries[0]["id"] == 1
    assert entries[0]["action"] == "resolve"
    assert entries[1]["id"] == 1
    assert entries[1]["action"] == "reopen"
    assert entries[2]["id"] == 1
    assert entries[2]["action"] == "archive"
    # Check seq continuity
    seq_vals = [e["seq"] for e in entries]
    assert seq_vals == list(range(initial_seq+1, initial_seq+4))

def test_id_permanence_after_archive():
    from models import complaints
    # Find max id before new complaint
    max_id = max(c.id for c in complaints)
    # Archive the last complaint (id max_id) after resolving
    cid = max_id
    client.post(f"/complaints/{cid}/resolve")
    client.post(f"/complaints/{cid}/archive")
    # Add new complaint
    response = client.post("/complaints", data={"agent_name": "NewAgent", "text": "New complaint"})
    assert response.status_code == 303
    from models import complaints as current
    new_cid = None
    for c in current:
        if c.agent_name == "NewAgent" and c.text == "New complaint":
            new_cid = c.id
            break
    assert new_cid is not None
    assert new_cid == max_id + 1
    # The archived complaint should still exist with original id
    archived = next((c for c in current if c.id == cid), None)
    assert archived is not None
    assert archived.status == "archived"
