"""Run every F.7 witness build through each acceptance checker and record the verdicts.

No model runs. `uv run python learn/code/qualify_matrix.py` compares with the committed result;
`--write` regenerates it. The mediated column leaves out the two checks that start a real server:
no witness concerns launching, and they cannot run side by side on one port.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grader_history
import harness
from grading import evaluate

EVIDENCE = harness.CODE.parents[1] / "docs/superpowers/research/2026-11-09-f7-qualify-acceptance"
SOURCES = EVIDENCE / "sources"
OPEN_BADGE, RESOLVED_BADGE = '<span class="badge text-bg-warning">Open</span>', '<span class="badge text-bg-secondary">Resolved</span>'
BOARD, BASE, ROUTE_ADD = "templates/complaints.html", "templates/base.html", "complaints.append(Complaint(agent_name, text))"
STATUS_LINE = "complaint.status = status"
NOT_SERVER = "not running_app_py"


def badges(shape):
    return [(BOARD, OPEN_BADGE, shape.format("Open")), (BOARD, RESOLVED_BADGE, shape.format("Resolved"))]


POST_INIT = [("models.py", "id: int = field(default_factory=lambda: next(_ids))", "id: int = None"),
             ("models.py", 'status: str = "open"\n', 'status: str = "open"\n\n    def __post_init__(self):\n        if self.id is None:\n            self.id = next(_ids)\n')]
SEPARATE = [("app.py", ROUTE_ADD, "complaint = Complaint(agent_name, text)\n    complaint.id = next(_route_ids)\n    complaints.append(complaint)"),
            ("app.py", "app = FastAPI()", "from itertools import count\n_route_ids = count(1_000_000)\n\napp = FastAPI()")]
RENUMBER = [("app.py", ROUTE_ADD, ROUTE_ADD + "\n    for index, item in enumerate(complaints, start=1):\n        item.id = index")]
OVERWRITE = [("app.py", ROUTE_ADD, "complaint = Complaint(agent_name, text)\n    complaint.id = max(item.id for item in complaints) + 1\n    complaints.append(complaint)")]
NAVLESS = [(BASE, '<nav class="navbar navbar-expand navbar-dark bg-dark">', "<div>"), (BASE, "</nav>", "</div>")]
REDIRECT = [("app.py", '@app.get("/")', '@app.get("/landing")'),
            ("app.py", 'if __name__ == "__main__":', '@app.get("/")\ndef root_redirect():\n    return RedirectResponse("/landing")\n\n\nif __name__ == "__main__":')]

# (suite, name): (kind, base build, edits)
MEDIUM_VALID = {
    "known_good": [], "caption": badges("<p>Status: {}</p>"), "strong_caption": badges("<p><strong>Status:</strong> {}</p>"),
    "state_caption": badges("<div>State: {}</div>"), "post_init_counter": POST_INIT,
    "emphasised_word_after_text": badges("<p>Filed under: <strong>{}</strong></p>"),
    "comment_in_card": [(BOARD, '<div class="card-body">', '<div class="card-body">\n<!-- one complaint -->')],
    "newest_first": [(BOARD, "{% for complaint in complaints %}", "{% for complaint in complaints|reverse %}")],
    "textual_date": [(BOARD, "%Y-%m-%d", "%B %d, %Y")],
    "inline_brand": [(BASE, ">AgentClinic</a>", ">Agent<strong>Clinic</strong></a>")],
}
MEDIUM_DEFECT = {
    "separate_route_counter": SEPARATE, "renumber_on_append": RENUMBER, "route_overwrites_with_max": OVERWRITE,
    "negated_caption": badges("<p>Status: Not {}</p>"), "negated_strong": badges("<p>Not <strong>{}</strong></p>"),
    "negated_span": badges("<p>Not <span>{}</span></p>"),
    "hidden_label": badges("<p hidden>Status: {}</p>"),
    "both_labels": badges("<p>Status: {}</p><p>Open</p><p>Resolved</p>"),
    "state_never_changes": [(BOARD, RESOLVED_BADGE, OPEN_BADGE)],
    "redirect_home": REDIRECT,
    "redirect_board": [("app.py", '@app.get("/complaints")', '@app.get("/board")'), ("app.py", 'if __name__ == "__main__":', '@app.get("/complaints")\ndef board_redirect():\n    return RedirectResponse("/board")\n\n\nif __name__ == "__main__":')],
    "html4_doctype": [(BASE, "<!doctype html>", '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')],
    "brand_in_comment": [(BASE, ">AgentClinic</a>", "><!-- AgentClinic --></a>")], "no_nav": NAVLESS, "hidden_nav": [(BASE, "<nav ", "<nav hidden ")],
    "seed_suffix": [("models.py", '"Scope creep never ends."', '"Scope creep never ends. Extra sentence."')],
    "date_tokens": [(BOARD, '{{ complaint.timestamp.strftime("%Y-%m-%d") }}', "{{ complaint.timestamp.year }} | {{ complaint.timestamp.month }} | {{ complaint.timestamp.day }}")],
    "disconnected_form": [(BOARD, '<form method="post" action="/complaints" class="mt-4">', '<form method="post" action="/complaints" class="mt-4"></form>')],
    "disabled_input": [(BOARD, 'name="agent_name" required', 'name="agent_name" disabled required')],
    "fieldset_disabled": [(BOARD, '<form method="post" action="/complaints" class="mt-4">', '<form method="post" action="/complaints" class="mt-4"><fieldset disabled>'), (BOARD, "Submit</button>\n</form>", "Submit</button>\n</fieldset></form>")],
    "hidden_name_input": [(BOARD, 'name="agent_name" required', 'name="agent_name" hidden required')],
    "hidden_input": [(BOARD, 'type="text" class="form-control"', 'type="hidden" class="form-control"')],
    "truncating_store": [("app.py", ROUTE_ADD, ROUTE_ADD + "\n    complaints[:] = complaints[-5:]")],
    "no_model_state": [("app.py", STATUS_LINE, "pass"), (BOARD, "{{ complaint.text }}", "{{ complaint.text }} Open Resolved")],
    "changes_every_complaint": [("app.py", STATUS_LINE, "for item in complaints:\n                item.status = status")],
    "buttons_do_not_submit": [(BOARD, '<button type="submit" class="btn btn-sm', '<button type="button" class="btn btn-sm')],
    "disabled_buttons": [(BOARD, '<button type="submit" class="btn btn-sm', '<button disabled type="submit" class="btn btn-sm')],
    "reverses_board": [("app.py", STATUS_LINE, STATUS_LINE + "\n            complaints.reverse()")],
    "swaps_seed_order": [("app.py", STATUS_LINE, STATUS_LINE + "\n            complaints[0], complaints[1] = complaints[1], complaints[0]")],
    "string_ids": [("models.py", "next(_ids)", "str(next(_ids))")], "float_ids": [("models.py", "next(_ids)", "float(next(_ids))")],
}
EASY_VALID = {
    "known_good": [], "inline_brand": [(BASE, ">AgentClinic</a>", ">Agent<strong>Clinic</strong></a>")],
    "home_html_response": [("app.py", 'return templates.TemplateResponse(request, "home.html")', 'return HTMLResponse(templates.get_template("home.html").render(request=request))'),
                           ("app.py", "from fastapi.responses import RedirectResponse", "from fastapi.responses import HTMLResponse, RedirectResponse")],
}
EASY_DEFECT = {
    "redirect_home": REDIRECT, "no_nav": NAVLESS, "hidden_nav": [(BASE, "<nav ", "<nav hidden ")],
    "no_title": [(BASE, "<title>{% block title %}AgentClinic{% endblock %}</title>", "")],
    "no_viewport": [(BASE, '<meta name="viewport" content="width=device-width, initial-scale=1">', "")],
    "home_without_layout": [("templates/home.html", '{% extends "base.html" %}', "")],
}


def witnesses():
    for suite, valid, defect in (("medium", MEDIUM_VALID, MEDIUM_DEFECT), ("easy", EASY_VALID, EASY_DEFECT)):
        for kind, group in (("valid", valid), ("defect", defect)):
            for name, edits in group.items():
                yield suite, name, kind, edits
    for name in ("base-r02", "base-r03"):
        yield "medium", name, "defect", name


def load(suite: str):
    return harness.load_suite(harness.SUITES, suite)


def build(suite_name: str, edits, root: Path) -> Path:
    suite = load(suite_name)
    shutil.copytree(suite.root / "base", root, dirs_exist_ok=True)
    fixture = suite.root / "fixtures" / ("witnesses/" + edits if isinstance(edits, str) else "known-good")
    shutil.copytree(fixture, root, dirs_exist_ok=True)
    for path, old, new in ([] if isinstance(edits, str) else edits):
        target = root / path
        assert old in target.read_text(), (path, old)
        target.write_text(target.read_text().replace(old, new))
    return root


def pytest_rejects(root: Path, target: Path, keyword: str | None = None) -> bool:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONPATH=str(root))
    command = ["uv", "run", "--frozen", "--with", "pytest", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", str(root), str(target)]
    if keyword:
        command += ["-k", keyword]
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=240)
    assert result.returncode in (0, 1), result.stdout + result.stderr
    return result.returncode == 1


def graded(root: Path, suite) -> str:
    result = evaluate(root, suite)
    return "pass" if result["checks_ran"] and not result["missing"] else "reject"


def andre_grader(suite_name: str):
    suite = load(suite_name)
    source = SOURCES / suite_name
    return replace(suite, tests=source / "grader", expected=tuple(json.loads((source / "expected.json").read_text())), grader_revision="andre-67f0138f")


def checkers(suite_name: str) -> dict:
    suite = load(suite_name)
    mediated_root = suite.root / "mediated"
    table = {"current": lambda root: graded(root, suite)}
    if suite_name == "medium":
        table["original_658bbea5"] = lambda root: graded(root, grader_history.select_grader(suite, "658bbea5"))
        table["andre_test_medium"] = lambda root: "reject" if pytest_rejects(root, SOURCES / "test_medium.py") else "pass"
    table["mediated"] = lambda root: "reject" if pytest_rejects(root, mediated_root, NOT_SERVER) else "pass"
    table["andre_grader"] = lambda root: graded(root, andre_grader(suite_name))
    return table


def verdict(job) -> tuple:
    suite, name, kind, edits, checker, run = job
    with tempfile.TemporaryDirectory(prefix="f7-matrix-") as directory:
        return suite, name, kind, checker, run(build(suite, edits, Path(directory)))


def compute() -> dict:
    jobs = [(suite, name, kind, edits, checker, run)
            for suite, name, kind, edits in witnesses() for checker, run in checkers(suite).items()]
    result: dict = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for suite, name, kind, checker, outcome in pool.map(verdict, jobs):
            result.setdefault(suite, {}).setdefault(name, {"kind": kind})[checker] = outcome
    return result


def markdown(result: dict) -> str:
    out = ["# F.7 qualification matrix", "", "Generated by `learn/code/qualify_matrix.py`; do not edit.", ""]
    for suite, rows in result.items():
        columns = [c for c in next(iter(rows.values())) if c != "kind"]
        out += [f"## {suite.capitalize()}", "", "| witness | kind | " + " | ".join(columns) + " |", "|---|---|" + "---|" * len(columns)]
        out += [f"| {name} | {row['kind']} | " + " | ".join(row[c] for c in columns) + " |" for name, row in rows.items()]
        out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = compute()
    print(markdown(result))
    path = EVIDENCE / "matrix.json"
    if args.write:
        path.write_text(json.dumps(result, indent=1) + "\n")
        (EVIDENCE / "matrix.md").write_text(markdown(result))
        return 0
    return 0 if path.is_file() and json.loads(path.read_text()) == result else 1


if __name__ == "__main__":
    raise SystemExit(main())
