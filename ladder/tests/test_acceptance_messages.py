"""The medium acceptance test must say what it FOUND when it fails, not just what it wanted.

The verify gate hands the worker each failing test's assertion lines. On the 2026-11-13
redirect-nudge screen, one rep spent all five gate rounds on "Bootstrap 5 CSS" with an
`any(<generator>)` underneath: its favicon link left an href quote open and swallowed the
stylesheet link, and nothing in the message showed that. Each case below breaks the complete
`agentclinic-done` build in one way and checks the failure names what the page held.

Slow: each case runs pytest in a copy of the synced fixture."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
DONE = HERE.parent / "fixtures" / "agentclinic-done"
ACC = HERE.parent / "fixtures" / "acceptance" / "test_medium.py"


def _run(tmp_path, edit):
    ws = tmp_path / "ws"
    shutil.copytree(DONE, ws, ignore=shutil.ignore_patterns(".venv", "__pycache__", "data.db", ".pytest_cache"))
    edit(ws)
    env = {**os.environ, "PYTHONPATH": str(ws)}
    env.pop("VIRTUAL_ENV", None)
    r = subprocess.run(
        ["uv", "run", "--frozen", "--with", "pytest", "python", "-m", "pytest", str(ACC), "-q", "-p", "no:cacheprovider", "--tb=short"],
        cwd=ws, env=env, capture_output=True, text=True, timeout=300,
    )
    return r.returncode, r.stdout + r.stderr


def _sub(path, old, new):
    text = path.read_text()
    assert old in text, f"fixture changed: {old!r} not in {path.name}"
    path.write_text(text.replace(old, new, 1))


def _reasons(out):
    return "\n".join(l for l in out.splitlines() if l.startswith("E "))


@pytest.mark.slow
def test_the_complete_build_stays_green(tmp_path):
    code, out = _run(tmp_path, lambda ws: None)
    assert code == 0, out[-2000:]


@pytest.mark.slow
def test_a_swallowed_stylesheet_link_shows_the_links_it_parsed(tmp_path):
    # rep 2's defect: an unclosed href quote on the favicon swallows the next <link>
    def edit(ws):
        _sub(ws / "templates" / "base.html",
             'href="https://www.python.org/static/favicon.ico">',
             'href="https://www.python.org/static/favicon.ico>')
    code, out = _run(tmp_path, edit)
    assert code != 0
    reasons = _reasons(out)
    assert "Bootstrap 5 CSS" in reasons
    assert re.search(r"<link[^\n]*bootstrap\.min\.css", reasons), reasons  # the parsed links are shown
    assert "generator object" not in reasons, reasons


@pytest.mark.slow
def test_a_missing_viewport_shows_the_meta_tags_found(tmp_path):
    def edit(ws):
        base = ws / "templates" / "base.html"
        base.write_text(re.sub(r'\s*<meta name="viewport"[^>]*>', "", base.read_text(), count=1))
    code, out = _run(tmp_path, edit)
    reasons = _reasons(out)
    assert "viewport" in reasons and "<meta" in reasons, reasons
    assert "generator object" not in reasons, reasons


@pytest.mark.slow
def test_a_missing_action_button_shows_the_card_forms_found(tmp_path):
    def edit(ws):
        tpl = ws / "templates" / "complaints.html"
        tpl.write_text(re.sub(r"(<button[^>]*>)\s*Resolve\s*(</button>)", r"\1Close\2", tpl.read_text()))
    code, out = _run(tmp_path, edit)
    reasons = _reasons(out)
    assert "resolve" in reasons.lower() and "Close" in reasons, reasons  # the button it did find
    assert "Tree object" not in reasons, reasons


@pytest.mark.slow
def test_a_missing_brand_shows_the_nav_links_found(tmp_path):
    def edit(ws):
        _sub(ws / "templates" / "base.html", ">AgentClinic</a>", ">Clinic</a>")
    code, out = _run(tmp_path, edit)
    reasons = _reasons(out)
    assert "AgentClinic brand" in reasons and "'Clinic'" in reasons, reasons


@pytest.mark.slow
def test_a_page_title_override_shows_the_title_found(tmp_path):
    # the 2026-11-13 messages screen, rep 1: home.html overrode the title block with "Home"
    def edit(ws):
        tpl = ws / "templates" / "home.html"
        text = tpl.read_text()
        text = re.sub(r"{% block title %}.*?{% endblock %}", "", text, flags=re.S)
        tpl.write_text(text.replace("{% block content %}", "{% block title %}Home{% endblock %}\n{% block content %}", 1))
    code, out = _run(tmp_path, edit)
    reasons = _reasons(out)
    assert "title" in reasons and "'Home'" in reasons, reasons
    assert "generator object" not in reasons, reasons
