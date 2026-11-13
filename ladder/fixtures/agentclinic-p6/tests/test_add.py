from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_post_redirects_to_board():
    response = client.post(
        "/complaints",
        data={"agent_name": "Eve", "text": "Too many meetings."},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"


def test_new_complaint_is_listed():
    client.post(
        "/complaints", data={"agent_name": "Finn", "text": "Nobody reads my logs."}
    )
    assert "Nobody reads my logs." in client.get("/complaints").text
