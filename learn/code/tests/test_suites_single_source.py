"""The suites describe each phase once (2026-11-06 audit, docs/superpowers/research/2026-11-06-suite-spec-audit.md).

`specs/roadmap.md` is the authority: every phase carries an Acceptance list. A prompt only says
which phase (or migration) to implement and points at the spec; it restates no requirement and
names no module, import or mechanism. The prompts and specs as first shipped stay runnable as the
`original` spec variant, so every record made before the change can be reproduced.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402

SUITES = ("easy", "medium", "hard")
ORIGINAL_PROMPTS = {"easy": 1, "medium": 4, "hard": 11}


def _suite(name):
    return harness.load_suite(harness.SUITES, name)


def _phases(roadmap: str) -> dict[str, str]:
    blocks, current = {}, None
    for line in roadmap.splitlines():
        if line.startswith("## "):
            current = line[3:] if line.startswith("## Phase") else None
            if current:
                blocks[current] = ""
        elif current is not None:
            blocks[current] += line + "\n"
    return blocks


@pytest.mark.parametrize("name", SUITES)
def test_every_roadmap_phase_carries_an_acceptance_list(name):
    roadmap = (_suite(name).root / "base/specs/roadmap.md").read_text()
    phases = _phases(roadmap)
    assert phases, f"{name}: no phases"
    for title, body in phases.items():
        assert "**Acceptance.**" in body, f"{name} {title} has no Acceptance list"


@pytest.mark.parametrize("name", SUITES)
def test_the_roadmap_says_how_to_check_and_rules_out_a_server(name):
    text = " ".join((_suite(name).root / "base/specs/roadmap.md").read_text().split())
    assert "uv run --frozen python -m pytest tests" in text
    assert "never by starting a server" in text


@pytest.mark.parametrize("name", SUITES)
def test_prompts_only_name_the_work_and_point_at_the_spec(name):
    for prompt in _suite(name).prompts:
        lines = [line for line in prompt.splitlines() if line.strip()]
        assert re.match(r"^Implement (Phase \d+ — .+|the migration `\w+`)\.$", lines[0]), lines[0]
        assert "specs/roadmap.md" in prompt
        assert len(lines) <= 4, f"{name}: a prompt restates the spec:\n{prompt}"
        for cue in ("RedirectResponse", "default_factory", "import ", "Migrations("):
            assert cue not in prompt, f"{name}: prompt names {cue!r}"


def test_hard_has_a_prompt_for_every_phase_and_migration_in_its_roadmap():
    suite = _suite("hard")
    roadmap = (suite.root / "base/specs/roadmap.md").read_text()
    named = [re.match(r"^Implement (.+)\.$", p.splitlines()[0]).group(1) for p in suite.prompts]
    phases = [f"Phase {t.split(' — ')[0].split()[-1]} — {t.split(' — ')[1]}" for t in _phases(roadmap)]
    migrations = re.findall(r"^### Migration `(\w+)`", roadmap, flags=re.M)
    assert len(migrations) == 4
    assert sorted(named) == sorted(phases + [f"the migration `{m}`" for m in migrations])


@pytest.mark.parametrize("name", SUITES)
def test_the_original_prompts_and_specs_stay_runnable(name):
    variant = harness.load_variant(_suite(name), "original")
    assert len(sorted((variant / "prompts").glob("*.md"))) == ORIGINAL_PROMPTS[name]
    assert (variant / "specs" / "roadmap.md").is_file()


@pytest.mark.parametrize("name", SUITES)
def test_every_suite_ships_the_tests_its_roadmap_tells_the_model_to_run(name):
    # The roadmap says to check with `pytest tests`; with no tests/ that command errors (exit 4).
    medium = (_suite("medium").root / "base/tests/test_home.py").read_text()
    starter = _suite(name).root / "base/tests/test_home.py"
    assert starter.is_file() and starter.read_text() == medium


@pytest.mark.parametrize("name", ("easy", "hard"))
def test_original_removes_the_starter_test_it_did_not_ship(name):
    assert json.loads((harness.load_variant(_suite(name), "original") / "delete.json").read_text()) == [
        "tests/test_home.py"]


@pytest.mark.parametrize("name", SUITES)
def test_the_layout_allows_every_module_the_roadmap_names(name):
    allow = json.loads((_suite(name).root / "layout.json").read_text())["allow"]
    roadmap = (_suite(name).root / "base/specs/roadmap.md").read_text()
    stack = (_suite(name).root / "base/specs/tech-stack.md").read_text()
    for module in sorted(set(re.findall(r"`(\w+\.py)`", roadmap + stack))):
        if module in ("app.py", "models.py", "migrations.py"):
            assert module in allow, f"{name}: layout.json does not allow {module}"


def test_hard_layout_allows_the_migrations_module():
    assert "migrations.py" in json.loads((_suite("hard").root / "layout.json").read_text())["allow"]


def test_hard_phase5_grader_has_no_dead_assertion():
    text = (_suite("hard").root / "grader/test_phase5.py").read_text()
    assert "if False) or True" not in text


def test_medium_phase2_grader_checks_behaviour_not_the_default_mechanism():
    text = (_suite("medium").root / "grader/test_phase2_board.py").read_text()
    assert "default_factory" not in text


@pytest.mark.parametrize("name", SUITES)
def test_the_suite_still_qualifies(name):
    ok, results = harness.qualify(_suite(name))
    assert results == {"known-good": True, "known-broken": False}, results
    assert ok


def test_the_cli_accepts_the_original_variant():
    args = harness.build_parser().parse_args(["run", "--suite", "easy", "--specs", "original"])
    assert args.specs == "original"


def test_the_cli_still_refuses_a_variant_the_suite_does_not_ship(tmp_path):
    with pytest.raises(SystemExit):
        harness.load_variant(_suite("easy"), "no-such-variant")


def test_hard_grader_passes_the_known_good_build_in_any_module_order(tmp_path):
    # Phase 5 used to archive a seeded complaint that Phase 2 expects on the board, so Hard's
    # grade held only because pytest runs the modules alphabetically (2026-11-06 review).
    suite = _suite("hard")
    shutil.copytree(suite.root / "base", tmp_path, dirs_exist_ok=True)
    shutil.copytree(suite.root / "fixtures" / "known-good", tmp_path, dirs_exist_ok=True)
    shutil.copytree(suite.tests, tmp_path / "grader_tests")
    order = ["test_phase5.py", "test_phase2_board.py", "test_phase4_resolve_reopen.py", "test_phase1_home.py"]
    result = subprocess.run(
        ["uv", "run", "--with", "pytest", "pytest", "-q", "-p", "no:cacheprovider",
         *[f"grader_tests/{name}" for name in order]],
        cwd=tmp_path, env=harness.grade_env(tmp_path), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:]


@pytest.mark.parametrize("name", SUITES)
def test_each_prompt_names_a_heading_its_roadmap_has(name):
    suite = _suite(name)
    roadmap = (suite.root / "base/specs/roadmap.md").read_text()
    headings = {line[3:] for line in roadmap.splitlines() if line.startswith("## Phase")}
    migrations = {f"the migration `{m}`" for m in re.findall(r"^### Migration `(\w+)`", roadmap, flags=re.M)}
    for prompt in suite.prompts:
        work = re.match(r"^Implement (.+)\.$", prompt.splitlines()[0]).group(1)
        assert work in headings | migrations, f"{name}: {work!r} names no roadmap heading"


@pytest.mark.parametrize("name", SUITES)
def test_the_roadmap_quotes_no_grader_literal(name):
    roadmap = (_suite(name).root / "base/specs/roadmap.md").read_text()
    for literal in ('"First complaint"', '"Second complaint"', "2099", "37.5"):
        assert literal not in roadmap, f"{name}: roadmap quotes the grader's {literal}"


def test_easy_phase1_acceptance_states_every_phase1_requirement():
    # The 2026-11-07 screen: every session missed the title override and the startup, which sat
    # outside Easy's Acceptance list. The Acceptance list now states all of Phase 1 as behaviour.
    roadmap = (_suite("easy").root / "base/specs/roadmap.md").read_text()
    body = _phases(roadmap)["Phase 1 — Home Page"]
    acceptance = " ".join(body.split("**Acceptance.**", 1)[1].split())
    for item in ("viewport", "Bootstrap 5", "bundle", "https://www.python.org/static/favicon.ico",
                 "own title", "hero", "welcom", "uv run --frozen python app.py", "reload",
                 'if __name__ == "__main__"'):
        assert item in acceptance, f"Easy Phase 1 Acceptance does not state {item!r}"
