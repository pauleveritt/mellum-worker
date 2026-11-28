from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text

def test_complaints_board():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaint():
    response = client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"

def test_post_complaint_appears_on_board():
    # Post a new complaint
    client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"})
    # Get the complaints board
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "TestAgent" in response.text
    assert "Test complaint" in response.text

def test_resolve_complaint():
    # Post a new complaint
    response = client.post("/complaints", data={"agent_name": "ResolveTest", "text": "Resolve test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    # Get complaint ids before resolving
    response = client.get("/complaints")
    assert response.status_code == 200
    import re
    ids_before = re.findall(r'/complaints/(\d+)/', response.text)
    assert ids_before, "No complaints found"
    # Find the id of the newly added complaint (it should have a resolve button)
    match = re.search(r'/complaints/(\d+)/resolve', response.text)
    assert match, "Resolve button not found"
    complaint_id = int(match.group(1))
    # Resolve it
    response = client.post(f"/complaints/{complaint_id}/resolve", follow_redirects=False)
    assert response.status_code == 303
    # Get complaint ids after resolving
    response = client.get("/complaints")
    assert response.status_code == 200
    ids_after = re.findall(r'/complaints/(\d+)/', response.text)
    assert ids_after == ids_before, "Order changed after resolve"
    # Check that the resolved complaint shows "Resolved"
    assert "Resolved" in response.text

def test_reopen_complaint():
    # Post a new complaint
    response = client.post("/complaints", data={"agent_name": "ReopenTest", "text": "Reopen test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    response = client.get("/complaints")
    assert response.status_code == 200
    import re
    ids_before = re.findall(r'/complaints/(\d+)/', response.text)
    assert ids_before, "No complaints found"
    # Find the id of the newly added complaint (it should have a resolve button)
    match = re.search(r'/complaints/(\d+)/resolve', response.text)
    assert match, "Resolve button not found"
    complaint_id = int(match.group(1))
    # Resolve it first
    response = client.post(f"/complaints/{complaint_id}/resolve", follow_redirects=False)
    assert response.status_code == 303
    # Now reopen it
    response = client.post(f"/complaints/{complaint_id}/reopen", follow_redirects=False)
    assert response.status_code == 303
    # Get complaint ids after reopening
    response = client.get("/complaints")
    assert response.status_code == 200
    ids_after = re.findall(r'/complaints/(\d+)/', response.text)
    assert ids_after == ids_before, "Order changed after reopen"
    # Check that the reopened complaint shows "Open"
    assert "Open" in response.text
