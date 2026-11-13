from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app)


def ids():
    return [complaint.id for complaint in models.complaints]


def test_resolve_then_reopen():
    complaint = models.complaints[0]
    before = ids()

    response = client.post(f"/complaints/{complaint.id}/resolve", follow_redirects=False)
    assert response.status_code == 303
    assert complaint.status == "resolved"
    assert ids() == before

    response = client.post(f"/complaints/{complaint.id}/reopen", follow_redirects=False)
    assert response.status_code == 303
    assert complaint.status == "open"
    assert ids() == before


def test_board_shows_badge_and_buttons():
    complaint = models.complaints[0]
    assert "Open" in client.get("/complaints").text
    client.post(f"/complaints/{complaint.id}/resolve")
    page = client.get("/complaints").text
    assert "Resolved" in page and "Reopen" in page
    client.post(f"/complaints/{complaint.id}/reopen")


def test_ids_are_unique():
    a = models.Complaint("a", "b")
    b = models.Complaint("a", "c")
    assert a.status == "open"
    assert a.id != b.id
