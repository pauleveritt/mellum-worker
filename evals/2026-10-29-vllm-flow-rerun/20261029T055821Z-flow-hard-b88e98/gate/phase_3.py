from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text

def test_complaints_page():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaint_redirects():
    response = client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/complaints"

def test_post_complaint_appears_on_page():
    # Post a new complaint
    client.post("/complaints", data={"agent_name": "TestAgent2", "text": "Test complaint 2"}, follow_redirects=False)
    # Get complaints page
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "TestAgent2" in response.text
    assert "Test complaint 2" in response.text
