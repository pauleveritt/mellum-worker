"""Easy's written Phase 1 acceptance is enforced, with alternative valid builds."""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness


SUITE = harness.load_suite(harness.SUITES, "easy")
PREFIX = "grader_tests/test_phase1_acceptance.py::"


def workspace(tmp_path):
    shutil.copytree(SUITE.root / "base", tmp_path, dirs_exist_ok=True)
    shutil.copytree(SUITE.root / "fixtures/known-good", tmp_path, dirs_exist_ok=True)
    return tmp_path


def change(root, path, old, new):
    target = root / path
    original = target.read_text()
    assert old in original
    target.write_text(original.replace(old, new))


def grade_check(root, check):
    """Select the shipped check, avoiding unrelated independent app copies."""
    with tempfile.TemporaryDirectory(prefix="easy-check-") as temporary:
        grader = Path(temporary)
        for path in SUITE.tests.glob("*.py"):
            if not path.name.startswith("test_"):
                shutil.copyfile(path, grader / path.name)
        source = SUITE.tests / "test_phase1_acceptance.py"
        shutil.copyfile(source, grader / "_phase1_acceptance.py")
        (grader / source.name).write_text(f"from grader_tests._phase1_acceptance import {check}\n")
        selected = replace(SUITE, tests=grader, expected=(PREFIX + check,))
        return harness.score_workspace_details(root, selected)


MUTANTS = [
    ("viewport-missing", "templates/base.html", '<meta name="viewport" content="width=device-width, initial-scale=1">', "", "test_layout_has_responsive_viewport"),
    ("viewport-fixed", "templates/base.html", "width=device-width", "width=1024", "test_layout_has_responsive_viewport"),
    ("css-v4", "templates/base.html", "bootstrap@5.3.3/dist/css", "bootstrap@4.6.2/dist/css", "test_layout_has_bootstrap5_cdn_stylesheet_in_head"),
    ("css-local", "templates/base.html", "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css", "/static/bootstrap.min.css", "test_layout_has_bootstrap5_cdn_stylesheet_in_head"),
    ("css-body", "templates/base.html", '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">', "", "test_layout_has_bootstrap5_cdn_stylesheet_in_head"),
    ("favicon", "templates/base.html", "https://www.python.org/static/favicon.ico", "/favicon.ico", "test_layout_has_python_favicon"),
    ("js-not-bundle", "templates/base.html", "bootstrap.bundle.min.js", "bootstrap.min.js", "test_layout_ends_body_with_bootstrap5_cdn_bundle"),
    ("js-v4", "templates/base.html", "bootstrap@5.3.3/dist/js", "bootstrap@4.6.2/dist/js", "test_layout_ends_body_with_bootstrap5_cdn_bundle"),
    ("js-head", "templates/base.html", '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>', "", "test_layout_ends_body_with_bootstrap5_cdn_bundle"),
    ("js-not-last", "templates/base.html", "</body>", "<footer>After the bundle</footer></body>", "test_layout_ends_body_with_bootstrap5_cdn_bundle"),
    ("title-default", "templates/base.html", "{% block title %}AgentClinic{% endblock %}", "{% block title %}Wrong default{% endblock %}", "test_layout_title_defaults_to_agentclinic"),
    ("title-fixed", "templates/base.html", "{% block title %}AgentClinic{% endblock %}", "AgentClinic", "test_extending_page_can_override_layout_title"),
    ("no-hero", "templates/home.html", '<section class="p-5 mb-4 bg-light rounded-3">', "", "test_home_has_hero_and_welcoming_paragraph"),
    ("no-welcome", "templates/home.html", '<p class="lead">Welcome to AgentClinic, a quiet place where AI agents can finally get their gripes off their chests.</p>', "", "test_home_has_hero_and_welcoming_paragraph"),
    ("reload-off", "app.py", "reload=True", "reload=False", "test_main_guard_launches_uvicorn_with_reload_and_keeps_serving"),
    ("no-launcher", "app.py", 'if __name__ == "__main__":\n    uvicorn.run("app:app", reload=True)', "", "test_main_guard_launches_uvicorn_with_reload_and_keeps_serving"),
    ("exits-early", "app.py", 'uvicorn.run("app:app", reload=True)', "raise SystemExit(0)", "test_main_guard_launches_uvicorn_with_reload_and_keeps_serving"),
]


@pytest.mark.parametrize("name,path,old,new,check", MUTANTS, ids=[row[0] for row in MUTANTS])
def test_missing_acceptance_item_is_rejected(tmp_path, name, path, old, new, check):
    root = workspace(tmp_path)
    change(root, path, old, new)
    if name == "css-body":
        change(root, path, "<body>", '<body><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">')
    elif name == "js-head":
        change(root, path, "</head>", '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script></head>')
    elif name == "no-hero":
        change(root, path, "</section>", "")
    passed, output, missing, ran = grade_check(root, check)
    assert ran, output
    assert not passed, output
    assert PREFIX + check in missing, output


def test_home_must_extend_and_render_the_named_shared_layout(tmp_path):
    root = workspace(tmp_path)
    base = (root / "templates/base.html").read_text()
    content = (root / "templates/home.html").read_text().split("{% block content %}", 1)[1].rsplit("{% endblock %}", 1)[0]
    standalone = base.replace("{% block content %}{% endblock %}", content)
    (root / "templates/home.html").write_text(standalone)
    passed, output, missing, ran = grade_check(root, "test_home_renders_home_template_extending_shared_base")
    assert ran, output
    assert not passed, output
    assert PREFIX + "test_home_renders_home_template_extending_shared_base" in missing, output


def test_inline_html_cannot_substitute_for_home_template(tmp_path):
    root = workspace(tmp_path)
    change(root, "app.py", 'return templates.TemplateResponse(request, "home.html")', 'return __import__("fastapi.responses", fromlist=["HTMLResponse"]).HTMLResponse(\'<!doctype html><html lang="en"><nav>AgentClinic <a href="/">Home</a><a href="/complaints">Complaints</a></nav><section>Come in. Sit down. Tell us about your human.<p>Hello, agents.</p></section></html>\')')
    passed, output, missing, ran = grade_check(root, "test_home_renders_home_template_extending_shared_base")
    assert ran, output
    assert not passed, output
    assert PREFIX + "test_home_renders_home_template_extending_shared_base" in missing, output


def test_assets_belong_to_shared_layout_not_only_home(tmp_path):
    root = workspace(tmp_path)
    stylesheet = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">'
    change(root, "templates/base.html", stylesheet, "{% block page_head %}{% endblock %}")
    change(root, "templates/home.html", '{% extends "base.html" %}', '{% extends "base.html" %}{% block page_head %}' + stylesheet + "{% endblock %}")
    check = "test_layout_has_bootstrap5_cdn_stylesheet_in_head"
    passed, output, missing, ran = grade_check(root, check)
    assert ran, output
    assert not passed, output
    assert PREFIX + check in missing, output


def test_layout_can_use_route_supplied_non_title_context(tmp_path):
    root = workspace(tmp_path)
    change(root, "templates/base.html", '>AgentClinic</a>', '>{{ organization.brand }}</a>')
    change(root, "app.py", 'return templates.TemplateResponse(request, "home.html")', 'return templates.TemplateResponse(request, "home.html", {"organization": {"brand": "AgentClinic"}})')
    passed, output, _, _ = grade_check(root, "test_layout_title_defaults_to_agentclinic")
    assert passed, output


@pytest.mark.parametrize("mechanism", ["renamed-block", "child-variable", "config-server", "manual-render", "div-hero", "protocol-relative-cdn", "nested-head", "dynamic-extends"])
def test_alternate_valid_layouts_and_launchers_pass(tmp_path, mechanism):
    root = workspace(tmp_path)
    change(root, "templates/home.html", 'class="p-5 mb-4 bg-light rounded-3"', 'aria-label="A place for agents"')
    change(root, "templates/home.html", "Welcome to AgentClinic, a quiet place where AI agents can finally get their gripes off their chests.", "Hello, agents. Take a seat and share what brought you here.")
    if mechanism == "renamed-block":
        change(root, "templates/base.html", "block title", "block browser_caption")
    elif mechanism == "child-variable":
        change(root, "templates/base.html", "{% block title %}AgentClinic{% endblock %}", "{{ browser_caption | default('AgentClinic') }}")
    elif mechanism == "config-server":
        change(root, "app.py", 'uvicorn.run("app:app", reload=True)', 'from uvicorn.supervisors import ChangeReload\n    config = uvicorn.Config("app:app", reload=True)\n    server = uvicorn.Server(config)\n    sock = config.bind_socket()\n    ChangeReload(config, target=server.run, sockets=[sock]).run()')
    elif mechanism == "manual-render":
        change(root, "app.py", 'return templates.TemplateResponse(request, "home.html")', 'return __import__("fastapi.responses", fromlist=["HTMLResponse"]).HTMLResponse(templates.env.get_template("home.html").render(request=request))')
    elif mechanism == "div-hero":
        change(root, "templates/home.html", "<section", "<div")
        change(root, "templates/home.html", "</section>", "</div>")
    elif mechanism == "protocol-relative-cdn":
        change(root, "templates/base.html", "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/", "//cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.3/")
    elif mechanism == "nested-head":
        change(root, "templates/base.html", "<head>", "<head>{% block shared_head %}")
        change(root, "templates/base.html", "</head>", "{% endblock %}</head>")
    else:
        change(root, "templates/home.html", '{% extends "base.html" %}', '{% extends layout_name %}')
        change(root, "app.py", 'return templates.TemplateResponse(request, "home.html")', 'return templates.TemplateResponse(request, "home.html", {"layout_name": "base.html"})')
    passed, output = harness.score_workspace(root, SUITE)
    assert passed, output


def test_known_good_still_passes_all_phase1_acceptance(tmp_path):
    root = workspace(tmp_path)
    passed, output = harness.score_workspace(root, SUITE)
    assert passed, output


def test_launcher_group_stops_if_grading_parent_exits(tmp_path):
    root = workspace(tmp_path / "app")
    trusted = tmp_path / "trusted"
    shutil.copytree(SUITE.tests, trusted / "grader_tests")
    events = tmp_path / "events.jsonl"
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = harness.grade_env(root) | {
        "EASY_LAUNCH_PORT": str(port), "EASY_LAUNCH_EVENTS": str(events),
        "PYTHONPATH": os.pathsep.join([str(trusted), str(root)]),
    }
    parent_code = '''
import json, os, subprocess, sys, time
from pathlib import Path
options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
child = subprocess.Popen([sys.executable, "-c", "from grader_tests._easy_launcher import run; run()"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
events = Path(os.environ["EASY_LAUNCH_EVENTS"])
deadline = time.monotonic() + 10
while time.monotonic() < deadline:
    if events.exists() and '"kind": "loaded"' in events.read_text():
        break
    time.sleep(0.05)
print(json.dumps({"pid": child.pid, "loaded": events.exists() and '"kind": "loaded"' in events.read_text()}))
'''
    parent = subprocess.run(["uv", "run", "--frozen", "python", "-c", parent_code], cwd=root, env=environment, capture_output=True, text=True, timeout=15)
    assert parent.returncode == 0, parent.stderr
    result = json.loads(parent.stdout)
    pid = result["pid"]
    try:
        assert result["loaded"], parent.stdout
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and harness.group_members(pid):
            time.sleep(0.1)
        assert not harness.group_members(pid), "Launcher processes survived their grading parent"
    finally:
        harness.kill_tree(pid)
