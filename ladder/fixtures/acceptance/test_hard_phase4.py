"""Mediated acceptance test for the hard suite, phase 4 (resolve / reopen),
written from prompts/04.md as a superset of the hidden
grader/test_phase4_resolve_reopen.py. It pins the oracle's checks and adds the
spec items it leaves thin: the status badge reading Open / Resolved and the
Resolve / Reopen action forms on the board.

The load-bearing one is the deep Phase-4 invariant: the complaint id is an
AUTOMATIC default on the dataclass, so two direct constructions get distinct
ids and a default status of open. An id assigned only in the add route passes
the happy path and fails right here.

Phase 4 cumulative: it imports models and app. Placed outside the worker write
scope and restored before every attempt, so the worker may read and run it but
cannot weaken it. Robust to shared module state: every mutating check reads a
count or id list before its change and asserts the delta, never an absolute
total, and never assumes a seed sits at a particular id.
"""
import models
from app import app
from starlette.testclient import TestClient

client = TestClient(app, follow_redirects=False)


# ---- the deep invariant: id is an automatic default ON the dataclass -------
def test_direct_construction_gives_distinct_auto_ids_and_open_status():
    a = models.Complaint("x", "first")
    b = models.Complaint("x", "second")
    assert a.status == "open" and b.status == "open"
    assert isinstance(a.id, int) and isinstance(b.id, int)
    assert a.id != b.id


def test_positional_construction_still_works():
    c = models.Complaint("tester", "a gripe")
    assert c.agent_name == "tester" and c.text == "a gripe"


def test_seed_complaints_have_distinct_ids():
    ids = [c.id for c in models.complaints]
    assert len(set(ids)) == len(ids)


# ---- resolve / reopen routes ----------------------------------------------
def _add(agent_name: str, text: str) -> int:
    client.post("/complaints", data={"agent_name": agent_name, "text": text})
    return models.complaints[-1].id


def test_resolve_sets_resolved_and_redirects_303():
    cid = _add("Resolve Check", "needs resolving")
    r = client.post(f"/complaints/{cid}/resolve")
    assert r.status_code == 303 and r.headers["location"] == "/complaints"
    target = next(c for c in models.complaints if c.id == cid)
    assert target.status == "resolved"
    assert "Resolved" in client.get("/complaints").text


def test_reopen_sets_open_and_redirects_303():
    cid = _add("Reopen Check", "needs reopening")
    client.post(f"/complaints/{cid}/resolve")
    r = client.post(f"/complaints/{cid}/reopen")
    assert r.status_code == 303 and r.headers["location"] == "/complaints"
    target = next(c for c in models.complaints if c.id == cid)
    assert target.status == "open"


def test_resolve_reopen_keeps_board_order():
    before = [c.id for c in models.complaints]
    cid = before[0]
    client.post(f"/complaints/{cid}/resolve")
    client.post(f"/complaints/{cid}/reopen")
    assert [c.id for c in models.complaints] == before


# ---- spec items the oracle leaves thin: the badge and the action forms -----
def test_board_shows_status_badge_and_action_forms():
    body = client.get("/complaints").text
    assert ">Open<" in body or ">Resolved<" in body
    low = body.lower()
    assert "/resolve" in low or "/reopen" in low
    assert 'method="post"' in low
