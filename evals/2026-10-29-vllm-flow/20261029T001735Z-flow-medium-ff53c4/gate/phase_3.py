from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_complaints_endpoint():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaints():
    response = client.post("/complaints", data={"agent_name": "Test User", "text": "Test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/complaints"

def test_complaints_include_posted():
    # Post a new complaint
    client.post("/complaints", data={"agent_name": "Test User", "text": "Test complaint"}, follow_redirects=False)
    # Get complaints page
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Test User" in response.text
    assert "Test complaint" in response.text
