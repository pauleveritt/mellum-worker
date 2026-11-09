"""Phase 2 — Complaints Board: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import dataclasses
import functools
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import nodes
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from turbohtml import Doctype, parse


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


def _board():
    response = _client().get("/complaints")
    assert response.status_code == 200, f"GET /complaints answered {response.status_code}"
    return response.text, parse(response.text)


def _words(node) -> str:
    return " ".join(node.text.split())


def _cards() -> list[str]:
    return [_words(card) for card in _board()[1].select(".card")]


def _shows_the_date(card: str, stamp: datetime) -> bool:
    def number(value: int, width: int = 1) -> bool:
        return re.search(rf"(?<!\d)0*{value:0{width}d}(?!\d)", card) is not None

    named_month = re.search(rf"\b({stamp.strftime('%B')}|{stamp.strftime('%b')})\b", card) is not None
    return number(stamp.year, 4) and number(stamp.day) and (number(stamp.month) or named_month)


def _link_path(href: str | None) -> str | None:
    parts = urlsplit(href or "")
    if parts.netloc not in ("", "testserver") or not (parts.path or parts.netloc):
        return None
    return parts.path or "/"


def test_board_answers_200_with_its_heading():
    _, document = _board()
    headings = document.select("h1, h2, h3, h4, h5, h6, [role=heading]")
    assert any("Complaints Board" in _words(heading) for heading in headings), "no heading reads Complaints Board"


def test_board_keeps_the_shared_layout():
    text, document = _board()
    assert text.lstrip().lower().startswith("<!doctype html>")
    assert any(isinstance(node, Doctype) and node.name.casefold() == "html" for node in document.children)
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"
    navbars = document.select("nav, .navbar")
    assert navbars, "the page has no navbar"
    for navbar in navbars:
        links = [(_words(a).casefold(), _link_path(a.attr("href"))) for a in navbar.select("a")]
        if "AgentClinic" in _words(navbar) and ("home", "/") in links and ("complaints", "/complaints") in links:
            return
    raise AssertionError("no navbar shows AgentClinic and links Home to / and Complaints to /complaints")


def test_board_is_rendered_from_complaints_html_which_extends_base_html():
    import app as module
    root = Path(module.__file__).resolve().parent / "templates"
    environment = Jinja2Templates(directory=str(root)).env
    extends = list(environment.parse((root / "complaints.html").read_text()).find_all(nodes.Extends))
    assert extends and isinstance(extends[0].template, nodes.Const) and extends[0].template.value == "base.html"


def test_complaint_constructs_positionally_with_its_own_aware_timestamp():
    Complaint = _models().Complaint
    assert dataclasses.is_dataclass(Complaint)
    first = Complaint("Ada", "The tests keep moving.")
    second = Complaint("Bo", "Nobody reads the logs.")
    assert (first.agent_name, first.text) == ("Ada", "The tests keep moving.")
    assert (second.agent_name, second.text) == ("Bo", "Nobody reads the logs.")
    assert isinstance(first.timestamp, datetime)
    assert first.timestamp is not second.timestamp, "each complaint needs its own timestamp"
    assert first.timestamp.utcoffset() is not None, "the timestamp must be timezone-aware"


def test_the_seed_is_a_module_level_list_of_three_to_five_with_scope_creep():
    models = _models()
    assert isinstance(models.complaints, list)
    assert 3 <= len(models.complaints) <= 5
    assert all(isinstance(complaint, models.Complaint) for complaint in models.complaints)
    assert any(complaint.text == "Scope creep never ends." for complaint in models.complaints)


def test_each_complaint_is_one_card_with_its_name_text_and_date():
    complaints = _models().complaints
    cards = _cards()
    for complaint in complaints:
        matching = [card for card in cards if complaint.agent_name in card and complaint.text in card]
        same = sum(1 for other in complaints if (other.agent_name, other.text) == (complaint.agent_name, complaint.text))
        assert len(matching) == same, f"expected one .card for {complaint.agent_name!r}, found {len(matching)}"
        assert any(_shows_the_date(card, complaint.timestamp) for card in matching), (
            f"the card for {complaint.agent_name!r} does not show its year, month and day")
