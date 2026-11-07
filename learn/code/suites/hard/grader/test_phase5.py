"""Archive rejection is inert; every successful transition has exactly one audit event."""
from copy import deepcopy
from dataclasses import asdict

from turbohtml import parse

import models
from grader_tests._contract import client


def _post_new_complaint(agent_name, text):
    response = client.post("/complaints", data={"agent_name": agent_name, "text": text}, follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/complaints"
    matches = [c for c in models.complaints if c.agent_name == agent_name and c.text == text]
    assert len(matches) == 1
    return matches[0]


def _cards(text):
    return [" ".join(card.text.split()) for card in parse(text).select(".card")]


def _records():
    return deepcopy([asdict(c) for c in models.complaints])


def _transition(target, action):
    response = client.post(f"/complaints/{target.id}/{action}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"


def test_archive_only_when_resolved():
    target = _post_new_complaint("Archive rejection", "Open archive must change nothing.")
    for _ in range(2):
        before, audit = _records(), deepcopy(models.audit)
        board = _cards(client.get("/complaints").text)
        response = client.post(f"/complaints/{target.id}/archive", follow_redirects=False)
        assert response.status_code == 400
        assert _records() == before and models.audit == audit
        assert _cards(client.get("/complaints").text) == board
    _transition(target, "resolve")
    _transition(target, "archive")
    for _ in range(2):
        before, audit = _records(), deepcopy(models.audit)
        response = client.post(f"/complaints/{target.id}/archive", follow_redirects=False)
        assert response.status_code == 400
        assert _records() == before and models.audit == audit


def test_archive_hides_from_board_but_keeps_the_record():
    target = _post_new_complaint("Archivist", "Archive me after I am resolved.")
    companion = _post_new_complaint("Still visible", "Keep this resolved complaint on the board.")
    _transition(companion, "resolve")
    _transition(target, "resolve")
    before = _records()
    before_cards = _cards(client.get("/complaints").text)
    _transition(target, "archive")
    assert target.status == "archived" and target in models.complaints
    expected = deepcopy(before)
    next(row for row in expected if row["id"] == target.id)["status"] = "archived"
    assert _records() == expected
    page = client.get("/complaints")
    assert page.status_code == 200 and target.text not in page.text
    after_cards = _cards(page.text)
    assert after_cards == [card for card in before_cards if target.text not in card]
    for complaint in models.complaints:
        if complaint.status in {"open", "resolved"}:
            assert complaint.text in page.text


def test_ids_are_never_reused_after_archive():
    target = _post_new_complaint("Identity archive", "Archive before adding the next complaint.")
    _transition(target, "resolve")
    _transition(target, "archive")
    previous = [c.id for c in models.complaints]
    for index in range(3):
        added = _post_new_complaint(f"Identity {index}", f"Addition after archive {index}.")
        assert type(added.id) is int and all(type(value) is int for value in previous)
        assert added.id > max(previous)
        previous.append(added.id)
    assert len(previous) == len(set(previous))


def test_stats_open_excludes_resolved_and_archived():
    target = _post_new_complaint("Stats", "Follow open count through every state.")
    for action in (None, "resolve", "reopen", "resolve", "archive"):
        if action:
            _transition(target, action)
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert type(data["open"]) is int
        assert data["open"] == sum(c.status == "open" for c in models.complaints)


def test_audit_records_each_transition_in_order_with_monotonic_seq():
    assert isinstance(models.audit, list)
    first = _post_new_complaint("Auditor first", "Resolve reopen and archive this record.")
    second = _post_new_complaint("Auditor second", "Interleave a second record's audit event.")
    for target, action in ((first, "resolve"), (second, "resolve"), (first, "reopen"),
                           (first, "resolve"), (first, "archive")):
        before = deepcopy(models.audit)
        _transition(target, action)
        assert models.audit[:-1] == before
        assert len(models.audit) == len(before) + 1
        entry = models.audit[-1]
        assert entry["id"] == target.id and type(entry["id"]) is int
        assert entry["action"] == action
        assert type(entry["seq"]) is int
        sequences = [event["seq"] for event in models.audit]
        assert all(type(value) is int for value in sequences)
        assert all(left < right for left, right in zip(sequences, sequences[1:]))
