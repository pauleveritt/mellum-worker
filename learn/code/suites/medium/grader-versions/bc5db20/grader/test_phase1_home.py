"""Phase 1 -- the home page. Harness-owned.

Independently collectable on purpose. Nothing in this module, or in
anything it imports, reaches the application's data module: a phase-1
workspace does not have one yet, and pytest imports a test module during
collection, before any selector applies. A check that reached it could
therefore not grade phase 1 at all.

Assertion bodies are copied verbatim from
agentclinic-repair-depth-3/overlay/test_acceptance.py (:47-:79). Only the
module structure differs; provenance is claimed per check and enforced by
tests/test_agentclinic_session_phased.py.
"""

from turbohtml import parse

from grader_tests._contract import (
    TAGLINE,
    _has_html5_doctype,
    _normalized_text,
    client,
)


def test_home_still_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert TAGLINE in response.text


def test_home_has_html5_doctype():
    document = parse(client.get("/").text)

    assert _has_html5_doctype(document)


def test_home_html_element_declares_english_language():
    document = parse(client.get("/").text)
    html = document.select_one("html")

    assert html is not None and html.attr("lang").casefold() == "en"


def test_home_still_has_navigation_links():
    body = client.get("/").text
    document = parse(body)

    assert "AgentClinic" in body
    assert any(
        link.attr("href") == "/" and _normalized_text(link).casefold() == "home"
        for link in document.select("a")
    )
    assert any(
        link.attr("href") == "/complaints"
        and _normalized_text(link).casefold() == "complaints"
        for link in document.select("a")
    )
