"""F.7: acceptance qualified on real builds, with original graders retained."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grader_history
import harness
import qualify_matrix
from grading import evaluate

REPO = harness.CODE.parents[1]
MEDIUM = harness.load_suite(harness.SUITES, "medium")
EASY = harness.load_suite(harness.SUITES, "easy")
ORIGINAL = "658bbea5"
ORIGINAL_DIGEST = "bb62e770424152f7ec2cac47158224a6cf1378ebda73536924158b68e3f77788"
WITNESSES = MEDIUM.root / "fixtures" / "witnesses"
PHASE4 = "grader_tests/test_phase4_resolve_reopen.py::"
IDENTITY = PHASE4 + "test_complaint_identity_is_stable_and_keyword_only"
ROUTES = {PHASE4 + name for name in (
    "test_resolve_route_marks_complaint_resolved_and_redirects",
    "test_reopen_route_marks_complaint_open_and_redirects",
    "test_resolve_reopen_does_not_reorder_the_board",
)}


def build(tmp_path: Path, suite, fixture: Path) -> Path:
    shutil.copytree(suite.root / "base", tmp_path, dirs_exist_ok=True)
    shutil.copytree(fixture, tmp_path, dirs_exist_ok=True)
    return tmp_path


def good(tmp_path: Path, suite=MEDIUM) -> Path:
    return build(tmp_path, suite, suite.root / "fixtures" / "known-good")


def witness(tmp_path: Path, name: str) -> Path:
    return build(tmp_path, MEDIUM, WITNESSES / name)


def edit(root: Path, path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    assert old in text, (path, old)
    target.write_text(text.replace(old, new))


def original():
    return grader_history.select_grader(MEDIUM, ORIGINAL)


@pytest.mark.parametrize("prefix", ["grader/", "mediated/", "expected.json", "base/pyproject.toml", "base/uv.lock", "base/tests/"])
def test_medium_original_bundle_matches_git_bytes(prefix):
    root = f"learn/code/suites/medium/{prefix}"
    paths = subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", ORIGINAL, root], text=True).splitlines()
    assert paths
    bundle = MEDIUM.root / "grader-versions" / ORIGINAL
    for path in paths:
        saved = bundle / path.removeprefix("learn/code/suites/medium/")
        assert saved.read_bytes() == subprocess.check_output(["git", "-C", str(REPO), "show", f"{ORIGINAL}:{path}"])


def test_medium_original_bundle_reproduces_recorded_digest():
    identity = grader_history.grader_identity(original())
    assert identity == {"revision": ORIGINAL, "assertion_digest": ORIGINAL_DIGEST, "execution_policy": "trusted-copy-v1"}
    records = sorted((REPO / "evals/2026-11-09-medium-final-screen").glob("*/run.json"))
    assert len(records) == 6
    for record in records:
        assert json.loads(record.read_text())["grader"]["assertion_digest"] == ORIGINAL_DIGEST


@pytest.mark.parametrize("name", ["base-r02", "base-r03"])
def test_witness_builds_replay_their_recorded_misses_on_the_original_bundle(tmp_path, name):
    result = evaluate(witness(tmp_path, name), original())
    assert result["checks_ran"]
    assert set(result["missing"]) == {IDENTITY} | ROUTES


MEDIATED_04 = MEDIUM.root / "mediated" / "test_04_resolve_reopen.py"


def mediated(workspace: Path, file: Path = MEDIATED_04) -> subprocess.CompletedProcess:
    """Run a mediated test the way the unit does: from outside, with the project importable."""
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONPATH=str(workspace))
    return subprocess.run(
        ["uv", "run", "--frozen", "--with", "pytest", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--rootdir", str(workspace), str(file)],
        cwd=workspace, env=env, capture_output=True, text=True, timeout=120)


FORM_CHECK = "grader_tests/test_phase3_add.py::test_complaints_board_renders_add_complaint_form"
OPEN_BADGE = '<span class="badge text-bg-warning">Open</span>'
RESOLVED_BADGE = '<span class="badge text-bg-secondary">Resolved</span>'
TEMPLATE = "templates/complaints.html"


def mark_up(workspace: Path, shape: str) -> Path:
    """Replace both state badges with one shape; {} is the word."""
    edit(workspace, TEMPLATE, OPEN_BADGE, shape.format("Open"))
    edit(workspace, TEMPLATE, RESOLVED_BADGE, shape.format("Resolved"))
    return workspace


VALID_LABELS = {
    "caption": "<p>Status: {}</p>",
    "strong_caption": "<p><strong>Status:</strong> {}</p>",
    "badge_in_caption": '<p>Status: <span class="badge">{}</span></p>',
    "state_caption": "<div>State: {}</div>",
    "emphasised_word_after_text": "<p>Filed under: <strong>{}</strong></p>",
    "comment_inside_the_label": '<span class="badge"><!-- state -->{}</span>',
}
FALSE_LABELS = {
    "negated_caption": "<p>Status: Not {}</p>",
    "negated_strong": "<p>Not <strong>{}</strong></p>",
    "negated_span": "<p>Not <span>{}</span></p>",
    "hidden_label": "<p hidden>Status: {}</p>",
    "both_words": "<p>Status: {}</p><p>Open</p><p>Resolved</p>",
}


@pytest.mark.parametrize("name", VALID_LABELS)
def test_medium_accepts_valid_status_markup(tmp_path, name):
    workspace = mark_up(good(tmp_path), VALID_LABELS[name])
    assert evaluate(workspace, MEDIUM)["missing"] == []
    result = mediated(workspace)
    assert result.returncode == 0, result.stdout + result.stderr


def test_medium_accepts_a_status_beside_its_form_in_one_element(tmp_path):
    workspace = good(tmp_path)
    edit(workspace, TEMPLATE, OPEN_BADGE, "<div>State: Open")
    edit(workspace, TEMPLATE, RESOLVED_BADGE, "<div>State: Resolved")
    edit(workspace, TEMPLATE, "Resolve</button>\n    </form>", "Resolve</button>\n    </form></div>")
    edit(workspace, TEMPLATE, "Reopen</button>\n    </form>", "Reopen</button>\n    </form></div>")
    assert evaluate(workspace, MEDIUM)["missing"] == []
    result = mediated(workspace)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", FALSE_LABELS)
def test_medium_rejects_false_status_markup(tmp_path, name):
    workspace = mark_up(good(tmp_path), FALSE_LABELS[name])
    assert ROUTES <= set(evaluate(workspace, MEDIUM)["missing"])
    assert mediated(workspace).returncode == 1


def test_medium_rejects_a_state_only_in_the_complaint_text(tmp_path):
    workspace = mark_up(good(tmp_path), "<i></i>")
    edit(workspace, TEMPLATE, "{{ complaint.text }}", "{{ complaint.text }} Open")
    assert ROUTES <= set(evaluate(workspace, MEDIUM)["missing"])
    assert mediated(workspace).returncode == 1


def test_medium_rejects_a_label_that_never_changes(tmp_path):
    workspace = good(tmp_path)
    edit(workspace, TEMPLATE, RESOLVED_BADGE, OPEN_BADGE)
    assert ROUTES <= set(evaluate(workspace, MEDIUM)["missing"])
    assert mediated(workspace).returncode == 1


@pytest.mark.parametrize("name", ["base-r02", "base-r03"])
def test_witness_builds_pass_route_checks_on_current(tmp_path, name):
    result = evaluate(witness(tmp_path, name), MEDIUM)
    assert result["checks_ran"]
    assert not ROUTES & set(result["missing"])
    assert IDENTITY in result["missing"]


CROSS_PATH = PHASE4 + "test_complaint_ids_increase_across_direct_and_route_creation"
ROUTE_APPEND = "complaints.append(Complaint(agent_name, text))"


def separate_route_counter(workspace: Path) -> Path:
    """Each path's ids rise, but they do not share one allocator."""
    edit(workspace, "app.py", ROUTE_APPEND,
         "complaint = Complaint(agent_name, text)\n    complaint.id = next(_route_ids)\n    complaints.append(complaint)")
    edit(workspace, "app.py", "app = FastAPI()", "from itertools import count\n_route_ids = count(1_000_000)\n\napp = FastAPI()")
    return workspace


def renumber_on_append(workspace: Path) -> Path:
    edit(workspace, "app.py", ROUTE_APPEND,
         "complaints.append(Complaint(agent_name, text))\n    for index, item in enumerate(complaints, start=1):\n        item.id = index")
    return workspace


def overwrite_with_max(workspace: Path) -> Path:
    edit(workspace, "app.py", ROUTE_APPEND,
         "complaint = Complaint(agent_name, text)\n    complaint.id = max(item.id for item in complaints) + 1\n    complaints.append(complaint)")
    return workspace


ID_MUTANTS = {"separate": separate_route_counter, "renumber": renumber_on_append, "max_overwrite": overwrite_with_max}


def test_separate_route_counter_passes_the_original_identity_check(tmp_path):
    assert evaluate(separate_route_counter(good(tmp_path)), original())["missing"] == []


@pytest.mark.parametrize("name", ID_MUTANTS)
def test_medium_rejects_ids_not_shared_across_paths(tmp_path, name):
    workspace = ID_MUTANTS[name](good(tmp_path))
    assert CROSS_PATH in evaluate(workspace, MEDIUM)["missing"]
    assert mediated(workspace).returncode == 1


def test_medium_accepts_a_post_init_counter(tmp_path):
    workspace = good(tmp_path)
    edit(workspace, "models.py", "id: int = field(default_factory=lambda: next(_ids))", "id: int = None")
    edit(workspace, "models.py", 'status: str = "open"\n',
         'status: str = "open"\n\n    def __post_init__(self):\n        if self.id is None:\n            self.id = next(_ids)\n')
    assert evaluate(workspace, MEDIUM)["missing"] == []
    result = mediated(workspace)
    assert result.returncode == 0, result.stdout + result.stderr


def repair_r02(workspace: Path) -> Path:
    edit(workspace, "models.py", "@dataclass\nclass Complaint:", "next_direct_id = 1\n\n@dataclass\nclass Complaint:")
    edit(workspace, "models.py", "if self.id == 0 and 'next_direct_id' in globals():", "if self.id == 0:")
    edit(workspace, "models.py", "        for i, c in enumerate(self, start=1):\n            c.id = i\n", "")
    edit(workspace, "models.py", "next_direct_id = max((c.id for c in complaints), default=0) + 1\n", "")
    return workspace


def repair_r03(workspace: Path) -> Path:
    edit(workspace, "app.py", "    if complaints:\n        new_complaint.id = max(c.id for c in complaints) + 1\n    else:\n        new_complaint.id = 1\n", "")
    edit(workspace, "models.py", "    complaint.id = i\n", "")
    return workspace


@pytest.mark.parametrize(("name", "repair"), [("base-r02", repair_r02), ("base-r03", repair_r03)])
def test_witness_builds_pass_everything_once_only_the_ids_are_repaired(tmp_path, name, repair):
    workspace = repair(witness(tmp_path, name))
    assert evaluate(workspace, MEDIUM)["missing"] == []
    result = mediated(workspace)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", ["base-r02", "base-r03"])
def test_witness_builds_still_fail_the_identity_invariant_on_current(tmp_path, name):
    workspace = witness(tmp_path, name)
    assert {IDENTITY, CROSS_PATH} <= set(evaluate(workspace, MEDIUM)["missing"])
    assert mediated(workspace).returncode == 1


def test_medium_current_has_nineteen_checks():
    assert len(MEDIUM.expected) == 19 and CROSS_PATH in MEDIUM.expected


ROADMAP_BUNDLE = "f7-roadmap"
EASY_DIGEST = "337644606cd9d203a25b456dfb495fdc50f3ecc516c0096a6904cb78cbe629b5"
EASY_BUNDLE = EASY.root / "grader-versions" / ROADMAP_BUNDLE
EASY_MEDIATED = EASY_BUNDLE / "mediated"


def easy_roadmap():
    return grader_history.select_grader(EASY, ROADMAP_BUNDLE)


def easy_good(tmp_path: Path) -> Path:
    return good(tmp_path, EASY)


def test_easy_current_identity_is_unchanged():
    assert grader_history.grader_identity(EASY)["assertion_digest"] == EASY_DIGEST
    assert len(EASY.expected) == 13


def test_easy_phase1_bytes_are_identical_in_bundle():
    for path in EASY.tests.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            assert (EASY_BUNDLE / "grader" / path.relative_to(EASY.tests)).read_bytes() == path.read_bytes()


def test_easy_bundle_extends_the_thirteen_checks():
    expected = easy_roadmap().expected
    assert expected[:13] == EASY.expected and len(expected) == 30


def test_a_phase_one_request_hands_over_only_phase_one():
    assert [path.name for path in harness.mediated_tests(EASY, 1)] == ["test_01_home.py"]
    assert [path.name for path in harness.mediated_tests(EASY, None)] == ["test_01_home.py"]


def test_easy_bundle_passes_known_good(tmp_path):
    workspace = easy_good(tmp_path)
    result = evaluate(workspace, easy_roadmap())
    assert result["checks_ran"] and result["missing"] == []
    outcome = mediated(workspace, EASY_MEDIATED)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr


def captioned_easy(workspace: Path) -> Path:
    return mark_up(workspace, "<p>Status: {}</p>")


def plain_word_easy(workspace: Path) -> Path:
    return mark_up(workspace, "<p>{}</p>")


def non_utc(workspace: Path) -> Path:
    edit(workspace, "models.py", "datetime.now(timezone.utc)", "datetime.now(timezone(timedelta(hours=2)))")
    edit(workspace, "models.py", "from datetime import datetime, timezone", "from datetime import datetime, timedelta, timezone")
    return workspace


def not_bootstrap_cards(workspace: Path) -> Path:
    edit(workspace, TEMPLATE, 'class="card mb-3"', 'class="panel mb-3"')
    return workspace


def duplicate_cards(workspace: Path) -> Path:
    edit(workspace, TEMPLATE, "{% for complaint in complaints %}", "{% for complaint in complaints + complaints %}")
    return workspace


def hidden_badge(workspace: Path) -> Path:
    return mark_up(workspace, '<span class="badge" style="display: none">{}</span>')


def non_utc_seed(workspace: Path) -> Path:
    edit(workspace, "models.py", 'Complaint("Aria", "My instructions contradict each other every other message."),',
         'Complaint("Aria", "My instructions contradict each other every other message.", datetime(2026, 1, 2, tzinfo=timezone(timedelta(hours=2)))),')
    edit(workspace, "models.py", "from datetime import datetime, timezone", "from datetime import datetime, timedelta, timezone")
    return workspace


def missing_form(workspace: Path) -> Path:
    edit(workspace, "app.py", "status_code=303)\n\n\n@app.post(\"/complaints/{complaint_id}/resolve\")", "status_code=302)\n\n\n@app.post(\"/complaints/{complaint_id}/resolve\")")
    return workspace


EASY_MUTANTS = {
    "captioned_state": captioned_easy,
    "plain_word_not_a_badge": plain_word_easy,
    "non_utc_timestamp": non_utc,
    "not_bootstrap_cards": not_bootstrap_cards,
    "complaint_shown_twice": duplicate_cards,
    "state_badge_hidden": hidden_badge,
    "non_utc_seed": non_utc_seed,
    "add_redirects_302": missing_form,
    "separate_route_counter": separate_route_counter,
    "renumber_on_append": renumber_on_append,
    "route_overwrites_with_max": overwrite_with_max,
}


@pytest.mark.parametrize("name", EASY_MUTANTS)
def test_easy_bundle_rejects_on_hidden_and_mediated(tmp_path, name):
    workspace = EASY_MUTANTS[name](easy_good(tmp_path))
    result = evaluate(workspace, easy_roadmap())
    assert result["checks_ran"] and result["missing"], name
    assert mediated(workspace, EASY_MEDIATED).returncode == 1


def test_easy_bundle_accepts_a_post_init_counter(tmp_path):
    workspace = easy_good(tmp_path)
    edit(workspace, "models.py", "id: int = field(default_factory=lambda: next(_ids))", "id: int = None")
    edit(workspace, "models.py", 'status: str = "open"\n',
         'status: str = "open"\n\n    def __post_init__(self):\n        if self.id is None:\n            self.id = next(_ids)\n')
    assert evaluate(workspace, easy_roadmap())["missing"] == []
    outcome = mediated(workspace, EASY_MEDIATED)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr


MAP_STATUSES = {"covered", "mediated-only", "hidden-only", "gap"}
MAPS = {"medium": (MEDIUM, lambda: MEDIUM, [MEDIUM.root / "mediated"]),
        "easy": (EASY, easy_roadmap, [EASY.root / "mediated", EASY_MEDIATED])}


def requirement_map(name: str) -> list[dict]:
    return json.loads((MAPS[name][0].root / "acceptance-map.json").read_text())


def phase_bullets(suite) -> list[str]:
    bullets, phase, lines = [], False, (suite.root / "base/specs/roadmap.md").read_text().splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        phase = bool(re.match(r"## Phase \d", line)) if line.startswith("## ") else phase
        if phase and line.startswith("- "):
            parts = [line[2:]]
            while index + 1 < len(lines) and lines[index + 1].startswith("  "):
                index += 1
                parts.append(lines[index].strip())
            bullets.append(" ".join(parts))
        index += 1
    return bullets


@pytest.mark.parametrize("name", MAPS)
def test_every_roadmap_phase_bullet_is_mapped(name):
    mapped = [entry["requirement"] for entry in requirement_map(name)]
    assert sorted(set(phase_bullets(MAPS[name][0])) - set(mapped)) == []


@pytest.mark.parametrize("name", MAPS)
def test_named_checks_exist(name):
    _, selected, roots = MAPS[name]
    hidden = set(selected().expected)
    mediated_names = {node.name for root in roots for path in root.glob("test_*.py")
                      for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef)}
    for entry in requirement_map(name):
        assert set(entry["hidden"]) <= hidden, entry["id"]
        assert set(entry["mediated"]) <= mediated_names, entry["id"]


@pytest.mark.parametrize("name", MAPS)
def test_map_statuses_match_their_checks(name):
    ids = [entry["id"] for entry in requirement_map(name)]
    assert len(ids) == len(set(ids))
    for entry in requirement_map(name):
        assert entry["status"] in MAP_STATUSES, entry["id"]
        expected = ("covered" if entry["hidden"] and entry["mediated"] else "mediated-only" if entry["mediated"]
                    else "hidden-only" if entry["hidden"] else "gap")
        assert entry["status"] == expected, entry["id"]
        if entry["status"] == "gap":
            assert entry.get("reason"), entry["id"]


@pytest.mark.parametrize("name", MAPS)
def test_no_written_requirement_is_left_to_the_hidden_grader_alone(name):
    assert [entry["id"] for entry in requirement_map(name) if entry["status"] == "hidden-only"] == []


EVIDENCE = REPO / "docs/superpowers/research/2026-11-09-f7-qualify-acceptance"


def matrix() -> dict:
    return json.loads((EVIDENCE / "matrix.json").read_text())


def test_matrix_sources_match_manifest():
    manifest = json.loads((EVIDENCE / "sources/manifest.json").read_text())
    assert manifest["commit"] == "67f0138fa42386cf057ba34c5117349817b40258"
    assert manifest["files"]
    for path, digest in manifest["files"].items():
        assert hashlib.sha256((EVIDENCE / "sources" / path).read_bytes()).hexdigest() == digest


def test_matrix_valid_builds_pass_and_defects_fail_on_ours():
    for suite, witnesses in matrix().items():
        ours = ["current", "mediated"]
        for name, row in witnesses.items():
            for checker in ours:
                expected = "pass" if row["kind"] == "valid" else "reject"
                assert row[checker] == expected, (suite, name, checker)


def test_matrix_mediated_rejects_whatever_current_rejects():
    for suite, witnesses in matrix().items():
        for name, row in witnesses.items():
            if row["current"] == "reject":
                assert row["mediated"] == "reject", (suite, name)


def test_matrix_replays_andre_test_medium_on_a_witness(tmp_path):
    workspace = witness(tmp_path, "base-r02")
    assert mediated(workspace, EVIDENCE / "sources/test_medium.py").returncode == 1


@pytest.mark.parametrize(("suite_name", "witness_name"), [
    ("medium", "redirect_home"), ("medium", "redirect_board"), ("medium", "hidden_nav"), ("medium", "date_tokens"),
    ("medium", "disabled_input"), ("medium", "disabled_buttons"), ("easy", "redirect_home"), ("easy", "hidden_nav"),
])
def test_mediated_rejects_the_defects_the_oracle_rejects(tmp_path, suite_name, witness_name):
    suite = harness.load_suite(harness.SUITES, suite_name)
    defects = qualify_matrix.MEDIUM_DEFECT if suite_name == "medium" else qualify_matrix.EASY_DEFECT
    workspace = qualify_matrix.build(suite_name, defects[witness_name], tmp_path)
    assert qualify_matrix.pytest_rejects(workspace, suite.root / "mediated", qualify_matrix.NOT_SERVER)


def test_easy_phase_one_mediated_original_is_retained():
    path = "learn/code/suites/easy/mediated/test_01_home.py"
    retained = EASY_BUNDLE / "mediated-658bbea5/test_01_home.py"
    assert retained.read_bytes() == subprocess.check_output(["git", "-C", str(REPO), "show", f"{ORIGINAL}:{path}"])


def test_matrix_sources_exclude_bytecode():
    assert not [path for path in json.loads((EVIDENCE / "sources/manifest.json").read_text())["files"] if "__pycache__" in path]


def test_medium_accepts_a_comment_inside_a_card(tmp_path):
    workspace = good(tmp_path)
    edit(workspace, TEMPLATE, '<div class="card-body">', '<div class="card-body">\n<!-- one complaint -->')
    assert evaluate(workspace, MEDIUM)["missing"] == []
    result = mediated(workspace)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", ["fieldset_disabled", "hidden_name_input"])
def test_medium_mediated_rejects_unusable_add_forms(tmp_path, name):
    workspace = good(tmp_path)
    if name == "fieldset_disabled":
        edit(workspace, TEMPLATE, '<form method="post" action="/complaints" class="mt-4">', '<form method="post" action="/complaints" class="mt-4"><fieldset disabled>')
        edit(workspace, TEMPLATE, "Submit</button>\n</form>", "Submit</button>\n</fieldset></form>")
    else:
        edit(workspace, TEMPLATE, 'name="agent_name" required', 'name="agent_name" hidden required')
    assert FORM_CHECK in evaluate(workspace, MEDIUM)["missing"]
    assert mediated(workspace, MEDIUM.root / "mediated" / "test_03_add.py").returncode == 1


def test_easy_bundle_accepts_a_board_template_of_any_name(tmp_path):
    workspace = easy_good(tmp_path)
    (workspace / "templates/complaints.html").rename(workspace / "templates/board.html")
    edit(workspace, "app.py", '"complaints.html"', '"board.html"')
    assert evaluate(workspace, easy_roadmap())["missing"] == []
    outcome = mediated(workspace, EASY_MEDIATED)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr


def test_easy_bundle_accepts_the_add_form_in_its_own_card(tmp_path):
    workspace = easy_good(tmp_path)
    edit(workspace, TEMPLATE, '<form method="post" action="/complaints" class="mt-4">', '<div class="card mt-4"><div class="card-body"><form method="post" action="/complaints">')
    edit(workspace, TEMPLATE, "Submit</button>\n</form>", "Submit</button>\n</form></div></div>")
    assert evaluate(workspace, easy_roadmap())["missing"] == []
    outcome = mediated(workspace, EASY_MEDIATED)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr


def test_easy_bundle_accepts_a_badge_beside_the_state_badge(tmp_path):
    workspace = easy_good(tmp_path)
    edit(workspace, TEMPLATE, OPEN_BADGE, '<span class="badge">#{{ complaint.id }}</span>' + OPEN_BADGE)
    edit(workspace, TEMPLATE, RESOLVED_BADGE, '<span class="badge">#{{ complaint.id }}</span>' + RESOLVED_BADGE)
    assert evaluate(workspace, easy_roadmap())["missing"] == []
    outcome = mediated(workspace, EASY_MEDIATED)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr


@pytest.mark.parametrize(("suite_name", "name", "checker"), [
    ("medium", "newest_first", "current"), ("medium", "textual_date", "mediated"),
    ("medium", "separate_route_counter", "current"), ("medium", "negated_caption", "mediated"),
    ("easy", "no_title", "mediated"),
])
def test_committed_matrix_rows_still_replay(tmp_path, suite_name, name, checker):
    row = matrix()[suite_name][name]
    groups = {"medium": (qualify_matrix.MEDIUM_VALID, qualify_matrix.MEDIUM_DEFECT), "easy": (qualify_matrix.EASY_VALID, qualify_matrix.EASY_DEFECT)}[suite_name]
    edits = groups[0][name] if row["kind"] == "valid" else groups[1][name]
    assert qualify_matrix.checkers(suite_name)[checker](qualify_matrix.build(suite_name, edits, tmp_path)) == row[checker]
