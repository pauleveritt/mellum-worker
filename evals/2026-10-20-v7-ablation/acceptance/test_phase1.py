"""Mediated acceptance test for Phase 1 (home page), written from phase-1-home.md."""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_home_returns_200_with_the_tagline():
    r = client.get("/")
    assert r.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in r.text


def test_layout_has_lang_title_nav_and_favicon():
    text = client.get("/").text
    assert 'lang="en"' in text
    assert "AgentClinic" in text
    assert 'href="/complaints"' in text
    assert "https://www.python.org/static/favicon.ico" in text
