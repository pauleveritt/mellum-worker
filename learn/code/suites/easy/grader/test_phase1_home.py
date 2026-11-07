"""Phase 1 page contract, independently collectable without a data module."""

from turbohtml import parse

from grader_tests._contract import (
    TAGLINE,
    _assert_navigation,
    _has_html5_doctype,
    _normalized_text,
    client,
)


def test_home_still_returns_200_and_tagline():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    assert TAGLINE in _normalized_text(parse(response.text))


def test_home_has_html5_doctype():
    document = parse(client.get("/", follow_redirects=False).text)
    assert _has_html5_doctype(document)


def test_home_html_element_declares_english_language():
    document = parse(client.get("/", follow_redirects=False).text)
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"


def test_home_still_has_navigation_links():
    document = parse(client.get("/", follow_redirects=False).text)
    _assert_navigation(document)
