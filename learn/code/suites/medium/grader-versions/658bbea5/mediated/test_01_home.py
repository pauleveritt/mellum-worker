"""Phase 1 — Home Page: the request's acceptance test, written from `specs/roadmap.md`.

You did not write this test and cannot change it; it runs from outside the project with the
project on the import path. The work is done when it passes.
"""

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

import jinja2
from fastapi import FastAPI
from jinja2 import nodes
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from turbohtml import Doctype, parse

TAGLINE = "Come in. Sit down. Tell us about your human."
BARE_PAGE = '{% extends "base.html" %}'
NAVBAR = "nav, .navbar"
SETTINGS_MARK = "UVICORN-SETTINGS "
READ_SETTINGS = f"""
import json, runpy, uvicorn
config_init = uvicorn.Config.__init__
def report(self, *args, **kwargs):
    config_init(self, *args, **kwargs)
    settings = {{"host": self.host, "port": self.port, "reload": self.reload}}
    print({SETTINGS_MARK!r} + json.dumps(settings), flush=True)
    raise SystemExit(0)
uvicorn.Config.__init__ = report
runpy.run_path("app.py", run_name="__main__")
"""


def _app():
    import app as module  # imported here so a broken app.py fails these tests instead of stopping collection
    return module


def _root() -> Path:
    return Path(_app().__file__).resolve().parent


def _home():
    response = TestClient(_app().app).get("/")
    assert response.status_code == 200, f"GET / answered {response.status_code}"
    return response.text, parse(response.text)


def _templates() -> jinja2.Environment:
    return Jinja2Templates(directory=str(_root() / "templates")).env


def _render_the_bare_layout():
    environment = _templates()
    environment.loader = jinja2.ChoiceLoader([jinja2.DictLoader({"mediated_page.html": BARE_PAGE}), environment.loader])
    application = _app().app
    scope = {"type": "http", "app": application, "router": application.router, "method": "GET", "path": "/",
             "root_path": "", "scheme": "http", "server": ("testserver", 80), "query_string": b"", "headers": []}
    return parse(environment.get_template("mediated_page.html").render(request=Request(scope)))


def _words(node) -> str:
    return " ".join(node.text.split())


def _link_path(href: str | None) -> str | None:
    """The path a link goes to on this site; None for an empty, fragment-only or off-site link."""
    parts = urlsplit(href or "")
    if parts.netloc not in ("", "testserver") or not (parts.path or parts.netloc):
        return None
    return parts.path or "/"


def _text_outside_the_navbar(document) -> list[str]:
    for navbar in document.select(NAVBAR):
        navbar.decompose()
    return _words(document.select_one("body")).split()


def _project_copy(tmp_path: Path) -> Path:
    """A throwaway copy of the project, so nothing here touches the real one."""
    return shutil.copytree(_root(), tmp_path / "project", ignore=shutil.ignore_patterns(
        ".venv", ".git", "__pycache__", ".pytest_cache"))


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH")}


def _stop(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    process.wait(timeout=10)


def _uvicorn_settings(project: Path) -> dict:
    """What app.py's `__main__` block hands to uvicorn, read without starting a server; empty if it never gets there."""
    process = subprocess.Popen([sys.executable, "-c", READ_SETTINGS], cwd=project, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, start_new_session=True, env=_env())
    try:
        output, _ = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        return {}
    finally:
        _stop(process)
    found = re.search(rf"^{SETTINGS_MARK}(\{{.*\}})$", output, re.M)
    return json.loads(found.group(1)) if found else {}


def _local_address(host: str) -> str:
    return "127.0.0.1" if host in ("", "0.0.0.0", "::", "localhost") else host


def _port_is_held(address: str, port: int) -> bool:
    try:
        with socket.create_connection((address, port), timeout=1):
            return True
    except OSError:
        return False


def _refuse_a_held_port(address: str, port: int) -> None:
    assert not _port_is_held(address, port), (
        f"port {port} is held by a server that is already running, so app.py was not started; "
        "stop that server (do not change the app for this) and run this check again")


def _serves_the_tagline(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200 and TAGLINE in response.read().decode()
    except OSError:
        return False


def test_app_py_holds_the_fastapi_application_as_app():
    assert isinstance(_app().app, FastAPI)


def test_home_answers_200_with_the_tagline_word_for_word():
    _, document = _home()
    assert TAGLINE in _words(document.select_one("body"))


def test_home_has_a_short_welcome_beside_the_tagline():
    _, document = _home()
    outside_the_navbar = " ".join(_text_outside_the_navbar(document))
    assert TAGLINE in outside_the_navbar, "the tagline is not in the page outside the navbar"
    from_the_layout = set(_text_outside_the_navbar(_render_the_bare_layout()))
    welcome = [word for word in outside_the_navbar.replace(TAGLINE, " ").split() if word not in from_the_layout]
    assert len(welcome) >= 3, f"no welcome beside the tagline: {welcome}"


def test_home_starts_with_the_doctype_and_html_lang_en():
    text, document = _home()
    assert text.lstrip().lower().startswith("<!doctype html>")
    assert any(isinstance(node, Doctype) and node.name.casefold() == "html" for node in document.children)
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"


def test_the_navbar_shows_the_brand_and_links_home_and_complaints():
    _, document = _home()
    navbars = document.select(NAVBAR)
    assert navbars, "the page has no navbar"
    for navbar in navbars:
        links = [(_words(a).casefold(), _link_path(a.attr("href"))) for a in navbar.select("a")]
        if "AgentClinic" in _words(navbar) and ("home", "/") in links and ("complaints", "/complaints") in links:
            return
    raise AssertionError("no navbar shows AgentClinic and links Home to / and Complaints to /complaints")


def test_home_is_rendered_from_home_html_which_extends_base_html():
    environment = _templates()
    source = (_root() / "templates" / "home.html").read_text()
    extends = list(environment.parse(source).find_all(nodes.Extends))
    assert extends and isinstance(extends[0].template, nodes.Const) and extends[0].template.value == "base.html"
    loaded: list[str] = []
    original = jinja2.Environment.get_template

    def recording(self, name, *args, **kwargs):
        loaded.append(getattr(name, "name", name))
        return original(self, name, *args, **kwargs)

    jinja2.Environment.get_template = recording
    try:
        assert TAGLINE in _home()[0]
    finally:
        jinja2.Environment.get_template = original
    assert "home.html" in loaded and "base.html" in loaded, loaded


def test_app_py_starts_uvicorn_with_reload_from_a_main_block(tmp_path):
    source = (_root() / "app.py").read_text()
    assert re.search(r"""^if\s+__name__\s*==\s*["']__main__["']\s*:""", source, re.M), (
        'app.py has no if __name__ == "__main__" block')
    settings = _uvicorn_settings(_project_copy(tmp_path))
    assert settings, "running app.py did not start uvicorn from its __main__ block"
    assert settings["reload"] is True, "app.py starts uvicorn without reload"


def test_running_app_py_serves_home(tmp_path):
    project = _project_copy(tmp_path)
    settings = _uvicorn_settings(project)
    address, port = _local_address(settings.get("host", "127.0.0.1")), settings.get("port", 8000)
    _refuse_a_held_port(address, port)
    url = f"http://{address}:{port}/"
    log = tmp_path / "app.log"
    with log.open("w") as sink:
        process = subprocess.Popen([sys.executable, "app.py"], cwd=project, stdout=sink,
                                   stderr=subprocess.STDOUT, start_new_session=True, env=_env())
    try:
        deadline = time.monotonic() + 30
        while not _serves_the_tagline(url):
            assert process.poll() is None, f"app.py exited instead of serving GET /:\n{log.read_text()[-1500:]}"
            assert time.monotonic() < deadline, f"app.py did not serve GET / within 30 s:\n{log.read_text()[-1500:]}"
            time.sleep(0.3)
    finally:
        _stop(process)


def test_the_projects_own_tests_pass(tmp_path):
    assert (_root() / "tests").is_dir()
    project = _project_copy(tmp_path)
    result = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
                            cwd=project, env=_env(), capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-1500:]
