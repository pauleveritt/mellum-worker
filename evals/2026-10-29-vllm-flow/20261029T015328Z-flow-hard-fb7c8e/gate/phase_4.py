from fastapi import FastAPI
from starlette.testclient import TestClient
from app import app

client = TestClient(app)

def test_get_complaints_returns_200_and_contains_seed_complaint():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaints_redirects_to_complaints_page():
    response = client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"

def test_post_complaints_adds_complaint_and_is_visible_on_get():
    client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"}, follow_redirects=False)
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "TestAgent" in response.text
    assert "Test complaint" in response.text

def test_resolve_complaint_changes_status_and_redirects():
    response = client.post("/complaints/1/resolve", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Resolved" in response.text
    assert 'action="/complaints/1/reopen"' in response.text

def test_reopen_complaint_changes_status_back_and_redirects():
    client.post("/complaints/1/resolve", follow_redirects=False)
    response = client.post("/complaints/1/reopen", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Open" in response.text
    assert 'action="/complaints/1/resolve"' in response.text

def test_complaint_order_unchanged_after_resolve():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text
    client.post("/complaints/1/resolve", follow_redirects=False)
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text
    assert "Resolved" in response.text
