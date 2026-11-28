from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_complaints_route():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text
