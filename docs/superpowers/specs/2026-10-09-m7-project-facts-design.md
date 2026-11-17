# M.7 design: project facts — Mellum succeeds on looser specs

Date: 2026-10-09. Depends on M.6 (`ladder/` in this repo) being merged.
Decided with Paul in brainstorming, 2026-10-09:

- A looser version of ac-demo's four AgentClinic phase specs serves both
  as course material (in ac-demo) and as a measured ladder fixture (here).
- Looser means: coding hints dropped, structure thinned to what tests and
  later phases need, project rules moved out of each phase into one
  project-level place, testable behaviour kept.
- The mechanism is a project facts block that Mode forwards (approach A),
  with test-command detection as the fallback (approach B). The mediated
  brief stays deferred (it becomes M.10) and is later compared on this
  fixture. A write-only guard goes to the backlog.

## Evidence that motivates it

Phase 1 of ac-demo, headless Mode on M.5, scratch clones, 2026-10-09
(one to two runs per level; an indication, not a ladder phase):

| Brief | Passes the spec's test | Requests | Wall |
| --- | --- | --- | --- |
| full task line (files, test command) | 1/1 | 27 | 54 s |
| `Implement specs/phase-1-home.md` | 2/2 (one wrote a forbidden `pytest.ini`) | 28, 37 | 75, 115 s |
| a developer sentence | 1/2 (one false success) | 47, 53 | 147, 195 s |

Every looser run started with the prompt's default `uv run --offline pytest
-q`, which cannot import the root `app.py`, and spent 7 to 25 commands
bending the project to that command (`tests/__init__.py`, `pytest.ini`,
relative imports, `pip install .`). The spec file named the right command,
but prompt v5's rule honours only a command in the task text. Content was
right even from a loose sentence, apart from what the sentence omitted.
The probe's record lines are kept with the M.7 research note (§6).

## 1. The project facts block

### Where and what

A `## Mellum` section in the project's `AGENTS.md` (working directory of
the session). Mode recognises Markdown bullets in that section and nothing
else; any label is forwarded, three are documented:

```markdown
## Mellum

- Test command: uv run python -m pytest tests
- Write only: app.py, models.py, templates/, tests/
- Do not: install packages or add dependencies; weaken tests
```

The section ends at the next heading of level 1 or 2. Over 600 characters
of bullets: Mode warns (UI, or stderr without one) and forwards nothing
from the section; the fallback then applies.

### What Mode does

- Read once per span, at activation, from `AGENTS.md` in `process.cwd()`.
- `filterForMellum` appends `\n\nProject facts:\n<bullets>` to every user
  message after the on-marker in the outgoing payload (string content, or
  the last text part of array content). The session's stored messages are
  unchanged; the same text is appended on every request, so the prefix
  cache is unaffected.
- The prompt is unchanged (v5); its existing rule "A command named in the
  task is the command" now sees the test command.
- `MELLUM_MODE_FACTS=0` turns off both the block and the fallback.

### Fallback (B)

When there is no section, or it has no `Test command:` bullet, and
`pyproject.toml` in the working directory mentions `pytest`: Mode appends
`Project facts:\n- Test command: uv run --offline python -m pytest -q`
(merged after any section bullets). Otherwise nothing is added; Node
projects keep the prompt's `node --test` rule.

### Recorded

- Run record (schema 2, new optional field): `facts: { source:
  "agents-md" | "detected" | "agents-md+detected" | "none" | "off",
  testCommand: string | null, chars: number }`.
- Handoff summary line gains `facts: <source>`.

### Tests (`tests/mellum-mode*.test.mjs`)

Each shown failing first. A pure `readProjectFacts(dir, { exists, read })`
returns `{ source, bullets, testCommand, chars }`: section found; section
with no test command plus pytest pyproject (merged); no section plus
pytest pyproject; no section, Node project; section over cap (warning,
fallback); section ended by a level-2 heading; `MELLUM_MODE_FACTS=0`.
`filterForMellum` with facts: appended to each post-marker user message
(string and array forms), not to tool results or pre-marker messages, and
not twice. Record and handoff carry the source.

## 2. The fixture: rungs 6–9

`ladder/fixtures/agentclinic-p1` … `agentclinic-p4`, one per phase. Each
holds `pyproject.toml` and `uv.lock` from ac-demo (FastAPI, pinned), an
`AGENTS.md` containing only the `## Mellum` section above, the looser
`specs/phase-N-*.md` for that rung and earlier ones, and a reference
solution for all earlier phases (rung 7 starts with phase 1 done). A
`README.md` in `ladder/fixtures/agentclinic/` records the authoring rules
and a fact count per phase, original against looser.

### Authoring the looser specs

From each original phase spec: drop every coding hint (imports,
`field(default_factory=…)`, `Form`, `RedirectResponse`, "insert alongside
the existing route"); keep a file or symbol name only where a hidden test
imports it or a later phase depends on it (`app.py`'s `app`, `models.py`'s
`Complaint` and `complaints`, `templates/base.html`); drop the per-phase
rules paragraph (it is in `AGENTS.md`); keep every testable behaviour in
plain words. Target: about 25% fewer facts per phase, counted and recorded.

### Scoring (`ladder/ladder/rungs.py`)

A rung passes only when all hold:

1. The facts block's test command passes in the workspace.
2. Hidden behaviour tests pass. They live in
   `ladder/fixtures/agentclinic-hidden/phase-N/`, are copied into the
   workspace after the run, and assert the original spec's kind-4 facts:
   phase 1 tagline and 200 at `/`; phase 2 200 at `/complaints` with
   `Scope creep never ends.`; phase 3 303 with `Location: /complaints` and
   the new complaint listed; phase 4 resolve and reopen with 303, the
   badge text, order unchanged, `Complaint(agent_name, text)` still
   constructs and ids are unique.
3. No existing test is removed or edited; additions are allowed. Every
   `tests/**/*.py` file present at the start still exists and parses, and each
   pytest-collected test in it (module-level `test*` functions, `test*`
   methods of `Test*` classes) is still there under the same qualified name
   with a byte-identical source segment. New tests, in old or new files,
   are allowed; non-`.py` files such as `tests/.gitkeep` do not count. The
   Mellum-visible tests must still pass (rule 1).
   Note: changed 2026-10-09 by Paul after A18 r1 showed the strict rule failing an appended test.
4. No path outside the write-only list was created or modified (from the
   workspace's git status). Scored and reported as its own column,
   `outside_write_list`, so the backlog guard can be measured against it.

The sentence for every rung: `Implement specs/phase-N-<name>.md`.

### Runner switches

- `--mode-facts off` sets `MELLUM_MODE_FACTS=0` in the child env.
- `--strip-facts-section` removes the `## Mellum` section from the
  workspace's `AGENTS.md` before the run (the fallback-only condition).
- `run.json` records both.

## 3. Measured phases and the ship rule

Mode, same launch as A17 (`ladder/`, this checkout), 3 repeats per rung:

| Phase | Condition | Rungs | Runs |
| --- | --- | --- | --- |
| A18 | `--mode-facts off` (Mode as shipped) | 6–9 | 12 |
| A19 | facts on | 1–9 | 27 |
| A20 | facts on, `--strip-facts-section` (fallback only) | 6–9 | 12 |

Ships when all hold: A19 rungs 1–5 ≥ 13/15 (A17 14/15, within one); A19
rungs 6–9 beat A18 by ≥ 3/12 or reach ≥ 10/12; A19's median requests on
rungs 6–9 are below A18's. A20 informs the docs (what a project without the
section gets) and does not gate. If the rule fails, the facts code is not
merged; the fixture and A18 stay as the baseline for M.10. Each phase gets
a `evals/<phase>/README.md` and a row in `ablation-summary.md`; raw
files go to a `research-YYYY-MM-DD` release (Paul's step).

## 4. ac-demo

- Nothing in this phase edits ac-demo's `AGENTS.md`. If any step must,
  it restores the file and checks `git -C <ac-demo> diff --quiet
  AGENTS.md` before the step ends.
- Probe and check runs use scratch clones of ac-demo, never the checkout.
- At the end, the four looser specs are copied into ac-demo as new,
  uncommitted files under `specs/loose/`; the `## Mellum` section is
  printed in the final report for Paul to paste. No ac-demo commits.

## 5. Docs, backlog, roadmap (only the ship-gated parts wait on A19)

- README "Use it": the facts block in one paragraph with the example;
  without it, Python projects get `python -m pytest`. Ship-gated.
- `skills/mellum-setup`: an optional step that offers to add the section
  to the current project, asking for the test command, and asks before
  writing. Ship-gated.
- `docs/recipe.md` §4b: the block, the fallback, `MELLUM_MODE_FACTS`.
- `CHANGELOG.md` `[Unreleased]` entries as work lands (AGENTS.md rule).
- Backlog: add "Write-only guard" (reopens when a facts-on phase shows
  `outside_write_list` violations); at close remove "Mode and the
  project's AGENTS.md" and "Mode-side test-command preflight"; narrow
  "Prompt default `python -m pytest`" to Worker.
- Roadmap: this phase is M.7; Worker one-liners, in-process Worker and
  mediated brief become M.8–M.10; M.10 compares on this fixture.

## 6. Order

1. Fixture rungs 6–9: looser specs, hidden tests, reference solutions,
   `rungs.py` scoring; a reference-solution self-check (each rung's hidden
   tests pass on the next rung's starting state).
2. Runner switches; A18 (baseline; useful even if later steps slip).
3. `readProjectFacts`, filter, record, handoff (TDD).
4. A19, A20; research note `docs/superpowers/research/2026-10-09-m7-project-facts.md`
   with the probe evidence and the three phases.
5. Ship-gated docs if A19 passes; backlog and roadmap either way.
6. Copy looser specs into ac-demo `specs/loose/` (uncommitted).

## 7. Excluded

Any prompt or template change; Worker (pi-subagents) behaviour; the
write-only guard; the mediated brief; reading anything from `AGENTS.md`
beyond the `## Mellum` section; commits in ac-demo; publishing releases.

## Risks

- The hidden tests encode the original spec's wording (badge text, seed
  text); a looser spec that still states them keeps the comparison fair,
  and the authoring rule keeps every testable behaviour.
- Rungs 6–9 run FastAPI under `uv --offline`; the uv cache on this machine
  must hold the locked packages. The fixture self-check runs offline first.
- Appending facts to every post-marker user message in `/mellum on` spans
  repeats them per task; that is intended (each task stands alone).
- Three repeats per rung is thin for a 3-of-12 margin; the rule is a
  floor, and the note reports per-rung results.

## Appendix A: the looser specs and the facts block (verbatim)

Fixture `AGENTS.md` (every rung):

```markdown
# AgentClinic

## Mellum

- Test command: uv run python -m pytest tests
- Write only: app.py, models.py, templates/, tests/
- Do not: install packages or add dependencies; remove or rewrite routes that already work; weaken tests
```

`specs/phase-1-home.md`:

```markdown
# Phase 1 — Home Page

- `app.py` holds the FastAPI application as `app`.
- A shared Jinja2 layout, `templates/base.html`: HTML5 with `lang="en"`, a responsive viewport, Bootstrap 5 from a CDN (CSS in the head, the JS bundle at the end of the body), the favicon `https://www.python.org/static/favicon.ico`, the title "AgentClinic" unless a page sets its own, and a navbar with the "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`).
- The home page at `/` uses that layout: a hero section with the tagline *"Come in. Sit down. Tell us about your human."* and a short welcoming paragraph.
- `python app.py` starts the app with uvicorn, with reload.
- A smoke test: `GET /` returns 200 and contains the tagline.
```

`specs/phase-2-board.md`:

```markdown
# Phase 2 — Complaints Board

- A complaint, `Complaint` in `models.py`, has an agent name, its text, and a UTC creation timestamp set automatically for each new complaint.
- `models.py` keeps complaints in a module-level list, `complaints`, seeded with three to five typical AI-agent gripes, one of them exactly `Scope creep never ends.`
- `GET /complaints` shows a "Complaints Board" in the shared layout: one Bootstrap card per complaint with the agent name, the date (year, month and day) and the text.
- The home page keeps working.
- A test: `GET /complaints` returns 200 and contains `Scope creep never ends.`
```

`specs/phase-3-add.md`:

```markdown
# Phase 3 — Add Complaint

- The Complaints Board ends with a form for a new complaint (agent name and text) that posts to `/complaints`.
- `POST /complaints` adds the complaint and redirects to the board with status 303 and `Location: /complaints`.
- Existing pages keep working.
- Tests: the POST, without following redirects, returns 303 with that `Location`; afterwards the board lists the new complaint.
```

`specs/phase-4-resolve-reopen.md`:

```markdown
# Phase 4 — Resolve and Reopen

- Each complaint gets a unique, stable integer `id`, assigned automatically and never reused; `Complaint(agent_name, text)` still works.
- Each complaint has a status, `"open"` unless changed.
- `POST /complaints/{id}/resolve` marks a complaint resolved and `POST /complaints/{id}/reopen` marks it open again; both redirect to the board with 303.
- The board shows a badge reading exactly "Open" or "Resolved", and a Resolve button for an open complaint or a Reopen button for a resolved one.
- Resolving or reopening never changes the order of the board.
- Tests: resolve and reopen change the status and redirect with 303, and the order is unchanged.
```

What was dropped from the originals: the per-phase rules paragraph (now the
facts block), every import and library call (`starlette.testclient`,
`dataclasses.field(default_factory=…)`, `Form`, `RedirectResponse`), the
template and test file names other than `templates/base.html`, "create the
`templates/` directory", `{% block content %}`, and "insert alongside the
existing route" (now a facts bullet).

## Appendix B: hidden tests (what each rung scores)

Copied into the workspace root as `_hidden_p<k>.py` for every phase k up
to the rung's phase, after the run, and run with `uv run --offline python -m
pytest _hidden_p*.py -q`. Each file builds its own
`TestClient(app)` (`from starlette.testclient import TestClient`, `from app
import app`).

Scoring rule 3 for these rungs: no existing test is removed or edited,
additions allowed. Note: changed 2026-10-09 by Paul after A18 r1 showed the strict rule failing an appended test.

- `_hidden_p1.py`: `GET /` is 200 and contains `Come in. Sit down. Tell us
  about your human.`
- `_hidden_p2.py`: `GET /complaints` is 200 and contains `Scope creep never
  ends.`; `GET /` is still 200.
- `_hidden_p3.py`: `POST /complaints` with `agent_name="hidden"`,
  `text="hidden-check-123"`, `follow_redirects=False` is 303 with
  `location == "/complaints"`; then `GET /complaints` contains
  `hidden-check-123`.
- `_hidden_p4.py`: `import models`; `models.Complaint("a", "b")` and
  `models.Complaint("a", "c")` construct, have `status == "open"` and
  different `id`s; for the first seeded complaint, `POST
  /complaints/{id}/resolve` (no redirects) is 303, its `status` becomes
  `"resolved"` and `GET /complaints` contains `Resolved`; `POST
  /complaints/{id}/reopen` is 303 and `status` is `"open"` again; the list
  of ids in `models.complaints` is the same before and after.
