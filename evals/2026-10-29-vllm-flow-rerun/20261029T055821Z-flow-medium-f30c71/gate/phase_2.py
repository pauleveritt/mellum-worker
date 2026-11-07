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
