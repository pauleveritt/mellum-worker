"""The suites describe each phase once (2026-11-06 audit, docs/superpowers/research/2026-11-06-suite-spec-audit.md).

`specs/roadmap.md` is the authority: every phase carries an Acceptance list. A prompt only says
which phase (or migration) to implement and points at the spec; it restates no requirement and
names no module, import or mechanism. The prompts and specs as first shipped stay runnable as the
`original` spec variant, so every record made before the change can be reproduced.
"""

import json
import os
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
    shutil.copytree(suite.root / "base", tmp_path, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".venv", "__pycache__"))
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


@pytest.mark.parametrize('variant', ['joined', 'split'])
def test_active_medium_variants_use_only_phase_and_spec_pointers(variant):
    root = harness.load_variant(_suite('medium'), variant)
    for number, path in enumerate(sorted((root / 'prompts').glob('*.md')), 1):
        prompt = path.read_text()
        lines = [line for line in prompt.splitlines() if line.strip()]
        pointer = f'specs/phase-{number}.md' if variant == 'split' else 'specs/roadmap.md'
        assert len(lines) <= 4, prompt
        assert pointer in prompt
        assert re.match(r'^Implement Phase \d+ — .+\.$', lines[0])
        assert 'uv run' not in prompt


@pytest.mark.parametrize('name', SUITES)
def test_layout_explicitly_accepts_optional_python_helpers(name, tmp_path):
    suite = _suite(name)
    (tmp_path / 'helpers').mkdir()
    (tmp_path / 'helpers/rendering.py').write_text('def render():\n    return \"ready\"\n')
    report = harness.layout_report(tmp_path, {}, suite.layout)
    assert report['created'] == ['helpers/rendering.py']
    assert report['out_of_layout'] == []


@pytest.mark.parametrize('name', SUITES)
def test_expected_ids_describe_every_declared_hidden_check(name):
    import ast
    suite = _suite(name)
    declared = {f'grader_tests/{path.name}::{node.name}'
                for path in suite.tests.glob('test_*.py')
                for node in ast.parse(path.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}
    assert set(suite.expected) == declared


# Easy's mediated tests (R.1): written from the roadmap, a superset of the hidden grader, and able
# to fail the known miss. Each hidden check names the mediated test that covers it.
EASY_COVERAGE = {
    "test_home_still_returns_200_and_tagline": "test_home_answers_200_with_the_tagline_word_for_word",
    "test_home_has_html5_doctype": "test_home_starts_with_the_html5_doctype",
    "test_home_html_element_declares_english_language": "test_home_html_element_declares_english",
    "test_home_still_has_navigation_links": "test_home_navbar_shows_the_brand_and_links_home_and_complaints",
    "test_home_renders_home_template_extending_shared_base": "test_home_is_rendered_from_home_html_which_extends_base_html",
    "test_layout_has_responsive_viewport": "test_layout_head_has_viewport_bootstrap_css_and_favicon",
    "test_layout_has_bootstrap5_cdn_stylesheet_in_head": "test_layout_head_has_viewport_bootstrap_css_and_favicon",
    "test_layout_has_python_favicon": "test_layout_head_has_viewport_bootstrap_css_and_favicon",
    "test_layout_ends_body_with_bootstrap5_cdn_bundle": "test_layout_body_ends_with_the_bootstrap5_js_bundle",
    "test_layout_title_defaults_to_agentclinic": "test_a_page_title_is_agentclinic_by_default",
    "test_extending_page_can_override_layout_title": "test_a_page_that_extends_the_layout_can_set_its_own_title",
    "test_home_has_hero_and_welcoming_paragraph": "test_home_has_a_hero_holding_the_tagline_and_a_welcoming_paragraph",
    "test_main_guard_launches_uvicorn_with_reload_and_keeps_serving": "test_running_app_py_starts_uvicorn_with_reload_and_serves_home",
}


def _test_names(path: Path) -> set[str]:
    return set(re.findall(r"^def (test_\w+)", path.read_text(), re.M))


def test_every_hidden_easy_check_names_the_mediated_test_that_covers_it():
    root = _suite("easy").root
    hidden = set().union(*(_test_names(p) for p in (root / "grader").glob("test_phase1_*.py")))
    mediated = _test_names(root / "mediated" / "test_01_home.py")
    assert set(EASY_COVERAGE) == hidden
    assert set(EASY_COVERAGE.values()) <= mediated


def _easy_mediated(tmp_path, fixture: str, edit=None):
    """Run Easy's mediated tests from outside a base + fixture workspace, as the unit does."""
    root = _suite("easy").root
    workspace = tmp_path / fixture
    shutil.copytree(root / "base", workspace)
    shutil.copytree(root / "fixtures" / fixture, workspace, dirs_exist_ok=True)
    if edit:
        edit(workspace)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"} | {"PYTHONPATH": str(workspace)}
    return subprocess.run(["uv", "run", "--offline", "python", "-m", "pytest", str(root / "mediated"), "-q",
                           "-p", "no:cacheprovider"], cwd=workspace, env=env, capture_output=True, text=True)


def test_the_easy_mediated_tests_pass_the_complete_build(tmp_path):
    result = _easy_mediated(tmp_path, "known-good")
    assert result.returncode == 0, result.stdout[-2000:]


def test_the_easy_mediated_tests_fail_the_broken_build(tmp_path):
    assert _easy_mediated(tmp_path, "known-broken").returncode == 1


def test_the_easy_mediated_tests_fail_a_layout_whose_title_cannot_be_overridden(tmp_path):
    def fixed_title(workspace):
        base = workspace / "templates" / "base.html"
        base.write_text(re.sub(r"<title>.*?</title>", "<title>AgentClinic</title>", base.read_text(), flags=re.S))

    result = _easy_mediated(tmp_path, "known-good", fixed_title)
    assert result.returncode == 1
    assert "test_a_page_that_extends_the_layout_can_set_its_own_title" in result.stdout


def test_the_easy_launch_check_shows_why_app_py_exited_at_once(tmp_path):
    """A start that dies at once (a port already held, say) reports its own output, not an empty log."""
    def dies_at_once(workspace):
        app = workspace / "app.py"
        app.write_text(app.read_text().replace(
            'if __name__ == "__main__":',
            'if __name__ == "__main__":\n    import sys\n    sys.exit("ERROR: [Errno 48] Address already in use")\n',
            1))

    result = _easy_mediated(tmp_path, "known-good", dies_at_once)
    assert result.returncode == 1
    assert "Address already in use" in result.stdout, result.stdout[-2000:]
