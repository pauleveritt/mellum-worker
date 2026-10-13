"""Phase 4 — Resolve and Reopen, as a developer on this project would test it.

Written from the Phase 4 bullets of the roadmap and tech-stack.md (TestClient,
no running server), before the phase is built. The M.11 screen hands this file
to Mellum with "make tests/test_phase4.py pass". "Never reused" is not tested:
there is no route that removes a complaint.
"""

from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app)


def board_ids():
    return [complaint.id for complaint in models.complaints]


def test_complaint_still_takes_agent_name_and_text_and_gets_an_automatic_id():
    first = models.Complaint("Aria", "The spec changed under me.")
    second = models.Complaint("Bolt", "Nobody runs my tests.")
    assert isinstance(first.id, int) and isinstance(second.id, int)
    assert first.id != second.id
    assert first.status == "open" and second.status == "open"


def test_resolve_redirects_to_the_board_and_shows_resolved_with_a_reopen_button():
    complaint = models.complaints[0]
    response = client.post(f"/complaints/{complaint.id}/resolve", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert complaint.status == "resolved"
    page = client.get("/complaints").text
    assert "Resolved" in page
    assert "Reopen" in page


def test_reopen_redirects_to_the_board_and_shows_open_with_a_resolve_button():
    complaint = models.complaints[0]
    client.post(f"/complaints/{complaint.id}/resolve")
    response = client.post(f"/complaints/{complaint.id}/reopen", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert complaint.status == "open"
    page = client.get("/complaints").text
    assert "Open" in page
    assert "Resolve" in page


def test_resolving_and_reopening_keep_the_board_order():
    before = board_ids()
    complaint = models.complaints[-1]
    client.post(f"/complaints/{complaint.id}/resolve")
    assert board_ids() == before
    client.post(f"/complaints/{complaint.id}/reopen")
    assert board_ids() == before
