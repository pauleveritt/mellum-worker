"""Trusted Phase 1 assertions derived from the public roadmap, never its hidden grader.

Candidate imports happen in CandidateProbe's container, not this interpreter.
Semantic hero/welcome and CDN version assertions are documented structural proxies.
"""
import ast
import fnmatch
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class Element:
    def __init__(self, tag, attrs=()):
        self.tag, self.attrs, self.children = tag, {key: value or "" for key, value in attrs}, []

    def all(self, tag):
        return [child for child in self.children if isinstance(child, Element)
                for child in ([child] if child.tag == tag else []) + child.all(tag)]

    def text(self):
        return re.sub(r"\s+", " ", " ".join(c.text() if isinstance(c, Element) else c
                                          for c in self.children)).strip()


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.root = Element("document")
        self.stack = [self.root]
        self.doctype = False
        self.feed(html)

    def handle_decl(self, decl):
        self.doctype |= decl.lower() == "doctype html"

    def handle_starttag(self, tag, attrs):
        item = Element(tag, attrs)
        self.stack[-1].children.append(item)
        if tag not in {"meta", "link", "br", "hr", "img", "input", "source", "area", "base", "wbr", "embed", "param", "track", "col"}:
            self.stack.append(item)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        self.stack[-1].children.append(text)


def guarded_reload(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    uvicorn_names = {alias.asname or "uvicorn" for n in ast.walk(tree) if isinstance(n, ast.Import)
                     for alias in n.names if alias.name == "uvicorn"}
    run_names = {alias.asname or "run" for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) and n.module == "uvicorn"
                 for alias in n.names if alias.name == "run"}
    def server_call(n):
        return isinstance(n, ast.Call) and (
            isinstance(n.func, ast.Attribute) and n.func.attr == "run"
            and isinstance(n.func.value, ast.Name) and n.func.value.id in uvicorn_names
            or isinstance(n.func, ast.Name) and n.func.id in run_names)
    guards = [n for n in ast.walk(tree) if isinstance(n, ast.If)
              and isinstance(n.test, ast.Compare) and len(n.test.ops) == 1
              and isinstance(n.test.ops[0], ast.Eq)
              and ((isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"
                    and isinstance(n.test.comparators[0], ast.Constant) and n.test.comparators[0].value == "__main__")
                   or (isinstance(n.test.left, ast.Constant) and n.test.left.value == "__main__"
                       and isinstance(n.test.comparators[0], ast.Name) and n.test.comparators[0].id == "__name__"))]
    calls = [n for n in ast.walk(tree) if server_call(n)]
    guarded = {id(n) for guard in guards for statement in guard.body for n in ast.walk(statement) if server_call(n)}
    return bool(calls) and all(id(n) in guarded and any(k.arg == "reload" and isinstance(k.value, ast.Constant)
        and k.value.value is True for k in n.keywords) for n in calls)


def evaluate(snapshot, probe, remaining):
    snapshot = Path(snapshot)
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    checks = {}
    def check(key, passed, observation):
        checks[key] = {"passed": bool(passed), "observation": str(observation)[:1200]}
    def observe(name, timeout):
        if remaining() <= 0:
            return {}
        value = probe.run(name, {}, min(timeout, remaining()))
        return value if isinstance(value, dict) else {}
    home = observe("home", 6)
    html = home.get("html", "")
    if not isinstance(html, str):
        html = ""
    doc = Document(html)
    check("fastapi_app", (snapshot / "app.py").is_file() and home.get("fastapi") is True,
          "app.py must export a FastAPI application as app")
    check("home_response", home.get("status") == 200 and "Come in. Sit down. Tell us about your human." in doc.root.text(),
          f"GET / status={home.get('status')}; must return 200 and required tagline")
    check("shared_layout", (snapshot / "templates/base.html").is_file() and isinstance(home.get("templates"), list)
          and "base.html" in home["templates"],
          "Home must render through templates/base.html")
    check("html5", doc.doctype, "Rendered page requires HTML5 doctype")
    check("english", any(n.attrs.get("lang", "").lower() == "en" for n in doc.root.all("html")),
          "html requires lang=en")
    heads = doc.root.all("head")
    head = heads[0] if heads else Element("head")
    check("viewport", any(n.attrs.get("name", "").lower() == "viewport" and
        "width=device-width" in n.attrs.get("content", "").replace(" ", "") for n in head.all("meta")),
        "head requires responsive width=device-width viewport")
    def bootstrap(url, suffix):
        return isinstance(url, str) and urlsplit(url).scheme in {"http", "https"} and bool(
            re.search(r"bootstrap(?:@|/|[-.])5(?:\D|$)", url, re.I)) and suffix in urlsplit(url).path.lower()
    check("bootstrap_css", any("stylesheet" in n.attrs.get("rel", "").lower().split() and
        bootstrap(n.attrs.get("href", ""), ".css") and re.search(r"/bootstrap(?:\.min)?\.css$",
        urlsplit(n.attrs.get("href", "")).path, re.I) for n in head.all("link")), "Bootstrap 5 CDN CSS must be in head")
    bodies = doc.root.all("body")
    children = [c for c in bodies[0].children if isinstance(c, Element)] if bodies else []
    last = children[-1] if children else Element("")
    check("bootstrap_bundle", last.tag == "script" and bootstrap(last.attrs.get("src", ""), "bootstrap.bundle")
          and urlsplit(last.attrs.get("src", "")).path.endswith(".js"), "Bootstrap 5 CDN JS bundle must end body")
    check("favicon", any("icon" in n.attrs.get("rel", "").lower().split() and
        n.attrs.get("href") == "https://www.python.org/static/favicon.ico" for n in head.all("link")),
        "head requires specified Python favicon")
    titles = observe("titles", 4)
    check("default_title", titles.get("default") == "AgentClinic", "Base title must default to AgentClinic")
    check("title_override", titles.get("overridden") is True, "A child template must be able to override page title")
    navs = doc.root.all("nav")
    anchors = [n for nav in navs for n in nav.all("a")]
    check("navbar_brand", any(n.text() == "AgentClinic" for n in anchors), "Navbar requires AgentClinic brand")
    for key, href, text in [("nav_home", "/", "home"), ("nav_complaints", "/complaints", "complaints")]:
        check(key, any(n.attrs.get("href") == href and n.text().casefold() == text for n in anchors),
              f"Navbar requires {text} link to {href}; target need not exist in Phase 1")
    tagline = "Come in. Sit down. Tell us about your human."
    sections = [n for tag in ("section", "header", "div", "main") for n in doc.root.all(tag)]
    check("hero_tagline", any(tagline in n.text() and any(n.all(tag) for tag in ("h1", "h2", "h3"))
                             for n in sections), "Structural hero proxy: content container with heading and tagline; CSS names are unrestricted")
    check("welcome_paragraph", any(n.text() and tagline not in n.text() for n in doc.root.all("p")),
          "Structural welcome proxy: nonempty paragraph separate from tagline; tone needs manual review")
    source = (snapshot / "app.py").read_text(errors="replace") if (snapshot / "app.py").is_file() else ""
    check("guarded_reload", guarded_reload(source), "uvicorn.run(reload=True) must be guarded by __name__ == __main__")
    startup = observe("startup", 12)
    launch_exit = startup.get("launch_exit_code")
    if type(launch_exit) is not int or not -255 <= launch_exit <= 255:
        launch_exit = "unknown or still running"
    log = startup.get("log_tail", startup.get("probe_error", ""))
    if not isinstance(log, str):
        log = ""
    log = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log[-4096:])
    log = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", log)
    diagnostic = json.dumps(re.sub(r"\s+", " ", log).strip()[-350:], ensure_ascii=False)
    check("startup", startup.get("ready") is True,
          "Documented uv run --frozen python app.py must serve GET / with reload; "
          f"launch exit={launch_exit}; untrusted candidate log tail: {diagnostic}")
    tests = observe("tests", 6)
    check("project_tests", tests.get("exit_code") == 0 and type(tests.get("tests")) is int
          and tests["tests"] > tests.get("skipped", tests["tests"])
          and tests.get("failures") == tests.get("errors") == 0,
          f"Full project tests must run nonempty and pass: {tests}")
    altered = [name for name, digest in manifest["base_hashes"].items()
               if not (snapshot / name).is_file() or hashlib.sha256((snapshot / name).read_bytes()).hexdigest() != digest]
    check("base_integrity", not altered, f"Frozen project inputs changed/missing: {altered}")
    pristine = set(manifest["base_hashes"])
    allowed = ["app.py", "templates/**", "tests/**", "specs/**"]
    ignored = [".venv/**", "__pycache__/**", "*.pyc", "*.log", "*.db", ".git/**", ".pytest_cache/**"]
    stray = [str(p.relative_to(snapshot)) for p in snapshot.rglob("*") if p.is_file()
             and str(p.relative_to(snapshot)) not in pristine
             and not any(fnmatch.fnmatch(str(p.relative_to(snapshot)), pattern) for pattern in allowed + ignored)]
    check("phase_layout", not stray, f"Files outside Phase 1 layout: {stray}")
    return {"status": "pass" if all(item["passed"] for item in checks.values()) else "fail", "checks": checks}
