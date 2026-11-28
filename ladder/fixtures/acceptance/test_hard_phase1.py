"""Mediated acceptance test for the hard suite, phase 1 (the home page), written
from prompts/01.md as a superset of the hidden grader/test_phase1_home.py. It
pins the oracle's own checks - 200 + tagline, HTML5 doctype, html lang="en", the
AgentClinic brand and the Home (/) and Complaints (/complaints) nav links - and
adds the phase-1 spec items the oracle leaves thin: the viewport and charset
meta, the Bootstrap 5 CSS CDN, the python.org favicon link, and a welcoming
paragraph alongside the tagline.

Phase 1 only: it imports app, never models, because a phase-1 workspace has no
data module yet - the same reason the hidden oracle splits phase 1 into its own
module. Placed outside the worker write scope and restored before every attempt,
so the worker may read and run it but cannot weaken it. Checks are tolerant
substrings on the lowered body, so any correct build passes and a real miss
fails; the aim is a complete gate, not a brittle one.
"""
from starlette.testclient import TestClient

from app import app

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."


def _home() -> str:
    r = client.get("/")
    assert r.status_code == 200
    return r.text


# ---- the hidden oracle's own checks (grader/test_phase1_home.py) ----------
def test_home_returns_200_and_the_tagline():
    assert TAGLINE in _home()


def test_home_has_html5_doctype_and_english_language():
    low = _home().lower()
    assert "<!doctype html" in low
    assert 'lang="en"' in low


def test_home_navbar_brands_agentclinic_and_links_home_and_complaints():
    body = _home()
    assert "AgentClinic" in body
    low = body.lower()
    assert 'href="/"' in low
    assert 'href="/complaints"' in low


# ---- the phase-1 spec items the oracle leaves thin (prompts/01.md) --------
def test_base_layout_carries_the_head_meta_and_bootstrap():
    low = _home().lower()
    assert 'name="viewport"' in low
    assert "charset" in low
    assert "bootstrap" in low  # the Bootstrap 5 CSS CDN link / JS bundle


def test_base_layout_links_the_python_favicon():
    low = _home().lower()
    assert "icon" in low  # a <link rel="...icon...">
    assert "python.org/static/favicon.ico" in low


def test_home_hero_shows_the_tagline_and_a_welcoming_paragraph():
    body = _home()
    assert TAGLINE in body
    assert "<p" in body.lower()  # a welcoming paragraph in the hero
