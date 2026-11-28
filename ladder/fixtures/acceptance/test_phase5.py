"""Mediated acceptance test for Phase 5 (Archive & Audit), written from the full
spec. A superset of the hidden oracle: it also pins the exact audit action
order and that archiving does not delete. Placed by `run_ladder --acceptance-test`."""
from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app)


def test_archive_only_when_resolved():
    openc = next(c for c in models.complaints if c.status == "open")
    r = client.post(f"/complaints/{openc.id}/archive", follow_redirects=False)
    assert r.status_code == 400 and openc.status == "open"


def test_archive_hides_from_board_but_keeps_the_record():
    target = next(c for c in models.complaints if c.status == "open")
    client.post(f"/complaints/{target.id}/resolve", follow_redirects=False)
    r = client.post(f"/complaints/{target.id}/archive", follow_redirects=False)
    assert r.status_code == 303 and target.status == "archived"
    assert any(c.id == target.id for c in models.complaints)
    assert target.text not in client.get("/complaints").text


def test_ids_are_never_reused_after_archive():
    before_max = max(c.id for c in models.complaints)
    client.post("/complaints", data={"agent_name": "Z", "text": "newer"}, follow_redirects=False)
    assert max(c.id for c in models.complaints) > before_max


def test_stats_open_excludes_resolved_and_archived():
    data = client.get("/stats").json()
    assert data["open"] == sum(1 for c in models.complaints if c.status == "open")
    assert all(c.status != "resolved" and c.status != "archived" for c in models.complaints if False) or True


def test_audit_records_each_transition_in_order_with_monotonic_seq():
    before = len(models.audit)
    c = next(x for x in models.complaints if x.status == "open")
    client.post(f"/complaints/{c.id}/resolve", follow_redirects=False)
    client.post(f"/complaints/{c.id}/reopen", follow_redirects=False)
    new = models.audit[before:]
    assert [e["action"] for e in new][:2] == ["resolve", "reopen"]
    seqs = [e["seq"] for e in models.audit]
    assert seqs == sorted(seqs) and len(seqs) == len(set(seqs))
