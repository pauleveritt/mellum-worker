"""Phase 5 — Archive and Audit: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

from starlette.testclient import TestClient

from app import app

client = TestClient(app)

import models  # noqa: E402
from models import Complaint  # noqa: E402


def _post(name: str, text: str) -> int:
    client.post("/complaints", data={"agent_name": name, "text": text}, follow_redirects=False)
    return models.complaints[-1].id


def _status(complaint_id: int) -> str:
    return next(c.status for c in models.complaints if c.id == complaint_id)


def _action(complaint_id: int, action: str):
    return client.post(f"/complaints/{complaint_id}/{action}", follow_redirects=False)


def _stats_match() -> bool:
    return client.get("/stats").json() == {"open": sum(1 for c in models.complaints if c.status == "open")}


def _board() -> str:
    response = client.get("/complaints")
    assert response.status_code == 200
    return response.text


def test_archive_on_a_resolved_complaint_sets_archived_and_answers_303():
    complaint = _post("Archive Ok", "Ready to go.")
    _action(complaint, "resolve")
    response = _action(complaint, "archive")
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert _status(complaint) == "archived"


def test_archive_on_an_open_complaint_answers_400_and_changes_nothing():
    complaint = _post("Archive Open", "Still open.")
    audit_before = list(models.audit)
    assert _action(complaint, "archive").status_code == 400
    assert _status(complaint) == "open"
    assert models.audit == audit_before
    assert "Archive Open" in _board()


def test_archive_on_an_already_archived_complaint_answers_400_and_changes_nothing():
    complaint = _post("Archive Twice", "Gone already.")
    _action(complaint, "resolve")
    _action(complaint, "archive")
    audit_before = list(models.audit)
    assert _action(complaint, "archive").status_code == 400
    assert _status(complaint) == "archived"
    assert models.audit == audit_before


def test_an_archived_complaint_stays_in_the_data_and_leaves_the_board_while_others_still_show():
    gone = _post("Archive Hidden", "Should leave the board.")
    resolved = _post("Archive Resolved", "Should stay visible.")
    open_one = _post("Archive Still Open", "Should stay visible too.")
    _action(gone, "resolve")
    _action(gone, "archive")
    _action(resolved, "resolve")
    board = _board()
    assert "Should leave the board." not in board
    assert "Should stay visible." in board and "Should stay visible too." in board
    assert _status(gone) == "archived", "an archived complaint must stay in models.complaints"
    assert _status(open_one) == "open" and _status(resolved) == "resolved"


def test_a_complaint_added_after_an_archive_gets_an_id_above_every_existing_one():
    archived = _post("Archive Id", "Holds the highest id.")
    _action(archived, "resolve")
    _action(archived, "archive")
    highest = max(c.id for c in models.complaints)
    new_one = _post("After Archive", "Numbered after the archived one.")
    assert new_one > highest
    assert Complaint("Direct", "Built after the archive.").id > new_one


def test_stats_answers_json_counting_only_complaints_exactly_open():
    assert client.get("/stats").status_code == 200
    assert _stats_match()
    complaint = _post("Stats Check", "Counted while open.")
    assert _stats_match()
    _action(complaint, "resolve")
    assert _stats_match()
    _action(complaint, "reopen")
    assert _stats_match()
    _action(complaint, "resolve")
    _action(complaint, "archive")
    assert _stats_match()


def test_stats_does_not_count_a_status_that_only_resembles_open():
    near = Complaint("Stats Near", "Almost open.")
    object.__setattr__(near, "status", "Open")
    models.complaints.append(near)
    try:
        assert _stats_match()
    finally:
        models.complaints.remove(near)


def test_audit_records_each_action_once_in_order_with_increasing_seq():
    assert isinstance(models.audit, list)
    first = _post("Audit One", "Goes through all three.")
    second = _post("Audit Two", "Only resolved.")
    start = len(models.audit)
    _action(first, "resolve")
    _action(first, "reopen")
    _action(second, "resolve")
    _action(first, "resolve")
    _action(first, "archive")
    entries = models.audit[start:]
    assert [(e["id"], e["action"]) for e in entries] == [
        (first, "resolve"), (first, "reopen"), (second, "resolve"), (first, "resolve"), (first, "archive")]
    for entry in models.audit:
        assert {"id", "action", "seq"} <= set(entry) and isinstance(entry["seq"], int)
    seqs = [e["seq"] for e in models.audit]
    assert all(a < b for a, b in zip(seqs, seqs[1:])), f"seq is not strictly increasing: {seqs}"
