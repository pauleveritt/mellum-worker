from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_complaints_endpoint():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaints():
    response = client.post("/complaints", data={"agent_name": "Test Agent", "text": "Test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    get_response = client.get("/complaints")
    assert get_response.status_code == 200
    assert "Test Agent" in get_response.text
    assert "Test complaint" in get_response.text
