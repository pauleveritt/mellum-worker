"""Exercise the shared oracle against real, privately mutated application builds."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

SUITES = Path(__file__).resolve().parents[1] / "suites"
PHASE1 = "test_phase1_home.py"
PHASE2 = "test_phase2_board.py"
PHASE3 = "test_phase3_add.py"
PHASE4 = "test_phase4_resolve_reopen.py"


def _workspace(tmp_path: Path, suite: str) -> Path:
    source = SUITES / suite
    shutil.copytree(source / "base", tmp_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copytree(source / "fixtures/known-good", tmp_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copytree(source / "grader", tmp_path / "grader_tests")
    return tmp_path


def _replace(workspace: Path, path: str, old: str, new: str) -> None:
    target = workspace / path
    text = target.read_text()
    assert old in text, (path, old)
    target.write_text(text.replace(old, new))


def _grade(workspace: Path, *selectors: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONPATH=str(workspace))
    for name in ("PYTEST_ADDOPTS", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"):
        env.pop(name, None)
    return subprocess.run(
        ["uv", "run", "--with", "pytest", "python", "-m", "pytest", "-q",
         "-p", "no:cacheprovider", *[f"grader_tests/{s}" for s in selectors]],
        cwd=workspace, env=env, capture_output=True, text=True, timeout=90,
    )


def _assert_rejected(result: subprocess.CompletedProcess) -> None:
    assert result.returncode == 1, result.stdout + result.stderr
    assert "FAILED" in result.stdout, result.stdout + result.stderr


@pytest.mark.parametrize("suite", ["easy", "medium", "hard"])
@pytest.mark.parametrize("defect", ["redirect", "html4", "comment_brand", "no_nav", "hidden_nav"])
def test_home_rejects_noncompliant_http_or_navigation(tmp_path, suite, defect):
    ws = _workspace(tmp_path, suite)
    if defect == "redirect":
        _replace(ws, "app.py", '@app.get("/")', '@app.get("/landing")')
        with (ws / "app.py").open("a") as stream:
            stream.write('\n@app.get("/")\ndef root_redirect():\n    return RedirectResponse("/landing")\n')
    elif defect == "html4":
        _replace(ws, "templates/base.html", "<!doctype html>", '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')
    elif defect == "comment_brand":
        _replace(ws, "templates/base.html", '>AgentClinic</a>', '><!-- AgentClinic --></a>')
    elif defect == "no_nav":
        _replace(ws, "templates/base.html", '<nav class="navbar navbar-expand navbar-dark bg-dark">', "<div>")
        _replace(ws, "templates/base.html", "</nav>", "</div>")
    else:
        _replace(ws, "templates/base.html", "<nav ", "<nav hidden ")
    _assert_rejected(_grade(ws, PHASE1))


@pytest.mark.parametrize("suite", ["medium", "hard"])
@pytest.mark.parametrize("defect", ["seed_suffix", "numeric_tokens", "nonlist"])
def test_board_rejects_inexact_seed_date_or_store(tmp_path, suite, defect):
    ws = _workspace(tmp_path, suite)
    if defect == "seed_suffix":
        _replace(ws, "models.py", '"Scope creep never ends."', '"Scope creep never ends. Extra sentence."')
    elif defect == "numeric_tokens":
        _replace(ws, "templates/complaints.html", '{{ complaint.timestamp.strftime("%Y-%m-%d") }}', '{{ complaint.timestamp.year }} | {{ complaint.timestamp.month }} | {{ complaint.timestamp.day }}')
    else:
        with (ws / "models.py").open("a") as stream:
            stream.write("\ncomplaints = tuple(complaints)\n")
    _assert_rejected(_grade(ws, PHASE2))


@pytest.mark.parametrize("suite", ["medium", "hard"])
@pytest.mark.parametrize("defect", ["disconnected", "disabled", "wrong_input_type", "drop_old"])
def test_add_rejects_unusable_form_or_dropped_records(tmp_path, suite, defect):
    ws = _workspace(tmp_path, suite)
    if defect == "disconnected":
        _replace(ws, "templates/complaints.html", '<form method="post" action="/complaints" class="mt-4">', '<form method="post" action="/complaints" class="mt-4"></form>')
    elif defect == "disabled":
        _replace(ws, "templates/complaints.html", 'name="agent_name" required', 'name="agent_name" disabled required')
    elif defect == "wrong_input_type":
        _replace(ws, "templates/complaints.html", 'type="text" class="form-control"', 'type="hidden" class="form-control"')
    else:
        _replace(ws, "app.py", "complaints.append(Complaint(agent_name, text))", "complaints.append(Complaint(agent_name, text))\n    complaints[:] = complaints[-5:]")
    _assert_rejected(_grade(ws, PHASE3))


@pytest.mark.parametrize("suite", ["medium", "hard"])
@pytest.mark.parametrize("defect", ["no_model_state", "global_state", "no_controls", "disabled_controls", "roundtrip_order", "seed_order"])
def test_transitions_reject_false_state_controls_or_reordering(tmp_path, suite, defect):
    ws = _workspace(tmp_path, suite)
    if defect == "no_model_state":
        _replace(ws, "app.py", "complaint.status = status", "pass")
        _replace(ws, "templates/complaints.html", '{{ complaint.text }}', '{{ complaint.text }} Open Resolved')
    elif defect == "global_state":
        _replace(ws, "app.py", "complaint.status = status", "for item in complaints:\n                item.status = status")
    elif defect == "no_controls":
        _replace(ws, "templates/complaints.html", '<button type="submit" class="btn btn-sm', '<button type="button" class="btn btn-sm')
    elif defect == "disabled_controls":
        _replace(ws, "templates/complaints.html", '<button type="submit" class="btn btn-sm', '<button disabled type="submit" class="btn btn-sm')
    elif defect == "roundtrip_order":
        _replace(ws, "app.py", "complaint.status = status", "complaint.status = status\n            complaints.reverse()")
    else:
        _replace(ws, "app.py", "complaint.status = status", "complaint.status = status\n            complaints[0], complaints[1] = complaints[1], complaints[0]")
    _assert_rejected(_grade(ws, PHASE4))


@pytest.mark.parametrize("suite", ["medium", "hard"])
@pytest.mark.parametrize("defect", ["string", "float", "reset_after_seed"])
def test_identity_rejects_noninteger_or_reused_seed_ids(tmp_path, suite, defect):
    ws = _workspace(tmp_path, suite)
    if defect == "reset_after_seed":
        with (ws / "models.py").open("a") as stream:
            stream.write("\n_ids = count(1)\n")
    else:
        _replace(ws, "models.py", "next(_ids)", f"{defect if defect == 'float' else 'str'}(next(_ids))")
    _assert_rejected(_grade(ws, f"{PHASE4}::test_complaint_identity_is_stable_and_keyword_only", f"{PHASE4}::test_seed_complaints_have_distinct_ids"))


@pytest.mark.parametrize("suite", ["medium", "hard"])
@pytest.mark.parametrize("alternative", ["newest_first", "post_init_timestamp", "associated_external_controls", "textual_date", "inline_brand"])
def test_shared_contract_accepts_valid_alternatives(tmp_path, suite, alternative):
    ws = _workspace(tmp_path, suite)
    if alternative == "inline_brand":
        _replace(ws, "templates/base.html", ">AgentClinic</a>", ">Agent<strong>Clinic</strong></a>")
    elif alternative == "newest_first":
        _replace(ws, "templates/complaints.html", '{% for complaint in complaints %}', '{% for complaint in complaints|reverse %}')
    elif alternative == "post_init_timestamp":
        _replace(ws, "models.py", "timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))", "timestamp: datetime = None")
        _replace(ws, "models.py", 'status: str = "open"', 'status: str = "open"\n\n    def __post_init__(self):\n        if self.timestamp is None:\n            self.timestamp = datetime.now(timezone.utc)')
    elif alternative == "associated_external_controls":
        _replace(ws, "templates/complaints.html", '<form method="post" action="/complaints" class="mt-4">', '<form id="add" method="post" action="/complaints" class="mt-4"></form>')
        _replace(ws, "templates/complaints.html", 'name="agent_name"', 'form="add" name="agent_name"')
        _replace(ws, "templates/complaints.html", 'name="text"', 'form="add" name="text"')
        _replace(ws, "templates/complaints.html", '<button type="submit" class="btn btn-primary">', '<button form="add" type="submit" class="btn btn-primary">')
    else:
        _replace(ws, "templates/complaints.html", '%Y-%m-%d', '%B %d, %Y')
    result = _grade(ws, PHASE1, PHASE2, PHASE3, PHASE4)
    assert result.returncode == 0, result.stdout + result.stderr


def test_shared_graders_tolerate_prior_archives_in_direct_module_order(tmp_path):
    ws = _workspace(tmp_path, "hard")
    result = _grade(ws, "test_phase5.py", PHASE3, PHASE2, PHASE4, PHASE1)
    assert result.returncode == 0, result.stdout + result.stderr
