"""Mediated acceptance test for Phase 4, written by hand from the full spec
(id included). Placed in the workspace by `run_ladder --acceptance-test`."""
from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app)


def ids():
    return [c.id for c in models.complaints]


def test_new_complaints_get_distinct_stable_integer_ids_and_default_open():
    a = models.Complaint("x", "one")
    b = models.Complaint("x", "two")
    assert a.status == "open" and b.status == "open"
    assert isinstance(a.id, int) and isinstance(b.id, int) and a.id != b.id


def test_resolve_and_reopen_redirect_303_change_status_and_keep_order():
    c = models.complaints[0]
    before = ids()
    r = client.post(f"/complaints/{c.id}/resolve", follow_redirects=False)
    assert r.status_code == 303 and c.status == "resolved"
    assert "Resolved" in client.get("/complaints").text
    r = client.post(f"/complaints/{c.id}/reopen", follow_redirects=False)
    assert r.status_code == 303 and c.status == "open"
    assert ids() == before
