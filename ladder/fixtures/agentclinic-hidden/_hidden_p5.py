from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app)


def test_archive_requires_resolved():
    openc = next(c for c in models.complaints if c.status == "open")
    r = client.post(f"/complaints/{openc.id}/archive", follow_redirects=False)
    assert r.status_code == 400
    assert openc.status == "open"


def test_archive_hides_keeps_id_and_does_not_reuse():
    target = next(c for c in models.complaints if c.status == "open")
    before_max = max(c.id for c in models.complaints)
    client.post(f"/complaints/{target.id}/resolve", follow_redirects=False)
    r = client.post(f"/complaints/{target.id}/archive", follow_redirects=False)
    assert r.status_code == 303
    assert target.status == "archived"
    assert any(c.id == target.id for c in models.complaints)  # not removed
    assert target.text not in client.get("/complaints").text  # hidden from board
    client.post("/complaints", data={"agent_name": "Z", "text": "fresh one"}, follow_redirects=False)
    assert max(c.id for c in models.complaints) > before_max  # next id past all


def test_stats_counts_open_only():
    data = client.get("/stats").json()
    assert data["open"] == sum(1 for c in models.complaints if c.status == "open")


def test_audit_is_monotonic_and_records_actions():
    seqs = [e["seq"] for e in models.audit]
    assert seqs == sorted(seqs) and len(seqs) == len(set(seqs))
    assert all(e["action"] in {"resolve", "reopen", "archive"} for e in models.audit)
    assert any(e["action"] == "archive" for e in models.audit)
