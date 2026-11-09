"""Phase 2 -- the complaints board. Harness-owned.

Cumulative scope: phases 1 AND 2. Imports the seed snapshot, so this
module is collectable only once the workspace defines the data module --
which is exactly the phase this file grades.

Assertion bodies are copied verbatim from
agentclinic-repair-depth-3/overlay/test_acceptance.py (:82-:155). Only the
module structure differs.
"""

from turbohtml import parse

from grader_tests._contract import (
    SEED_COMPLAINT,
    _has_html5_doctype,
    _normalized_text,
    client,
)
from grader_tests._seed import MISSING, SEED_COMPLAINTS, Complaint, fields


def test_complaints_board_still_lists_seed_complaint():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert SEED_COMPLAINT in response.text


def test_complaints_board_preserves_the_shared_layout():
    response = client.get("/complaints")
    document = parse(response.text)
    html = document.select_one("html")

    assert _has_html5_doctype(document)
    assert html is not None and html.attr("lang").casefold() == "en"
    assert "AgentClinic" in response.text
    assert any(
        link.attr("href") == "/" and _normalized_text(link).casefold() == "home"
        for link in document.select("a")
    )
    assert any(
        link.attr("href") == "/complaints"
        and _normalized_text(link).casefold() == "complaints"
        for link in document.select("a")
    )


def test_complaints_board_still_has_its_heading():
    assert "Complaints Board" in client.get("/complaints").text


def test_complaints_board_still_renders_seed_complaint_details():
    document = parse(client.get("/complaints").text)
    cards = [_normalized_text(card) for card in document.select(".card")]
    assert len(cards) >= len(SEED_COMPLAINTS)

    for complaint in SEED_COMPLAINTS:
        matching_cards = [
            text
            for text in cards
            if complaint.agent_name in text
            and complaint.text in text
        ]
        assert matching_cards, (
            f"Complaint details not rendered for {complaint.agent_name!r}"
        )

        month_tokens = {
            str(complaint.timestamp.month),
            f"{complaint.timestamp.month:02d}",
            complaint.timestamp.strftime("%B"),
            complaint.timestamp.strftime("%b"),
        }
        day_tokens = {str(complaint.timestamp.day), f"{complaint.timestamp.day:02d}"}
        assert any(
            str(complaint.timestamp.year) in text
            and any(token in text for token in month_tokens)
            and any(token in text for token in day_tokens)
            for text in matching_cards
        ), f"Formatted timestamp not rendered for {complaint.agent_name!r}"


def test_complaint_model_contract_is_preserved():
    field_map = {field.name: field for field in fields(Complaint)}
    assert {"agent_name", "text", "timestamp"} <= field_map.keys()
    assert field_map["timestamp"].default_factory is not MISSING

    first = Complaint("first", "First complaint")
    second = Complaint("second", "Second complaint")
    assert first.timestamp is not second.timestamp
    assert first.timestamp.tzinfo is not None
    assert first.timestamp.tzinfo.utcoffset(first.timestamp) is not None


def test_seed_complaint_count_is_preserved():
    assert 3 <= len(SEED_COMPLAINTS) <= 5
