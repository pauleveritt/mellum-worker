"""Phase 1 — Home Page: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import ast
import os
import re
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

import jinja2
from jinja2 import nodes
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from turbohtml import Doctype, Element, parse

import app as app_module
from app import app

ROOT = Path(app_module.__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))
client = TestClient(app)
TAGLINE = "Come in. Sit down. Tell us about your human."
FAVICON = "https://www.python.org/static/favicon.ico"


def _page(path: str):
    response = client.get(path)
    assert response.status_code == 200, f"GET {path} answered {response.status_code}"
    return response.text, parse(response.text)


def _render(source: str) -> str:
    """Render a template string against the project's own templates, as a page of the app would."""
    request = Request({"type": "http", "app": app, "router": app.router, "method": "GET", "path": "/",
                       "root_path": "", "headers": [], "query_string": b"", "scheme": "http",
                       "server": ("testserver", 80)})
    return TEMPLATES.env.from_string(source).render(request=request)


def _title(html: str) -> str:
    element = parse(html).select_one("title")
    return " ".join(element.text.split()) if element is not None else ""


def _is_bootstrap5(url: str | None, suffix: str) -> bool:
    url = url or ""
    return url.startswith(("http://", "https://", "//")) and re.search(r"bootstrap@?/?5", url) is not None \
        and url.split("?")[0].endswith(suffix)


def test_home_answers_200_with_the_tagline_word_for_word():
    body, _ = _page("/")
    assert TAGLINE in body


def test_home_starts_with_the_html5_doctype():
    body, document = _page("/")
    assert body.lstrip().lower().startswith("<!doctype html>")
    assert any(isinstance(node, Doctype) and node.name.casefold() == "html" for node in document.children)


def test_home_html_element_declares_english():
    _, document = _page("/")
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"


def test_home_navbar_shows_the_brand_and_links_home_and_complaints():
    body, document = _page("/")
    assert "AgentClinic" in body
    links = [(" ".join(a.text.split()), a.attr("href")) for a in document.select("a")]
    assert any(text.casefold() == "home" and href == "/" for text, href in links), links
    assert any(text.casefold() == "complaints" and href == "/complaints" for text, href in links), links


def test_home_is_rendered_from_home_html_which_extends_base_html():
    source = (ROOT / "templates" / "home.html").read_text()
    extends = list(TEMPLATES.env.parse(source).find_all(nodes.Extends))
    assert extends and isinstance(extends[0].template, nodes.Const) and extends[0].template.value == "base.html"
    loaded: list[str] = []
    original = jinja2.Environment.get_template

    def recording(self, name, *args, **kwargs):
        loaded.append(getattr(name, "name", name))
        return original(self, name, *args, **kwargs)

    jinja2.Environment.get_template = recording
    try:
        assert TAGLINE in _page("/")[0]
    finally:
        jinja2.Environment.get_template = original
    assert "home.html" in loaded and "base.html" in loaded, loaded


def test_layout_head_has_viewport_bootstrap_css_and_favicon():
    head = parse(_render('{% extends "base.html" %}')).select_one("head")
    assert head is not None
    viewports = [m.attr("content") or "" for m in head.select("meta") if (m.attr("name") or "") == "viewport"]
    assert any("width=device-width" in v for v in viewports), viewports
    links = head.select("link")
    assert any(_is_bootstrap5(link.attr("href"), ".css") for link in links), "no Bootstrap 5 CSS from a CDN"
    assert any(link.attr("href") == FAVICON and "icon" in (link.attr("rel") or "") for link in links)


def test_layout_body_ends_with_the_bootstrap5_js_bundle():
    body = parse(_render('{% extends "base.html" %}')).select_one("body")
    assert body is not None
    elements = [child for child in body.children if isinstance(child, Element)]
    assert elements, "the body has no elements"
    last = elements[-1]
    assert last.tag == "script" and _is_bootstrap5(last.attr("src"), ".js") and "bundle" in (last.attr("src") or "")


def test_a_page_title_is_agentclinic_by_default():
    assert _title(_render('{% extends "base.html" %}')) == "AgentClinic"


def test_a_page_that_extends_the_layout_can_set_its_own_title():
    blocks = {b.name for b in TEMPLATES.env.parse((ROOT / "templates" / "base.html").read_text()).find_all(nodes.Block)}
    titles = {name: _title(_render('{% extends "base.html" %}{% block ' + name + ' %}Own Title{% endblock %}'))
              for name in blocks}
    assert "Own Title" in titles.values(), titles


def test_home_has_a_hero_holding_the_tagline_and_a_welcoming_paragraph():
    _, document = _page("/")
    marked = lambda e: e.tag == "section" or "hero" in f"{e.attr('class') or ''} {e.attr('id') or ''}".lower()
    heroes = [e for e in document.select("*") if marked(e) and TAGLINE in " ".join(e.text.split())]
    assert heroes, "no hero section (a <section>, or an element marked hero) holds the tagline"
    paragraphs = [" ".join(p.text.split()) for p in document.select("p")]
    assert any(text and TAGLINE not in text and len(text) >= 20 for text in paragraphs), paragraphs


def test_app_py_has_a_main_block():
    tree = ast.parse((ROOT / "app.py").read_text())
    assert any(isinstance(n, ast.If) and "__name__" in ast.unparse(n.test) and "__main__" in ast.unparse(n.test)
               for n in tree.body)


def test_running_app_py_starts_uvicorn_with_reload_and_serves_home(tmp_path):
    log = tmp_path / "app.log"
    with log.open("w") as sink:
        process = subprocess.Popen(["uv", "run", "--offline", "python", "app.py"], cwd=ROOT,
                                   stdout=sink, stderr=subprocess.STDOUT, start_new_session=True,
                                   env={k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"})
    output, url = "", None
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and process.poll() is None:
            output = log.read_text()
            match = re.search(r"Uvicorn running on (https?://\S+)", output)
            if match and url is None:
                url = match.group(1).replace("0.0.0.0", "127.0.0.1")
            if url:
                try:
                    with urllib.request.urlopen(url.rstrip("/") + "/", timeout=2) as response:
                        if response.status == 200 and TAGLINE in response.read().decode():
                            break
                except OSError:
                    pass
            time.sleep(0.3)
        else:
            output = log.read_text()  # a start that died at once wrote its reason after the last read
            raise AssertionError(f"app.py did not serve GET / within 30 s:\n{output[-1500:]}")
        assert "reloader" in output.lower(), f"uvicorn is not running with reload:\n{output[-1500:]}"
        assert process.poll() is None, "app.py stopped serving"
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)


def test_the_projects_own_tests_pass():
    assert (ROOT / "tests" / "test_home.py").is_file()
    result = subprocess.run(["uv", "run", "--offline", "python", "-m", "pytest", "tests", "-q"], cwd=ROOT,
                            capture_output=True, text=True, timeout=120,
                            env={k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH")})
    assert result.returncode == 0, result.stdout[-1500:]
