"""Mediated acceptance test for Phase 2 (complaints board), from phase-2-board.md."""
from datetime import datetime

from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app)


def test_board_returns_200_and_the_seeded_complaint():
    r = client.get("/complaints")
    assert r.status_code == 200
    assert "Scope creep never ends." in r.text


def test_complaints_seeded_three_to_five_with_fields():
    assert 3 <= len(models.complaints) <= 5
    c = models.Complaint("Aria", "something")
    assert c.agent_name == "Aria" and c.text == "something"
    assert isinstance(c.timestamp, datetime)


def test_board_lists_every_seeded_complaint():
    text = client.get("/complaints").text
    for c in models.complaints:
        assert c.text in text and c.agent_name in text


def test_home_still_works():
    assert client.get("/").status_code == 200
