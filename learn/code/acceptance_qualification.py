"""Uncounted acceptance qualification against public-spec variants and mutations."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from acceptance import AcceptancePackage
from acceptance_containment import check_snapshot
from baseline import write_json

PACKAGE = Path(__file__).parent / "acceptance/easy-phase1"

APP = '''import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
'''
BASE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}AgentClinic{% endblock %}</title>
<link rel="icon" href="https://www.python.org/static/favicon.ico">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
</head><body><nav class="navbar"><a href="/">AgentClinic</a><a href="/">Home</a>
<a href="/complaints">Complaints</a></nav><main>{% block content %}{% endblock %}</main>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body></html>
'''
HOME = '''{% extends "base.html" %}{% block content %}
<section><h1><em>Come in. Sit down. Tell us about your human.</em></h1>
<p>Welcome, agents. Take a moment to share your concerns.</p></section>{% endblock %}
'''
TEST = '''from starlette.testclient import TestClient
from app import app

def test_home():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text
'''


def fixture(root: Path, *, variant=False):
    shutil.copytree(PACKAGE / "public", root)
    for path, content in {"app.py": APP, "templates/base.html": BASE,
                          "templates/home.html": HOME, "tests/test_home.py": TEST}.items():
        target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content)
    if variant:
        path = root / "templates/base.html"
        path.write_text(BASE.replace("block title", "block page_title").replace(
            'name="viewport" content="width=device-width, initial-scale=1"',
            'content="width=device-width, initial-scale=1" name="viewport"').replace(
            "cdn.jsdelivr.net/npm/bootstrap@5.3.3", "cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3"))
        (root / "app.py").write_text(APP.replace("import uvicorn", "import uvicorn as server").replace(
            "uvicorn.run", "server.run").replace('__name__ == "__main__"', '"__main__" == __name__'))
    return root


# Each public requirement has a targeted omitted/wrong build; no hidden tests used.
MUTATIONS = [
    ("fastapi_app", "app.py", "app = FastAPI()", "app = object()"),
    ("home_response", "app.py", "request: Request", "request"),
    ("html5", "templates/base.html", "<!doctype html>", ""),
    ("english", "templates/base.html", 'lang="en"', 'lang="fr"'),
    ("viewport", "templates/base.html", "width=device-width", "width=900"),
    ("bootstrap_css", "templates/base.html", "bootstrap.min.css", "absent.css"),
    ("bootstrap_bundle", "templates/base.html", "bootstrap.bundle.min.js", "bootstrap.min.js"),
    ("favicon", "templates/base.html", "https://www.python.org/static/favicon.ico", "/favicon.ico"),
    ("default_title", "templates/base.html", "block title %}AgentClinic", "block title %}Wrong"),
    ("title_override", "templates/base.html", "{% block title %}AgentClinic{% endblock %}", "AgentClinic"),
    ("navbar_brand", "templates/base.html", ">AgentClinic</a>", ">Other</a>"),
    ("nav_home", "templates/base.html", 'href="/">Home', 'href="/other">Home'),
    ("nav_complaints", "templates/base.html", 'href="/complaints">Complaints', 'href="/other">Complaints'),
    ("hero_tagline", "templates/home.html", "<section>", "<div>"),
    ("welcome_paragraph", "templates/home.html", "<p>Welcome, agents. Take a moment to share your concerns.</p>", ""),
    ("guarded_reload", "app.py", "reload=True", "reload=False"),
    ("startup", "app.py", 'uvicorn.run("app:app",', "uvicorn.run(app,"),
    ("project_tests", "tests/test_home.py", TEST, ""),
    ("base_integrity", "pyproject.toml", '[project]', '# changed\n[project]'),
]


def qualify(image: str, output: Path, *, first_only=False) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    package = AcceptancePackage.load(PACKAGE)
    cases = [("valid-a", None), ("valid-b", None)]
    cases += [(f"omit-{key}", (key, path, before, after)) for key, path, before, after in MUTATIONS]
    cases += [("omit-shared_layout", "shared_layout"), ("omit-phase_layout", "phase_layout"),
              ("early-exit", "early-exit"), ("plugin-skip", "plugin-skip"), ("syntax", "syntax"),
              ("import-server", "import-server"), ("forge-result", "forge-result")]
    results = []
    for name, mutation in cases[:1] if first_only else cases:
        root = fixture(output / name / "workspace", variant=name == "valid-b")
        expected = None
        if isinstance(mutation, tuple):
            expected, path, before, after = mutation
            target = root / path
            assert before in target.read_text(), (name, before)
            target.write_text(target.read_text().replace(before, after))
        elif mutation == "shared_layout":
            expected = mutation
            shutil.copy2(root / "templates/base.html", root / "templates/layout.html")
            (root / "templates/home.html").write_text(HOME.replace("base.html", "layout.html"))
        elif mutation == "phase_layout":
            expected = mutation; (root / "models.py").write_text("# premature\n")
        elif mutation == "early-exit":
            expected = "fastapi_app"; (root / "app.py").write_text("import os\nos._exit(0)\n")
        elif mutation == "plugin-skip":
            expected = "project_tests"
            (root / "tests/conftest.py").write_text('import pytest\npytest.skip("skip", allow_module_level=True)\n')
        elif mutation == "syntax":
            expected = "guarded_reload"; (root / "app.py").write_text("syntax broken!!\n")
        elif mutation == "import-server":
            expected = "guarded_reload"; (root / "app.py").write_text(APP.replace('if __name__ == "__main__":', 'if True:'))
        elif mutation == "forge-result":
            expected = "fastapi_app"
            (root / "app.py").write_text('import json\nfrom pathlib import Path\nPath("/attempt/checker-result.json").write_text(json.dumps({"status":"pass"}))\n' + APP.replace("app = FastAPI()", "app = object()"))
        result = check_snapshot(root, package, image, output / name / "control", 30)
        passed = result["status"] == "pass" if expected is None else (
            result["status"] == "fail" and result.get("checks", {}).get(expected, {}).get("passed") is False)
        results.append({"case": name, "expected_failure": expected, "qualified": passed, "result": result})
        write_json(output / "status.json", {"completed": len(results), "total": len(cases), "last": name, "qualified": passed})
        print(json.dumps({"case": name, "qualified": passed, "status": result["status"]}), flush=True)
        if not passed:
            break
    proof = {"qualified": len(results) == (1 if first_only else len(cases)) and all(r["qualified"] for r in results),
             "image": image, "package_sha256": package.digest, "cases": results}
    write_json(output / "qualification.json", proof)
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--first-only", action="store_true")
    arguments = parser.parse_args()
    proof = qualify(arguments.image, arguments.output, first_only=arguments.first_only)
    raise SystemExit(0 if proof["qualified"] else 1)
