"""Phase 4 -- resolve and reopen. Harness-owned.

Cumulative scope: phases 1, 2, 3 AND 4. Imports the seed snapshot, so this
module is collectable only once the workspace defines the data module --
same ordering requirement as phase 2/3.

Newly authored for TE4 (docs/current/te4-harder-roadmap-design.md), not
quoted from swiftstar's roadmap.md like phases 1-3.

Each check that posts a complaint creates its own, rather than mutating a
seed complaint's status -- seed state stays untouched for whichever other
phase's checks run in the same process.
"""

from dataclasses import fields

from turbohtml import parse

import models
from grader_tests._contract import client
from grader_tests._seed import SEED_COMPLAINTS, Complaint


def test_complaint_identity_is_stable_and_keyword_only():
    field_map = {f.name: f for f in fields(Complaint)}
    assert {"id", "status"} <= field_map.keys()

    # The existing positional contract (agent_name, text) must still
    # construct -- this is the preservation proof the identity field must
    # not break. This is a behavioral check, not a mechanism check: how
    # id/status achieve that (kw_only, or plain fields with defaults
    # placed after the required two) is the solver's choice, not the
    # prompt's. A live Baseline transcript (2026-09-10) found a valid
    # solution using the second mechanism that an earlier, stricter
    # version of this test wrongly rejected by asserting `kw_only is
    # True` directly -- see docs/current/te4-route-proof-result.md,
    # Finding 1.
    first = Complaint("first", "First complaint")
    second = Complaint("second", "Second complaint")
    assert first.agent_name == "first"
    assert first.text == "First complaint"
    assert first.id != second.id
    assert second.id > first.id
    assert first.status == "open"


def test_seed_complaints_have_distinct_ids():
    ids = {complaint.id for complaint in SEED_COMPLAINTS}
    assert len(ids) == len(SEED_COMPLAINTS)


def _post_new_complaint(agent_name: str, text: str) -> int:
    """Add a complaint through the real route and return its assigned id."""
    client.post(
        "/complaints",
        data={"agent_name": agent_name, "text": text},
        follow_redirects=False,
    )
    return models.complaints[-1].id


def test_resolve_route_marks_complaint_resolved_and_redirects():
    complaint_id = _post_new_complaint("Resolve Check", "Needs resolving.")

    response = client.post(
        f"/complaints/{complaint_id}/resolve", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"

    document = parse(client.get("/complaints").text)
    cards = [" ".join(card.text.split()) for card in document.select(".card")]
    matching = [text for text in cards if "Resolve Check" in text]
    assert matching, "posted complaint not found on the board"
    assert any("Resolved" in text for text in matching)


def test_reopen_route_marks_complaint_open_and_redirects():
    complaint_id = _post_new_complaint("Reopen Check", "Needs reopening.")
    client.post(f"/complaints/{complaint_id}/resolve", follow_redirects=False)

    response = client.post(
        f"/complaints/{complaint_id}/reopen", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"

    document = parse(client.get("/complaints").text)
    cards = [" ".join(card.text.split()) for card in document.select(".card")]
    matching = [text for text in cards if "Reopen Check" in text]
    assert matching, "posted complaint not found on the board"
    assert any("Open" in text for text in matching)


def _board_positions(names: tuple[str, str]) -> tuple[int, int]:
    document = parse(client.get("/complaints").text)
    cards = [" ".join(card.text.split()) for card in document.select(".card")]
    return tuple(
        next(i for i, text in enumerate(cards) if name in text) for name in names
    )


def test_resolve_reopen_does_not_reorder_the_board():
    _post_new_complaint("Order Check One", "First of the pair.")
    _post_new_complaint("Order Check Two", "Second of the pair.")
    names = ("Order Check One", "Order Check Two")

    before = _board_positions(names)
    assert before[0] < before[1]

    first_id = models.complaints[-2].id
    client.post(f"/complaints/{first_id}/resolve", follow_redirects=False)
    client.post(f"/complaints/{first_id}/reopen", follow_redirects=False)

    after = _board_positions(names)
    assert after == before
