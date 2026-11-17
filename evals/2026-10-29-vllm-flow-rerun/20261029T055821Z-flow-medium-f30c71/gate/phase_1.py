from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text
    assert response.text.startswith("<!DOCTYPE html>")
    assert 'lang="en"' in response.text
    assert 'href="/"' in response.text
    assert 'href="/complaints"' in response.text
    assert "AgentClinic" in response.text
