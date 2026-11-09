"""F.8: one requested phase, graded on its own scope and every earlier one, never a later one."""
import shutil
from pathlib import Path

import pytest

import harness
import phase_boundary
from grader_history import grader_identity, select_grader
from grading import evaluate
from test_phase_acceptance import EASY_DIGEST, ORIGINAL_DIGEST

SUITES = harness.SUITES


def easy(grader="current"):
    return select_grader(harness.load_suite(SUITES, "easy"), grader)


def test_phase_one_of_f7_roadmap_keeps_exactly_the_13_phase_one_checks():
    scoped = phase_boundary.phase_scope(easy("f7-roadmap"), 1)
    assert scoped.phase == 1
    assert scoped.expected == easy().expected and len(scoped.expected) == 13


def test_phase_two_adds_its_own_checks_and_keeps_phase_one():
    scoped = phase_boundary.phase_scope(easy("f7-roadmap"), 2)
    modules = {node.split("::")[0].rsplit("/", 1)[-1].split("_")[1] for node in scoped.expected}
    assert modules == {"phase1", "phase2"}


def test_unscoped_digests_are_unchanged():
    assert grader_identity(easy())["assertion_digest"] == EASY_DIGEST
    medium = select_grader(harness.load_suite(SUITES, "medium"), "658bbea5")
    assert grader_identity(medium)["assertion_digest"] == ORIGINAL_DIGEST
    assert "phase" not in grader_identity(easy())


def test_a_phase_scope_names_its_phase_and_hashes_only_what_it_runs():
    two, four = (phase_boundary.phase_scope(easy("f7-roadmap"), n) for n in (2, 4))
    assert grader_identity(two)["phase"] == 2
    assert grader_identity(two)["assertion_digest"] != grader_identity(four)["assertion_digest"]
    assert grader_identity(four)["assertion_digest"] == grader_identity(phase_boundary.phase_scope(easy("f7-roadmap"), 4))["assertion_digest"]


def test_easys_default_still_has_one_prompt():
    assert len(harness.load_suite(SUITES, "easy").prompts) == 1


def test_a_phase_prompt_comes_from_prompts_then_phase_prompts():
    suite = easy("f7-roadmap")
    assert phase_boundary.phase_prompt(suite, 1) == suite.prompts[0]
    for number, title in ((2, "Complaints Board"), (3, "Add Complaint"), (4, "Resolve and Reopen")):
        assert phase_boundary.phase_prompt(suite, number).startswith(f"Implement Phase {number} — {title}.")
    medium = harness.load_suite(SUITES, "medium")
    assert phase_boundary.phase_prompt(medium, 3) == medium.prompts[2]
    with pytest.raises(SystemExit, match="phase 5"):
        phase_boundary.phase_prompt(suite, 5)


def test_phase_mediated_takes_01_from_the_suite_and_later_ones_from_the_bundle():
    suite = phase_boundary.phase_scope(easy("f7-roadmap"), 2)
    files = phase_boundary.phase_mediated(suite, 2)
    assert files == [suite.root / "mediated" / "test_01_home.py",
                     suite.root / "grader-versions" / "f7-roadmap" / "mediated" / "test_02_board.py"]
    assert phase_boundary.phase_mediated(phase_boundary.phase_scope(easy(), 2), 2) == [suite.root / "mediated" / "test_01_home.py"]


def phase_one_build(root: Path) -> Path:
    """Easy's base plus only the home page: what a strict Phase 1 leaves, with no models.py."""
    suite = harness.load_suite(SUITES, "easy")
    shutil.copytree(suite.root / "base", root, dirs_exist_ok=True)
    good = suite.root / "fixtures" / "known-good"
    (root / "templates").mkdir()
    for name in ("base.html", "home.html"):
        shutil.copyfile(good / "templates" / name, root / "templates" / name)
    (root / "app.py").write_text(
        "import uvicorn\nfrom fastapi import FastAPI, Request\nfrom fastapi.templating import Jinja2Templates\n\n"
        "app = FastAPI()\ntemplates = Jinja2Templates(directory=\"templates\")\n\n\n"
        "@app.get(\"/\")\ndef home(request: Request):\n    return templates.TemplateResponse(request, \"home.html\")\n\n\n"
        "if __name__ == \"__main__\":\n    uvicorn.run(\"app:app\", reload=True)\n")
    return root


def test_a_phase_one_only_easy_build_passes_f7_roadmap_at_phase_one_and_fails_at_two(tmp_path):
    build = phase_one_build(tmp_path / "build")
    one = evaluate(build, phase_boundary.phase_scope(easy("f7-roadmap"), 1))
    assert one["checks_ran"] and one["passed"], one["tail"]
    two = evaluate(build, phase_boundary.phase_scope(easy("f7-roadmap"), 2))
    # Phase 2's checks import models.py, which a Phase-1 build does not have: collection fails whole.
    assert not two["passed"] and not two["checks_ran"]
    assert any("phase2" in node for node in two["missing"])
