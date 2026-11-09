"""Phase 3 — Add Complaint: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

from starlette.testclient import TestClient
from turbohtml import parse

from app import app
import models

client = TestClient(app)


def _is_add_form(node) -> bool:
    return (node.tag == "form" and (node.attr("method") or "").lower() == "post"
            and node.attr("action") in {None, "", "/complaints"}
            and node.select_one('[name="agent_name"]') is not None)


def _add_form(document):
    forms = [f for f in document.select("form") if _is_add_form(f)]
    assert forms, "no form that posts agent_name to /complaints"
    return forms[-1]


def test_board_ends_with_a_form_posting_name_and_text():
    document = parse(client.get("/complaints").text)
    form = _add_form(document)
    name = form.select_one('input[name="agent_name"]')
    assert name is not None and (name.attr("type") or "text").lower() == "text"
    assert form.select_one('textarea[name="text"]') is not None
    controls = form.select("button, input")
    assert any(
        (c.tag == "button" and (c.attr("type") or "submit").lower() == "submit")
        or (c.tag == "input" and (c.attr("type") or "").lower() == "submit")
        for c in controls
    ), "the form has no submit control"


def test_the_form_comes_after_every_complaint_on_the_board():
    document = parse(client.get("/complaints").text)
    order = document.select(".card, form")
    forms = [i for i, node in enumerate(order) if _is_add_form(node)]
    assert forms, "no form that posts agent_name to /complaints"
    last_card = max(i for i, node in enumerate(order) if node.tag != "form"
                    and any(c.text in " ".join(node.text.split()) for c in models.complaints))
    assert forms[-1] > last_card, "the form is not at the end of the board"


def test_post_answers_303_to_the_board():
    response = client.post("/complaints", data={"agent_name": "Poster", "text": "Posted once."},
                           follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"


def test_post_appends_the_complaint():
    before = len(models.complaints)
    client.post("/complaints", data={"agent_name": "Appender", "text": "Added at the end."},
                follow_redirects=False)
    assert len(models.complaints) == before + 1
    newest = models.complaints[-1]
    assert (newest.agent_name, newest.text) == ("Appender", "Added at the end.")


def test_posted_complaint_appears_on_the_next_board():
    name, text = "Mediated Agent", "The brief changed after the build."
    client.post("/complaints", data={"agent_name": name, "text": text}, follow_redirects=False)
    response = client.get("/complaints")
    assert response.status_code == 200
    assert name in response.text and text in response.text
