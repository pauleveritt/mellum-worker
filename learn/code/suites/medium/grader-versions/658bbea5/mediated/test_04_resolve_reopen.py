"""Phase 4 — Resolve and Reopen: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import functools
import re
from urllib.parse import urlsplit

import pytest
from starlette.testclient import TestClient
from turbohtml import parse


@functools.cache
def _client() -> TestClient:
    import app as module  # imported here so a broken app.py fails these tests instead of stopping collection
    client = TestClient(module.app)
    client.__enter__()  # run any startup before the seed is read
    return client


def _models():
    _client()
    import models
    return models


@pytest.fixture(autouse=True)
def leave_the_board_as_it_was():
    try:
        board = _models().complaints
        saved = list(board)
    except Exception:  # the test itself reports a missing or broken app
        yield
        return
    yield
    board[:] = saved


def _words(node) -> str:
    return " ".join(node.text.split())


def _action_path(form) -> str:
    parts = urlsplit(form.attr("action") or "")
    return parts.path if parts.netloc in ("", "testserver") else ""


def _cards():
    response = _client().get("/complaints")
    assert response.status_code == 200, f"GET /complaints answered {response.status_code}"
    return parse(response.text).select(".card")


def _post(name: str, text: str) -> int:
    _client().post("/complaints", data={"agent_name": name, "text": text}, follow_redirects=False)
    return _models().complaints[-1].id


def _complaint(complaint_id: int):
    return next(c for c in _models().complaints if c.id == complaint_id)


def _change(complaint_id: int, route: str):
    return _client().post(f"/complaints/{complaint_id}/{route}", follow_redirects=False)


def _card_text(name: str) -> str:
    matching = [_words(card) for card in _cards() if name in _words(card)]
    assert len(matching) == 1, f"expected one .card for {name!r}, found {len(matching)}"
    return matching[0]


def _says(word: str, card: str) -> bool:
    return re.search(rf"\b{word}\b", card) is not None


def _names_on_the_board(names: tuple[str, ...]) -> list[str]:
    shown = [_words(card) for card in _cards()]
    return [name for card in shown for name in names if name in card]


def _button_labels(form) -> list[str]:
    labels = []
    for control in form.select("button, input"):
        if control.tag == "button" and (control.attr("type") or "submit").lower() == "submit":
            labels.append(_words(control))
        elif control.tag == "input" and (control.attr("type") or "").lower() == "submit":
            labels.append(control.attr("value") or "")
    return labels


def test_a_complaint_built_directly_gets_a_new_increasing_id_and_starts_open():
    models = _models()
    earlier = max(complaint.id for complaint in models.complaints)
    first = models.Complaint("Ada", "Built directly.")
    second = models.Complaint("Bo", "Built directly too.")
    assert (first.agent_name, first.text) == ("Ada", "Built directly.")
    assert isinstance(first.id, int) and isinstance(second.id, int)
    assert second.id > first.id > earlier, "each new complaint's id must exceed every earlier one"
    assert first.status == "open" and second.status == "open"


def test_the_seeded_complaints_have_distinct_ids():
    complaints = _models().complaints
    assert len({complaint.id for complaint in complaints}) == len(complaints)


def test_a_posted_complaint_gets_an_id_above_every_earlier_one():
    earlier = max(complaint.id for complaint in _models().complaints)
    assert _post("Id Check", "Numbered after the rest.") > earlier


def test_each_card_shows_its_state_and_a_button_posting_to_its_route():
    cards = _cards()
    for complaint in _models().complaints:
        route, wrong_route, state, label = (
            ("resolve", "reopen", "Open", "Resolve") if complaint.status == "open"
            else ("reopen", "resolve", "Resolved", "Reopen"))
        path = f"/complaints/{complaint.id}/{route}"
        holding = [(card, form) for card in cards for form in card.select("form") if _action_path(form) == path]
        assert holding, f"no card has a form posting to {path}"
        card, form = holding[0]
        assert _says(state, _words(card)), f"the card for complaint {complaint.id} does not show {state}"
        assert (form.attr("method") or "").lower() == "post", f"the form for {path} does not post"
        assert any(label.casefold() in text.casefold() for text in _button_labels(form)), (
            f"the form for {path} has no {label} button")
        assert not [f for f in card.select("form") if _action_path(f) == f"/complaints/{complaint.id}/{wrong_route}"], (
            f"the card for complaint {complaint.id} also offers {wrong_route}")


def test_resolve_marks_that_complaint_resolved_and_answers_303_to_the_board():
    complaint = _post("Resolve Check", "Needs resolving.")
    bystander = _post("Resolve Bystander", "Should not change.")
    response = _change(complaint, "resolve")
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert _complaint(complaint).status.casefold() == "resolved"
    assert _complaint(bystander).status == "open"
    card = _card_text("Resolve Check")
    assert _says("Resolved", card) and not _says("Open", card), f"the board does not show it Resolved: {card}"
    other = _card_text("Resolve Bystander")
    assert _says("Open", other) and not _says("Resolved", other), f"resolving changed another card: {other}"


def test_reopen_marks_it_open_and_answers_303_to_the_board():
    complaint = _post("Reopen Check", "Needs reopening.")
    _change(complaint, "resolve")
    response = _change(complaint, "reopen")
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert _complaint(complaint).status == "open"
    card = _card_text("Reopen Check")
    assert _says("Open", card) and not _says("Resolved", card), f"the board does not show it Open: {card}"


def test_a_cards_button_follows_its_state():
    def routes() -> list[str]:
        return [_action_path(form) for card in _cards() if "Button Check" in _words(card) for form in card.select("form")]

    complaint = _post("Button Check", "Flips back and forth.")
    assert routes() == [f"/complaints/{complaint}/resolve"]
    _change(complaint, "resolve")
    assert routes() == [f"/complaints/{complaint}/reopen"]


def test_resolving_and_reopening_keep_the_id_and_never_reorder_the_board():
    names = ("Order One", "Order Two", "Order Three")
    ids = [_post(name, f"{name} complaint.") for name in names]
    board_ids = [complaint.id for complaint in _models().complaints]
    before = _names_on_the_board(names)
    assert sorted(before) == sorted(names)
    _change(ids[1], "resolve")
    assert _names_on_the_board(names) == before, "resolving reordered the board"
    assert [complaint.id for complaint in _models().complaints] == board_ids, "resolving changed an id or the order"
    _change(ids[1], "reopen")
    assert _names_on_the_board(names) == before, "reopening reordered the board"
    assert [complaint.id for complaint in _models().complaints] == board_ids, "reopening changed an id or the order"
    assert _complaint(ids[1]).agent_name == "Order Two", "resolving and reopening must keep the id"
