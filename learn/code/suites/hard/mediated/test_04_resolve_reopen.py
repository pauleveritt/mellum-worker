"""Phase 4 — Resolve and Reopen: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

from dataclasses import fields

from starlette.testclient import TestClient
from turbohtml import parse

from app import app

client = TestClient(app)
client.__enter__()  # run any startup before the seed is read

import models  # noqa: E402
from models import Complaint  # noqa: E402

SEED = tuple(models.complaints)  # read before any test posts a complaint


def _post(name: str, text: str) -> int:
    client.post("/complaints", data={"agent_name": name, "text": text}, follow_redirects=False)
    return models.complaints[-1].id


def _complaint(complaint_id: int):
    return next(c for c in models.complaints if c.id == complaint_id)


def _status(name: str) -> str:
    """The text of the one card that shows this agent's name."""
    cards = [" ".join(c.text.split()) for c in parse(client.get("/complaints").text).select(".card")]
    matching = [t for t in cards if name in t]
    assert len(matching) == 1, f"expected one card for {name!r}, found {len(matching)}"
    return matching[0]


def _names_in_board_order(names: tuple[str, ...]) -> list[str]:
    text = " ".join(card.text for card in parse(client.get("/complaints").text).select(".card"))
    return sorted(names, key=text.index)


def test_complaint_built_directly_gets_a_new_increasing_id_and_starts_open():
    assert {"id", "status"} <= {f.name for f in fields(Complaint)}
    first = Complaint("Ada", "Built directly.")
    second = Complaint("Bo", "Built directly too.")
    assert (first.agent_name, first.text) == ("Ada", "Built directly.")
    assert isinstance(first.id, int) and isinstance(second.id, int)
    assert second.id > first.id
    assert first.id > max(c.id for c in SEED), "a new complaint's id must exceed every earlier one"
    assert first.status == "open"


def test_seeded_complaints_have_distinct_ids():
    assert len({c.id for c in SEED}) == len(SEED)


def test_posted_complaint_gets_an_id_above_every_earlier_one():
    before = max(c.id for c in models.complaints)
    assert _post("Id Check", "Numbered after the rest.") > before


def test_each_card_shows_its_state_and_a_button_posting_to_its_route():
    document = parse(client.get("/complaints").text)
    cards = document.select(".card")
    for complaint in [c for c in models.complaints if c.status in ("open", "resolved")]:
        route = "resolve" if complaint.status == "open" else "reopen"
        label = "Open" if complaint.status == "open" else "Resolved"
        matching = []
        for card in cards:
            forms = [f for f in card.select("form")
                     if (f.attr("action") or "").endswith(f"/complaints/{complaint.id}/{route}")]
            if forms:
                matching.append((card, forms[0]))
        assert matching, f"no card posts to /complaints/{complaint.id}/{route}"
        card, form = matching[0]
        assert label in " ".join(card.text.split()), f"the card for complaint {complaint.id} does not show {label}"
        assert (form.attr("method") or "").lower() == "post"
        assert any(c.tag == "button" or (c.attr("type") or "").lower() == "submit"
                   for c in form.select("button, input")), "the form has no button"


def test_resolve_marks_resolved_and_answers_303_to_the_board():
    complaint = _post("Resolve Check", "Needs resolving.")
    other = _post("Resolve Bystander", "Should not change.")
    response = client.post(f"/complaints/{complaint}/resolve", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert _complaint(complaint).status == "resolved" and _complaint(other).status == "open"
    assert "Resolved" in _status("Resolve Check")


def test_reopen_marks_open_and_answers_303_to_the_board():
    complaint = _post("Reopen Check", "Needs reopening.")
    client.post(f"/complaints/{complaint}/resolve", follow_redirects=False)
    response = client.post(f"/complaints/{complaint}/reopen", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert _complaint(complaint).status == "open"
    card = _status("Reopen Check")
    assert "Open" in card and "Resolved" not in card


def test_resolving_and_reopening_keep_the_id_and_never_reorder_the_board():
    first = _post("Order One", "First of the pair.")
    _post("Order Two", "Second of the pair.")
    names = ("Order One", "Order Two")
    before = _names_in_board_order(names)
    client.post(f"/complaints/{first}/resolve", follow_redirects=False)
    middle = _names_in_board_order(names)
    client.post(f"/complaints/{first}/reopen", follow_redirects=False)
    after = _names_in_board_order(names)
    assert before == middle == after
    assert _complaint(first).agent_name == "Order One", "resolving and reopening must keep the id"
