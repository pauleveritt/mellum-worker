"""Phase 4 — Resolve and Reopen: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import functools
from urllib.parse import urlsplit

import pytest
from starlette.testclient import TestClient
from turbohtml import Element, parse


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
    response = _client().get("/complaints", follow_redirects=False)
    assert response.status_code == 200, f"GET /complaints answered {response.status_code}"
    return parse(response.text).select(".card")


def _post(name: str, text: str) -> int:
    _client().post("/complaints", data={"agent_name": name, "text": text}, follow_redirects=False)
    return _models().complaints[-1].id


def _complaint(complaint_id: int):
    return next(c for c in _models().complaints if c.id == complaint_id)


def _change(complaint_id: int, route: str):
    return _client().post(f"/complaints/{complaint_id}/{route}", follow_redirects=False)


def _card(name: str):
    matching = [card for card in _cards() if name in _words(card)]
    assert len(matching) == 1, f"expected one .card for {name!r}, found {len(matching)}"
    return matching[0]


def _on_show(element) -> bool:
    """False for anything a browser would not show: hidden itself or inside something hidden."""
    for node in (element, *element.ancestors):
        if isinstance(node, Element):
            style = "".join((node.attr("style") or "").split()).casefold()
            if "hidden" in node.attrs or "display:none" in style or "visibility:hidden" in style:
                return False
    return True


def _states(card) -> set[str]:
    """What this card's badges read; the roadmap asks for a badge reading exactly the word."""
    return {_words(badge) for badge in card.select(".badge") if _on_show(badge)} & {"Open", "Resolved"}


def _names_on_the_board(names: tuple[str, ...]) -> list[str]:
    shown = [_words(card) for card in _cards()]
    return [name for card in shown for name in names if name in card]


def _button_labels(form) -> list[str]:
    labels = []
    for control in form.select("button, input"):
        if "disabled" in control.attrs:
            continue
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


def test_direct_and_posted_complaints_share_one_rising_id_sequence():
    models = _models()
    stored = [complaint.id for complaint in models.complaints]
    built_first = models.Complaint("Built First", "Made without the form.")
    posted_first = _post("Posted First", "Made with the form.")
    built_second = models.Complaint("Built Second", "Made after the form ran.")
    posted_second = _post("Posted Second", "Made after both ways ran.")
    order = [max(stored), built_first.id, posted_first, built_second.id, posted_second]
    assert all(earlier < later for earlier, later in zip(order, order[1:])), (
        f"each new complaint's id must exceed every earlier one, however it was made: {order}")
    assert (built_first.id, built_second.id) == (order[1], order[3]), "an id changed after it was given"
    assert [complaint.id for complaint in models.complaints][:len(stored)] == stored, "an earlier id changed"


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
        assert _states(card) == {state}, f"the card for complaint {complaint.id} does not show {state}"
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
    assert _states(_card("Resolve Check")) == {"Resolved"}, "the board does not show it Resolved"
    assert _states(_card("Resolve Bystander")) == {"Open"}, "resolving changed another card"


def test_reopen_marks_it_open_and_answers_303_to_the_board():
    complaint = _post("Reopen Check", "Needs reopening.")
    _change(complaint, "resolve")
    response = _change(complaint, "reopen")
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    assert _complaint(complaint).status == "open"
    assert _states(_card("Reopen Check")) == {"Open"}, "the board does not show it Open"


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
