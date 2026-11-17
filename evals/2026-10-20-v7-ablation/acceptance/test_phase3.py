"""Mediated acceptance test for Phase 3 (add complaint), from phase-3-add.md."""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_post_returns_303_to_the_board_and_lists_the_new_complaint():
    r = client.post(
        "/complaints",
        data={"agent_name": "Zed", "text": "mediated-add-xyz"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/complaints"
    assert "mediated-add-xyz" in client.get("/complaints").text


def test_board_has_a_form_posting_to_complaints():
    text = client.get("/complaints").text.lower()
    assert "<form" in text and 'action="/complaints"' in text
    assert 'name="agent_name"' in text and 'name="text"' in text


def test_existing_pages_work():
    assert client.get("/").status_code == 200
    assert client.get("/complaints").status_code == 200
