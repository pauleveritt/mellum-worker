"""Phase 3 -- adding a complaint. Harness-owned.

Cumulative scope: phases 1, 2 AND 3. None of these three checks touches
the seed snapshot, so this module imports the shared preamble only.

NOTE -- the known semantic trap (lessons.md #13): TestClient follows
redirects by default, so a test for the 303 MUST pass
follow_redirects=False or it will silently assert against the followed
page and pass for the wrong reason. This suite is the one place that trap
must not be fallen into, since it is what grades everyone else.

Assertion bodies are copied verbatim from
agentclinic-repair-depth-3/overlay/test_acceptance.py (:158-:206). Only
the module structure differs.
"""

from turbohtml import parse

from grader_tests._contract import client


def test_post_complaint_redirects_to_complaints_board():
    response = client.post(
        "/complaints",
        data={
            "agent_name": "Codex",
            "text": "The requirements changed mid-sprint.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/complaints"


def test_posted_complaint_appears_on_complaints_board():
    agent_name = "Codex acceptance test"
    text = "The acceptance criteria changed after implementation."
    client.post(
        "/complaints",
        data={"agent_name": agent_name, "text": text},
        follow_redirects=False,
    )

    response = client.get("/complaints")
    assert response.status_code == 200
    assert agent_name in response.text
    assert text in response.text


def test_complaints_board_renders_add_complaint_form():
    document = parse(client.get("/complaints").text)

    assert any(
        form.attr("action") in {None, "", "/complaints"}
        and (form.attr("method") or "").lower() == "post"
        for form in document.select("form")
    )
    assert any(
        control.tag == "input" and control.attr("name") == "agent_name"
        for control in document.select("input, textarea, button")
    )
    assert any(
        control.tag == "textarea" and control.attr("name") == "text"
        for control in document.select("input, textarea, button")
    )
    assert any(
        (control.tag == "button" and (control.attr("type") or "").lower() in {"", "submit"})
        or (control.tag == "input" and (control.attr("type") or "").lower() == "submit")
        for control in document.select("input, textarea, button")
    )
