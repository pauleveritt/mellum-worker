"""Mediated acceptance test for the medium suite (phases 1-4), written from the
full spec (prompts 01-04), not from the grader. A superset of the hidden oracle:
it pins the same contracts and adds the ones the oracle leaves thin — most of all
the Phase-4 invariant that the complaint id is an automatic default ON the
dataclass (two direct constructions get distinct ids), which an id assigned only
in the add-route passes on the happy path and fails here. Placed outside the
workspace and run by the verify gate (VERIFY_TEST) with PYTHONPATH=cwd.

Robust to shared module state: every mutating check reads a COUNT/ID list before
its change and asserts the delta, never an absolute total, and never assumes a
seed sits at a particular id."""
from datetime import datetime

from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app, follow_redirects=False)


# ---- Phase 1: home page + base layout -------------------------------------
def test_home_renders_the_tagline_and_base_layout():
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "Come in. Sit down. Tell us about your human." in body
    low = body.lower()
    assert "<!doctype html" in low
    assert 'lang="en"' in low
    assert "AgentClinic" in body
    assert 'href="/"' in body and 'href="/complaints"' in body


# ---- Phase 2: complaints board -------------------------------------------
def test_board_lists_seed_complaints_with_name_date_and_text():
    r = client.get("/complaints")
    assert r.status_code == 200
    body = r.text
    assert "Scope creep never ends." in body
    seed = models.complaints[0]
    assert seed.agent_name in body
    assert seed.timestamp.strftime("%Y-%m-%d") in body


def test_complaint_dataclass_carries_the_spec_fields():
    c = models.Complaint("tester", "a gripe")
    assert c.agent_name == "tester" and c.text == "a gripe"
    assert isinstance(c.timestamp, datetime)


# ---- Phase 3: add complaint ----------------------------------------------
def test_add_complaint_redirects_303_to_the_board_and_appears():
    before = len(models.complaints)
    r = client.post("/complaints", data={"agent_name": "Zed", "text": "a brand new gripe"})
    assert r.status_code == 303
    assert r.headers["location"] == "/complaints"
    assert len(models.complaints) == before + 1
    assert "a brand new gripe" in client.get("/complaints").text


def test_add_form_posts_to_complaints_with_the_named_fields():
    body = client.get("/complaints").text.lower()
    assert 'action="/complaints"' in body
    assert 'method="post"' in body
    assert 'name="agent_name"' in body and 'name="text"' in body


# ---- Phase 4: resolve / reopen (the deep contract) ------------------------
def test_new_complaints_default_open_with_distinct_auto_ids():
    # The id must be an AUTOMATIC default on the dataclass, so constructing a
    # Complaint directly (not through the add route) still gives a unique id and
    # a default status of "open". An id assigned in the route fails right here.
    a = models.Complaint("x", "first")
    b = models.Complaint("x", "second")
    assert a.status == "open" and b.status == "open"
    assert isinstance(a.id, int) and isinstance(b.id, int)
    assert a.id != b.id


def test_resolve_then_reopen_sets_status_303_and_keeps_order():
    target = models.complaints[0]
    before = [c.id for c in models.complaints]

    r = client.post(f"/complaints/{target.id}/resolve")
    assert r.status_code == 303 and r.headers["location"] == "/complaints"
    assert target.status == "resolved"
    assert "Resolved" in client.get("/complaints").text

    r = client.post(f"/complaints/{target.id}/reopen")
    assert r.status_code == 303
    assert target.status == "open"

    assert [c.id for c in models.complaints] == before  # order and ids unchanged


def test_board_shows_status_badge_and_the_action_forms():
    body = client.get("/complaints").text
    assert ">Open<" in body or ">Resolved<" in body
    assert "/resolve" in body or "/reopen" in body
