from fastapi import FastAPI
from starlette.testclient import TestClient
from app import app

def test_get_complaints_returns_200_and_contains_seed_complaint():
    client = TestClient(app)
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaints_returns_303_and_redirects():
    client = TestClient(app, follow_redirects=False)
    response = client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"})
    assert response.status_code == 303
    assert response.headers["Location"] == "/complaints"

def test_post_complaints_adds_complaint_to_board():
    client = TestClient(app)
    post_client = TestClient(app, follow_redirects=False)
    post_response = post_client.post("/complaints", data={"agent_name": "TestAgentPost", "text": "Test complaint post"})
    assert post_response.status_code == 303
    assert post_response.headers["Location"] == "/complaints"
    get_response = client.get("/complaints")
    assert get_response.status_code == 200
    assert "TestAgentPost" in get_response.text
    assert "Test complaint post" in get_response.text
