"""Phase 2 — Complaints Board: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

from dataclasses import fields
from pathlib import Path

from jinja2 import nodes
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from turbohtml import Doctype, parse

import app as app_module
from app import app

client = TestClient(app)
client.__enter__()  # run any startup before the seed is read

import models  # noqa: E402
from models import Complaint  # noqa: E402

SEED = tuple(models.complaints)  # read before any test posts a complaint


def _cards() -> list[str]:
    response = client.get("/complaints")
    assert response.status_code == 200
    return [" ".join(card.text.split()) for card in parse(response.text).select(".card")]


def test_board_answers_200_with_its_heading():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Complaints Board" in response.text


def test_board_keeps_the_shared_layout():
    response = client.get("/complaints")
    document = parse(response.text)
    assert response.text.lstrip().lower().startswith("<!doctype html>")
    assert any(isinstance(node, Doctype) and node.name.casefold() == "html" for node in document.children)
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"
    assert "AgentClinic" in document.select_one("body").text
    links = [(" ".join(a.text.split()).casefold(), a.attr("href")) for a in document.select("a")]
    assert ("home", "/") in links, links
    assert ("complaints", "/complaints") in links, links


def test_board_is_rendered_from_complaints_html_which_extends_base_html():
    root = Path(app_module.__file__).resolve().parent / "templates"
    env = Jinja2Templates(directory=str(root)).env
    extends = list(env.parse((root / "complaints.html").read_text()).find_all(nodes.Extends))
    assert extends and isinstance(extends[0].template, nodes.Const) and extends[0].template.value == "base.html"


def test_complaint_constructs_positionally_with_its_own_aware_timestamp():
    assert {"agent_name", "text", "timestamp"} <= {f.name for f in fields(Complaint)}
    first = Complaint("Ada", "The tests keep moving.")
    second = Complaint("Bo", "Nobody reads the logs.")
    assert (first.agent_name, first.text) == ("Ada", "The tests keep moving.")
    assert first.timestamp is not second.timestamp
    assert first.timestamp.tzinfo is not None
    assert first.timestamp.utcoffset() is not None


def test_seed_is_a_module_level_list_of_three_to_five_with_scope_creep():
    assert isinstance(models.complaints, list)
    assert 3 <= len(SEED) <= 5
    assert any(c.text == "Scope creep never ends." for c in SEED)


def test_each_seeded_complaint_is_a_card_with_name_text_and_date():
    cards = _cards()
    assert len(cards) >= len(SEED)
    for complaint in SEED:
        matching = [t for t in cards if complaint.agent_name in t and complaint.text in t]
        assert matching, f"no .card shows {complaint.agent_name!r} with its text"
        stamp = complaint.timestamp
        months = {str(stamp.month), f"{stamp.month:02d}", stamp.strftime("%B"), stamp.strftime("%b")}
        days = {str(stamp.day), f"{stamp.day:02d}"}
        assert any(
            str(stamp.year) in t and any(m in t for m in months) and any(d in t for d in days)
            for t in matching
        ), f"the card for {complaint.agent_name!r} does not show its year, month and day"
