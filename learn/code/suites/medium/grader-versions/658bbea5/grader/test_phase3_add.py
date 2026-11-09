"""Phase 3: usable form association, append semantics, and visible persistence."""

from turbohtml import parse

from grader_tests._contract import _normalized_text, _post_forms, client
import models


def test_post_complaint_redirects_to_complaints_board():
    response = client.post(
        "/complaints", data={"agent_name": "Codex", "text": "The requirements changed mid-sprint."},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"


def _records():
    return [(complaint.agent_name, complaint.text, complaint.timestamp) for complaint in models.complaints]


def test_posted_complaint_appears_on_complaints_board():
    before = _records()
    prior_cards = [_normalized_text(card) for card in parse(client.get("/complaints").text).select(".card")]
    # Multiple additions expose stores that silently discard older complaints.
    for index in range(4):
        agent_name = f"Codex acceptance test {index}"
        text = f"The acceptance criteria changed after implementation, round {index}."
        response = client.post(
            "/complaints", data={"agent_name": agent_name, "text": text}, follow_redirects=False,
        )
        assert response.status_code == 303
        after = _records()
        assert after[:-1] == before
        assert len(after) == len(before) + 1
        assert after[-1][:2] == (agent_name, text)
        response = client.get("/complaints", follow_redirects=False)
        assert response.status_code == 200
        cards = [_normalized_text(card) for card in parse(response.text).select(".card")]
        assert all(card in cards for card in prior_cards)
        assert any(agent_name in card and text in card for card in cards)
        before, prior_cards = after, cards


def test_complaints_board_renders_add_complaint_form():
    document = parse(client.get("/complaints", follow_redirects=False).text)
    cards = document.select(".card")
    assert any(
        all(card.position < form.position for card in cards)
        and any(control.tag == "input" and control.attr("name") == "agent_name"
                and (control.attr("type") or "text").casefold() == "text"
                and "readonly" not in control.attrs for control in controls)
        and any(control.tag == "textarea" and control.attr("name") == "text"
                and "readonly" not in control.attrs for control in controls)
        for form, controls, _ in _post_forms(document, "/complaints")
    ), "the final add form needs its own enabled name, text, and submit controls"
