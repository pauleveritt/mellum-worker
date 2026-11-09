"""Phase 2: the board, seed data, and positional timestamp contract."""

from datetime import timedelta

from turbohtml import parse

from grader_tests._contract import (
    SEED_COMPLAINT,
    _assert_navigation,
    _has_displayed_date,
    _has_html5_doctype,
    _normalized_text,
    client,
)
from grader_tests._seed import SEED_COMPLAINTS, Complaint, fields
import models


def test_complaints_board_still_lists_seed_complaint():
    response = client.get("/complaints", follow_redirects=False)
    assert response.status_code == 200
    assert any(complaint.text == SEED_COMPLAINT for complaint in SEED_COMPLAINTS)
    assert SEED_COMPLAINT in _normalized_text(parse(response.text))


def test_complaints_board_preserves_the_shared_layout():
    response = client.get("/complaints", follow_redirects=False)
    assert response.status_code == 200
    document = parse(response.text)
    html = document.select_one("html")
    assert _has_html5_doctype(document)
    assert html is not None and (html.attr("lang") or "").casefold() == "en"
    _assert_navigation(document)


def test_complaints_board_still_has_its_heading():
    document = parse(client.get("/complaints", follow_redirects=False).text)
    assert any(_normalized_text(heading) == "Complaints Board"
               for heading in document.select("h1, h2, h3, h4, h5, h6, [role=heading]"))


def test_complaints_board_still_renders_seed_complaint_details():
    document = parse(client.get("/complaints", follow_redirects=False).text)
    cards = [_normalized_text(card) for card in document.select(".card")]
    assert len(cards) >= len(SEED_COMPLAINTS)
    for complaint in SEED_COMPLAINTS:
        matching = [text for text in cards if complaint.agent_name in text and complaint.text in text]
        assert matching, f"Complaint details not rendered for {complaint.agent_name!r}"
        assert any(_has_displayed_date(text, complaint.timestamp) for text in matching), (
            f"Complaint date not rendered for {complaint.agent_name!r}"
        )


def test_complaint_model_contract_is_preserved():
    field_map = {field.name: field for field in fields(Complaint)}
    assert {"agent_name", "text", "timestamp"} <= field_map.keys()
    first = Complaint("first", "First complaint")
    second = Complaint("second", "Second complaint")
    assert first.agent_name == "first" and first.text == "First complaint"
    assert first.timestamp is not second.timestamp
    for complaint in (first, second):
        assert complaint.timestamp.tzinfo is not None
        assert complaint.timestamp.tzinfo.utcoffset(complaint.timestamp) is not None


def test_seed_complaint_count_is_preserved():
    assert isinstance(models.complaints, list)
    assert 3 <= len(SEED_COMPLAINTS) <= 5


def test_complaint_timestamps_are_utc():
    assert Complaint("utc", "Timezone check").timestamp.utcoffset() == timedelta(0)
    assert all(complaint.timestamp.utcoffset() == timedelta(0) for complaint in SEED_COMPLAINTS)


def test_board_shows_one_bootstrap_card_per_complaint():
    document = parse(client.get("/complaints", follow_redirects=False).text)
    cards = [_normalized_text(card) for card in document.select(".card")]
    for complaint in models.complaints:
        same = sum((other.agent_name, other.text) == (complaint.agent_name, complaint.text) for other in models.complaints)
        assert sum(complaint.agent_name in card and complaint.text in card for card in cards) == same
