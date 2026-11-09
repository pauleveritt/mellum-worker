"""Phase 3 — Add Complaint: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import functools
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


def _document():
    response = _client().get("/complaints", follow_redirects=False)
    assert response.status_code == 200, f"GET /complaints answered {response.status_code}"
    return parse(response.text)


def _words(node) -> str:
    return " ".join(node.text.split())


def _posts_to_the_board(form) -> bool:
    action = form.attr("action")
    parts = urlsplit(action or "")
    goes_to_the_board = not action or (parts.netloc in ("", "testserver") and parts.path == "/complaints")
    return (form.attr("method") or "").lower() == "post" and goes_to_the_board


def _is_add_form(node) -> bool:
    return node.tag == "form" and _posts_to_the_board(node) and node.select_one('[name="agent_name"]') is not None


def _add_form(document):
    forms = [form for form in document.select("form") if _is_add_form(form)]
    assert forms, "no form that posts agent_name to /complaints"
    return forms[-1]


def _usable(control) -> bool:
    """A control a person can fill in: not disabled, read-only or hidden, nor in a disabled fieldset."""
    if any(word in control.attrs for word in ("disabled", "readonly", "hidden")):
        return False
    return not any(getattr(node, "tag", None) == "fieldset" and "disabled" in node.attrs for node in control.ancestors)


def _post(name: str, text: str):
    return _client().post("/complaints", data={"agent_name": name, "text": text}, follow_redirects=False)


def test_the_form_has_a_name_input_a_text_area_and_a_submit_control():
    form = _add_form(_document())
    name = form.select_one('input[name="agent_name"]')
    assert name is not None and (name.attr("type") or "text").lower() == "text", "no agent_name text input"
    text = form.select_one('textarea[name="text"]')
    assert text is not None, "no text textarea"
    assert _usable(name) and _usable(text), "the form's fields must accept input"
    assert any(
        _usable(control) and (
            (control.tag == "button" and (control.attr("type") or "submit").lower() == "submit")
            or (control.tag == "input" and (control.attr("type") or "").lower() == "submit"))
        for control in form.select("button, input")
    ), "the form has no usable submit control"


def test_the_board_ends_with_the_form_after_every_complaint():
    complaints = _models().complaints
    order = _document().select(".card, form")
    forms = [index for index, node in enumerate(order) if _is_add_form(node)]
    assert forms, "no form that posts agent_name to /complaints"
    cards = [index for index, node in enumerate(order)
             if node.tag != "form" and any(complaint.text in _words(node) for complaint in complaints)]
    assert cards, "no card shows a complaint"
    assert forms[-1] > max(cards), "the form is not at the end of the board"


def test_post_answers_303_to_the_board():
    response = _post("Poster", "Posted once.")
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"


def test_post_appends_the_complaint():
    models = _models()
    before = len(models.complaints)
    _post("Appender", "Added at the end.")
    assert len(models.complaints) == before + 1
    newest = models.complaints[-1]
    assert isinstance(newest, models.Complaint)
    assert (newest.agent_name, newest.text) == ("Appender", "Added at the end.")


def test_the_posted_complaint_appears_on_the_next_board():
    name, text = "Mediated Agent", "The brief changed after the build."
    _post(name, text)
    assert any(name in _words(card) and text in _words(card) for card in _document().select(".card")), (
        "the posted complaint is not a .card on the board")
