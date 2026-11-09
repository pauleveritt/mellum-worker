"""Phase 4: global integer identity and target-only, order-preserving transitions."""

from dataclasses import fields
import re

from turbohtml import Element, Text, parse

from grader_tests._contract import _is_visible, _normalized_text, _post_forms, client
from grader_tests._seed import SEED_COMPLAINTS, Complaint
import models


def _snapshot():
    records = {
        complaint.id: (complaint.agent_name, complaint.text, complaint.timestamp, complaint.status)
        for complaint in models.complaints
    }
    assert len(records) == len(models.complaints), "complaint ids must remain unique"
    return records


# The roadmap asks for the word; a caption before it is still that word on show.
_STATE = re.compile(r"(?:(?i:status|state)\s*:\s*)?(Open|Resolved)")
_CONTROLS = {"form", "button", "input", "select", "textarea"}


def _label_text(node) -> str:
    """The text an element shows, leaving out the controls that may sit beside a label."""
    if isinstance(node, Text):
        return node.text
    if isinstance(node, Element) and (node.tag in _CONTROLS or not _is_visible(node)):
        return ""
    return "".join(_label_text(child) for child in node.children)


def _state_label(node) -> str | None:
    match = _STATE.fullmatch(" ".join(_label_text(node).split()))
    return match[1] if match else None


def _is_negated(node) -> bool:
    """`Not` directly before a state word makes a different phrase, not that state on show."""
    earlier = None
    for child in node.parent.children:
        if child == node:
            break
        if not isinstance(child, Text) or child.text.strip():
            earlier = child
    return isinstance(earlier, Text) and re.search(r"\bnot\s*$", earlier.text, re.I) is not None


def _post_new_complaint(agent_name: str, text: str) -> int:
    before = _snapshot()
    response = client.post(
        "/complaints", data={"agent_name": agent_name, "text": text}, follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    after = _snapshot()
    assert len(after) == len(before) + 1
    assert all(after.get(key) == value for key, value in before.items())
    new_ids = after.keys() - before.keys()
    assert len(new_ids) == 1
    complaint_id = new_ids.pop()
    assert type(complaint_id) is int
    assert complaint_id > max(before, default=-1)
    assert after[complaint_id][:2] == (agent_name, text)
    assert after[complaint_id][-1] == "open"
    return complaint_id


def test_complaint_identity_is_stable_and_keyword_only():
    # Retain this historical check id; the contract does not mandate kw_only.
    field_map = {field.name: field for field in fields(Complaint)}
    assert {"id", "status"} <= field_map.keys()
    earlier_ids = [complaint.id for complaint in models.complaints]
    assert all(type(identity) is int for identity in earlier_ids)
    first = Complaint("first", "First complaint")
    second = Complaint("second", "Second complaint")
    assert first.agent_name == "first" and first.text == "First complaint"
    assert second.agent_name == "second" and second.text == "Second complaint"
    assert type(first.id) is int and type(second.id) is int
    assert first.id > max(earlier_ids, default=-1)
    assert second.id > first.id
    assert first.status == second.status == "open"
    first_id, second_id = first.id, second.id
    route_id = _post_new_complaint("Identity route check", "Identity spans every construction path.")
    assert route_id > second_id
    assert first.id == first_id and second.id == second_id


def test_complaint_ids_increase_across_direct_and_route_creation():
    stored = [complaint.id for complaint in models.complaints]
    direct_one = Complaint("Direct path one", "Built without the route.")
    route_one = _post_new_complaint("Route path one", "Created through the route.")
    direct_two = Complaint("Direct path two", "Built after the route ran.")
    route_two = _post_new_complaint("Route path two", "Created after both paths ran.")
    sequence = [max(stored, default=-1), direct_one.id, route_one, direct_two.id, route_two]
    assert all(type(identity) is int for identity in sequence)
    assert all(earlier < later for earlier, later in zip(sequence, sequence[1:])), sequence
    assert (direct_one.id, direct_two.id) == (sequence[1], sequence[3])
    assert [complaint.id for complaint in models.complaints][:len(stored)] == stored


def test_seed_complaints_have_distinct_ids():
    ids = [complaint.id for complaint in SEED_COMPLAINTS]
    assert all(type(identity) is int for identity in ids)
    assert len(set(ids)) == len(ids)
    created = [Complaint("Seed identity check", "The counter continues after seeding.") for _ in range(3)]
    previous = max(ids, default=-1)
    for complaint in created:
        assert type(complaint.id) is int and complaint.id > previous
        previous = complaint.id


def _card_has_control(document, card, complaint_id: int, action: str) -> bool:
    return any(
        any(card in submit.ancestors
            and (_normalized_text(submit).casefold() == action
                 or (submit.attr("value") or "").casefold() == action)
            for submit in submits)
        for _, _, submits in _post_forms(document, f"/complaints/{complaint_id}/{action}")
    )


def _board_order() -> tuple[int, ...]:
    response = client.get("/complaints", follow_redirects=False)
    assert response.status_code == 200
    document = parse(response.text)
    cards = document.select(".card")
    located = []
    for complaint in models.complaints:
        if complaint.status == "archived":
            continue
        assert complaint.status in {"open", "resolved"}
        action = "resolve" if complaint.status == "open" else "reopen"
        matching = [card for card in cards
                    if complaint.agent_name in _normalized_text(card)
                    and complaint.text in _normalized_text(card)
                    and _card_has_control(document, card, complaint.id, action)]
        assert len(matching) == 1, f"complaint {complaint.id} needs one card with its {action} control"
        card = matching[0]
        labels = set()
        for node in card.select("*"):
            # Read the complete outer label, including nested inline markup.
            if any(isinstance(parent, Element) and parent != card and (parent.tag in {"span", "output"}
                   or parent.attr("role") == "status" or "badge" in (parent.attr("class") or "").split())
                   for parent in node.ancestors):
                continue
            label = _state_label(node) if _is_visible(node) and not _is_negated(node) else None
            if label:
                labels.add(label)
        assert labels == {complaint.status.capitalize()}, f"card state disagrees with complaint {complaint.id}"
        located.append((cards.index(card), complaint.id))
    assert len({index for index, _ in located}) == len(located)
    return tuple(identity for _, identity in sorted(located))


def _transition(complaint_id: int, action: str) -> None:
    before = _snapshot()
    order = _board_order()
    response = client.post(f"/complaints/{complaint_id}/{action}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"
    expected = dict(before)
    expected[complaint_id] = (*before[complaint_id][:-1], "resolved" if action == "resolve" else "open")
    assert _snapshot() == expected, "only the target complaint's status may change"
    assert _board_order() == order, f"{action} changed the board order"


def test_resolve_route_marks_complaint_resolved_and_redirects():
    complaint_id = _post_new_complaint("Resolve Check", "Needs resolving.")
    _transition(complaint_id, "resolve")


def test_reopen_route_marks_complaint_open_and_redirects():
    complaint_id = _post_new_complaint("Reopen Check", "Needs reopening.")
    _transition(complaint_id, "resolve")
    _transition(complaint_id, "reopen")


def test_resolve_reopen_does_not_reorder_the_board():
    first_id = _post_new_complaint("Order Check One", "First of the pair.")
    _post_new_complaint("Order Check Two", "Second of the pair.")
    _transition(first_id, "resolve")
    _transition(first_id, "reopen")
