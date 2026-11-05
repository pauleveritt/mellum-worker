"""Fixed observation operations, run ONLY in the untrusted candidate container.

There are no acceptance assertions, expected task values or oracle tests here.
"""
import contextlib
import io
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


class Titles(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.active = False; self.title = ""; self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag == "title": self.active = True
    def handle_endtag(self, tag):
        if tag == "title": self.active = False
    def handle_data(self, text):
        if self.active: self.title += text


def home():
    sys.path.insert(0, str(Path.cwd()))
    import jinja2
    loaded = []
    original = jinja2.Environment.get_template
    def tracking(self, name, *args, **kwargs):
        loaded.append(str(name)); return original(self, name, *args, **kwargs)
    jinja2.Environment.get_template = tracking
    from app import app
    from fastapi import FastAPI
    from starlette.testclient import TestClient
    with TestClient(app) as client:
        response = client.get("/")
    return {"fastapi": isinstance(app, FastAPI), "status": response.status_code,
            "html": response.text, "templates": loaded}


def titles():
    from jinja2 import Environment, FileSystemLoader, nodes
    environment = Environment(loader=FileSystemLoader("templates"))
    source = environment.loader.get_source(environment, "base.html")[0]
    tree = environment.parse(source)
    context = {"request": type("Request", (), {"url_for": lambda *a, **k: ""})()}
    default = Titles(environment.get_template("base.html").render(**context)).title.strip()
    marker = "probe-" + uuid.uuid4().hex
    overridden = False
    for node in tree.find_all(nodes.Block):
        child = '{% extends "base.html" %}{% block ' + node.name + ' %}' + marker + '{% endblock %}'
        rendered = environment.from_string(child).render(**context)
        overridden |= Titles(rendered).title.strip() == marker
    return {"default": default, "overridden": overridden}


def startup():
    log = Path("/tmp/probe-startup.log")
    with log.open("w") as output:
        child = subprocess.Popen(["uv", "run", "--offline", "--frozen", "python", "app.py"],
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        ready = False
        try:
            until = time.monotonic() + 9
            while child.poll() is None and time.monotonic() < until:
                match = re.search(r"http://(?:0\.0\.0\.0|127\.0\.0\.1|localhost|\[::\]):(\d+)", log.read_text())
                if match:
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{match[1]}/", timeout=.3) as response:
                            if response.status == 200:
                                ready = True; break
                    except OSError:
                        pass
                time.sleep(.1)
        finally:
            try: os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=1)
    return {"ready": ready, "exit_code": child.returncode}


def tests():
    result = subprocess.run(["uv", "run", "--offline", "--frozen", "python", "-m", "pytest", "tests", "-q",
        "--junitxml=/tmp/probe-tests.xml"], capture_output=True, timeout=5)
    path = Path("/tmp/probe-tests.xml")
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    if path.is_file():
        suites = list(ET.parse(path).getroot().iter("testsuite"))
        totals = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in totals}
    return {"exit_code": result.returncode, **totals}


if __name__ == "__main__":
    operations = {"home": home, "titles": titles, "startup": startup, "tests": tests}
    try:
        json.loads(sys.stdin.read())
        # Candidate prints cannot masquerade as the observation envelope.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            observation = operations[sys.argv[1]]()
    except Exception as error:
        observation = {"probe_error": f"{type(error).__name__}: {error}"[:1000]}
    print(json.dumps(observation))
