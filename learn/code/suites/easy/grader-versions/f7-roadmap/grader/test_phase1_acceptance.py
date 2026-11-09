"""The remaining existing Easy Phase 1 Acceptance items. Harness-owned."""

import ast
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from jinja2 import Environment, Template, TemplateError, meta, nodes
from starlette.requests import Request

from grader_tests._contract import TAGLINE, client
from grader_tests._easy_acceptance import Document, Element, bootstrap5_url, title


def _rendered_home(monkeypatch):
    """Observe real Jinja rendering, including applications returning HTMLResponse."""
    rendered, loaded = [], []
    render, render_async = Template.render, Template.render_async
    get_template = Environment.get_template

    def observe_render(template, *args, **kwargs):
        rendered.append((template, dict(*args, **kwargs)))
        return render(template, *args, **kwargs)

    async def observe_async(template, *args, **kwargs):
        rendered.append((template, dict(*args, **kwargs)))
        return await render_async(template, *args, **kwargs)

    def observe_load(environment, *args, **kwargs):
        template = get_template(environment, *args, **kwargs)
        loaded.append(template)
        return template

    with monkeypatch.context() as instrumentation:
        instrumentation.setattr(Template, "render", observe_render)
        instrumentation.setattr(Template, "render_async", observe_async)
        instrumentation.setattr(Environment, "get_template", observe_load)
        response = client.get("/", follow_redirects=False)
    home = next((item for item in rendered if item[0].name == "home.html"), None)
    assert home is not None, "GET / must render home.html through Jinja2"
    template, context = home
    assert Path(template.filename).resolve() == Path("templates/home.html").resolve()
    base = next((item for item in loaded if item.name == "base.html"), None)
    assert base is not None, "The home rendering must inherit base.html"
    assert Path(base.filename).resolve() == Path("templates/base.html").resolve()
    source, _, _ = template.environment.loader.get_source(template.environment, "home.html")
    assert list(template.environment.parse(source).find_all(nodes.Extends)), "home.html must extend the shared layout"
    return response, base, context


def _base_context(context, base):
    context = dict(context)
    request = context.get("request")
    if request is None:
        request = Request({"type": "http", "method": "GET", "path": "/", "root_path": "", "scheme": "http", "server": ("testserver", 80), "query_string": b"", "headers": [], "app": client.app})
    context["request"] = request
    # Keep application context unrelated to the page title. Remove only values
    # that a page could have supplied to override the default title.
    source, _, _ = base.environment.loader.get_source(base.environment, "base.html")
    match = re.search(r"<title\b[^>]*>(.*?)</title\s*>", source, flags=re.I | re.S)
    if match:
        title_variables = meta.find_undeclared_variables(base.environment.parse(match.group(1)))
        for name in title_variables - {"request"}:
            context.pop(name, None)
    return context


def test_home_renders_home_template_extending_shared_base(monkeypatch):
    _rendered_home(monkeypatch)


def _layout_documents(monkeypatch):
    response, base, context = _rendered_home(monkeypatch)
    return Document(response.text), Document(base.render(**_base_context(context, base)))


def test_layout_has_responsive_viewport(monkeypatch):
    for document in _layout_documents(monkeypatch):
        assert any(
            element.within("head")
            and (element.attrs.get("name") or "").casefold() == "viewport"
            and re.search(r"(?:^|[,;])\s*width\s*=\s*device-width\s*(?:[,;]|$)", element.attrs.get("content") or "", flags=re.I)
            for element in document.all("meta")
        ), "The shared head needs a responsive viewport"


def test_layout_has_bootstrap5_cdn_stylesheet_in_head(monkeypatch):
    for document in _layout_documents(monkeypatch):
        assert any(
            element.within("head")
            and "stylesheet" in (element.attrs.get("rel") or "").casefold().split()
            and bootstrap5_url(element.attrs.get("href"))
            for element in document.all("link")
        ), "Bootstrap 5 CSS must come from a CDN in the shared head"


def test_layout_has_python_favicon(monkeypatch):
    for document in _layout_documents(monkeypatch):
        assert any(
            element.within("head")
            and "icon" in (element.attrs.get("rel") or "").casefold().split()
            and element.attrs.get("href") == "https://www.python.org/static/favicon.ico"
            for element in document.all("link")
        ), "The shared head must link the specified Python favicon"


def test_layout_ends_body_with_bootstrap5_cdn_bundle(monkeypatch):
    for document in _layout_documents(monkeypatch):
        bodies = document.all("body")
        assert len(bodies) == 1
        meaningful = [node for node in bodies[0].children if isinstance(node, Element) or node.strip()]
        assert meaningful
        last = meaningful[-1]
        assert isinstance(last, Element) and last.tag == "script" and bootstrap5_url(last.attrs.get("src"), bundle=True), "The Bootstrap 5 CDN bundle must be last in the shared body"


def test_layout_title_defaults_to_agentclinic(monkeypatch):
    _, base, context = _rendered_home(monkeypatch)
    assert title(base.render(**_base_context(context, base))) == "AgentClinic"


def test_extending_page_can_override_layout_title(monkeypatch):
    _, base, context = _rendered_home(monkeypatch)
    environment = base.environment
    source, _, _ = environment.loader.get_source(environment, "base.html")
    tree = environment.parse(source)
    marker = "Independent page caption 81726"
    # Derive possible extension mechanisms, then check their actual rendered title.
    # No block or variable name is prescribed by the written contract.
    candidates = ["{% extends 'base.html' %}{% block " + block.name + " %}" + content + "{% endblock %}"
                  for block in tree.find_all(nodes.Block)
                  for content in (marker, "<title>" + marker + "</title>")]
    candidates.extend("{% extends 'base.html' %}{% set " + name + " = '" + marker + "' %}" for name in meta.find_undeclared_variables(tree) if name != "request")
    for candidate in candidates:
        try:
            rendered_title = title(environment.from_string(candidate).render(**_base_context(context, base)))
        except (TemplateError, AssertionError, TypeError, ValueError):
            # Overriding an outer head block can remove the title entirely.
            # That candidate says nothing about a nested title block or variable.
            continue
        if marker in rendered_title:
            return
    raise AssertionError("An extending page must be able to supply its own title")


def test_home_has_hero_and_welcoming_paragraph():
    document = Document(client.get("/", follow_redirects=False).text)
    assert any(
        element.visible() and not element.within("nav") and TAGLINE in element.text()
        and (element.tag in {"section", "header", "article", "div"} or element.attrs.get("role") in {"region", "banner"})
        for element in document.root.elements()
    ), "The tagline must be held in a hero section"
    assert any(
        paragraph.visible() and not paragraph.within("nav") and paragraph.text() and paragraph.text() != TAGLINE
        for paragraph in document.all("p")
    ), "The home page needs a welcoming paragraph"


def _main_guard(statement):
    if not isinstance(statement, ast.If) or not isinstance(statement.test, ast.Compare):
        return False
    comparison = statement.test
    if len(comparison.ops) != 1 or not isinstance(comparison.ops[0], ast.Eq):
        return False
    left, right = comparison.left, comparison.comparators[0]
    return any(isinstance(name, ast.Name) and name.id == "__name__" and isinstance(value, ast.Constant) and value.value == "__main__" for name, value in ((left, right), (right, left)))


def _events(path):
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # The worker may currently be finishing its event line.
    return events


def _stop(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=3)
        process.wait(timeout=3)
        return
    # A launcher can exit while a reload supervisor/worker is still alive.
    # Signal the process group even when the immediate process already exited.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=2)


def test_main_guard_launches_uvicorn_with_reload_and_keeps_serving(tmp_path):
    app_path = Path("app.py")
    original = app_path.read_bytes()
    assert any(_main_guard(statement) for statement in ast.parse(original).body), "app.py needs a __main__ guard"
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    events_path = tmp_path / "launcher-events.jsonl"
    trusted = Path(__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "EASY_LAUNCH_PORT": str(port),
        "EASY_LAUNCH_EVENTS": str(events_path),
        "UVICORN_PORT": str(port),
        "UVICORN_HOST": "127.0.0.1",
        "PYTHONPATH": os.pathsep.join([str(trusted), str(Path.cwd())]),
    }
    url = f"http://127.0.0.1:{port}/"
    with (tmp_path / "launcher-output.log").open("w+") as output:
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen([sys.executable, "-c", "from grader_tests._easy_launcher import run; run()"], stdout=output, stderr=subprocess.STDOUT, env=environment, **options)
        try:
            deadline = time.monotonic() + 10
            ready = False
            while time.monotonic() < deadline and process.poll() is None:
                configurations = [event for event in _events(events_path) if event["kind"] == "config"]
                if configurations:
                    assert all(event["reload"] is True for event in configurations), "uvicorn reload must be enabled"
                try:
                    with urlopen(url, timeout=0.25) as response:
                        ready = response.status == 200 and TAGLINE in response.read().decode()
                except (URLError, TimeoutError, ConnectionError):
                    pass
                if ready:
                    break
                time.sleep(0.05)
            output.flush()
            output.seek(0)
            assert ready, "The launcher did not serve GET /: " + output.read()[-3000:]
            configurations = [event for event in _events(events_path) if event["kind"] == "config"]
            assert configurations and all(event["reload"] is True for event in configurations)
            before = {event["pid"] for event in _events(events_path) if event["kind"] == "loaded"}
            assert before, "The real uvicorn server must load the application"
            # Exercise actual reload, rather than only observing a reload=True argument.
            deadline = time.monotonic() + 10
            after = before
            revision, next_change = 0, 0
            while time.monotonic() < deadline and process.poll() is None:
                after = {event["pid"] for event in _events(events_path) if event["kind"] == "loaded"}
                if after - before:
                    break
                # WatchFiles installs its watcher lazily after supervisor startup.
                # Retry the change so an unusually fast worker cannot race it.
                if time.monotonic() >= next_change:
                    revision += 1
                    app_path.write_bytes(original + f"\n# Reload probe {revision}\n".encode())
                    next_change = time.monotonic() + 1
                time.sleep(0.1)
            output.flush()
            output.seek(0)
            assert after - before, "Changing app.py must reload the running application: " + output.read()[-3000:]
            for _ in range(3):
                time.sleep(0.2)
                assert process.poll() is None, "The launcher exited while it should keep serving"
                with urlopen(url, timeout=1) as response:
                    assert response.status == 200 and TAGLINE in response.read().decode()
        finally:
            _stop(process)
            app_path.write_bytes(original)
