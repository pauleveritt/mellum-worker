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

import jinja2
from jinja2 import nodes
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient
from turbohtml import Doctype, parse

import app as app_module
from app import app

ROOT = Path(app_module.__file__).resolve().parent
client = TestClient(app)
TAGLINE = "Come in. Sit down. Tell us about your human."


def _page(path: str):
    response = client.get(path)
    assert response.status_code == 200, f"GET {path} answered {response.status_code}"
    return response.text, parse(response.text)


def _project_copy(tmp_path: Path) -> Path:
    """A throwaway copy of the project, so nothing here touches the real one."""
    return shutil.copytree(ROOT, tmp_path / "project", ignore=shutil.ignore_patterns(
        ".venv", ".git", "__pycache__", ".pytest_cache"))


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH")}


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


def _uvicorn_settings(project: Path) -> dict:
    """What app.py's `__main__` block hands to uvicorn, read without starting a server; empty if it never gets there."""
    process = subprocess.Popen([sys.executable, "-c", READ_SETTINGS], cwd=project, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, start_new_session=True, env=_env())
    try:
        output, _ = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        return {}
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        process.wait(timeout=10)
    found = re.search(rf"^{SETTINGS_MARK}(\{{.*\}})$", output, re.M)
    return json.loads(found.group(1)) if found else {}


def _refuse_a_held_port(project: Path) -> None:
    settings = _uvicorn_settings(project)
    host, port = settings.get("host", "127.0.0.1"), settings.get("port", 8000)
    address = "127.0.0.1" if host in ("", "0.0.0.0", "::", "localhost") else host
    try:
        with socket.create_connection((address, port), timeout=1):
            held = True
    except OSError:
        held = False
    assert not held, (
        f"port {port} is held by a server that is already running, so app.py was not started; "
        "stop that server (do not change the app for this) and run this check again")


def test_home_answers_200_with_the_tagline_word_for_word():
    body, _ = _page("/")
    assert TAGLINE in body


def test_home_has_a_short_welcome_beside_the_tagline():
    _, document = _page("/")
    rest = " ".join(document.select_one("body").text.split()).replace(TAGLINE, "")
    words = [w for w in re.findall(r"[A-Za-z']+", rest) if w not in ("AgentClinic", "Home", "Complaints")]
    assert len(words) >= 3, f"no welcome beyond the tagline and the navbar: {words}"


def test_home_starts_with_the_doctype_and_html_lang_en():
    body, document = _page("/")
    assert body.lstrip().lower().startswith("<!doctype html>")
    assert any(isinstance(node, Doctype) and node.name.casefold() == "html" for node in document.children)
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"


def test_home_navbar_shows_the_brand_and_links_home_and_complaints():
    _, document = _page("/")
    assert "AgentClinic" in document.select_one("body").text
    links = [(" ".join(a.text.split()).casefold(), a.attr("href")) for a in document.select("a")]
    assert ("home", "/") in links, links
    assert ("complaints", "/complaints") in links, links


def test_home_is_rendered_from_home_html_which_extends_base_html():
    env = Jinja2Templates(directory=str(ROOT / "templates")).env
    extends = list(env.parse((ROOT / "templates" / "home.html").read_text()).find_all(nodes.Extends))
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


def test_running_app_py_starts_uvicorn_with_reload_and_serves_home(tmp_path):
    project = _project_copy(tmp_path)
    _refuse_a_held_port(project)
    log = tmp_path / "app.log"
    with log.open("w") as sink:
        process = subprocess.Popen([sys.executable, "app.py"], cwd=project, stdout=sink,
                                   stderr=subprocess.STDOUT, start_new_session=True, env=_env())
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
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)


def test_the_projects_own_tests_pass(tmp_path):
    assert (ROOT / "tests" / "test_home.py").is_file()
    project = _project_copy(tmp_path)
    result = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
                            cwd=project, env=_env(), capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-1500:]
