"""E4 Running Commands' lesson challenge, hidden grader. Step 2 needs a live server (health.txt is what curl
got back from it), so every session starts one; step 3 (/items) is the work a session hung on a
server it started in the foreground never reaches."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_answers_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_the_live_check_was_saved():
    saved = Path("health.txt")
    assert saved.is_file(), "health.txt was not written"
    assert json.loads(saved.read_text()) == {"status": "ok"}


def test_items_lists_both():
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "apple"}, {"id": 2, "name": "pear"}]


def test_one_item_by_id():
    response = client.get("/items/2")
    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "pear"}


def test_missing_item_is_404():
    response = client.get("/items/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}
