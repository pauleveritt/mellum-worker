---
phase: LC
feature_cycle: LC.19A
cycle: 1
lifecycle: closed
---

# LC.19A — the suite-shaped instrument LC.19 owes

## Why

Lesson 10, "One spec file per phase", was measured on ladder rungs 6–9: a
four-phase build whose last phase's automatic id was missed in five of six runs
when the roadmap was one joined file, against one of six when it was one file
per phase. LC.24 retired the ladder as the lessons' instrument, and the hard
suite — the shape that would carry the arm — is 0/9 for every arm, so it has no
headroom to separate anything.

Two things are missing and both are small once the record is the target:

- **A reading finer than passes.** `medium/expected.json` already names 18
  checks grouped by grader module, four of them `test_phase4_resolve_reopen.py`,
  and `score_workspace_details` computes which expected ids did not pass before
  reducing them to a count. On medium at n=3 the passes floor, but the failed
  checks do not: LC.24 measured bare at 18/18/18 against worker at 2/12/2.
- **An arm that can bite.** `medium/prompts/04.md` restates every phase-4
  requirement, so the spec layout cannot change any outcome. The arm needs thin
  prompts that point at the spec, which is what rung 9 had.

No run is made in this cycle.

## Decisions taken before this plan

- **The reading is per grader module, not per "phase".** The record field is
  `check_groups`, keyed by the expected test's module file, because the hard
  suite also grades `test_migrations.py` and `test_visits.py`, which are not
  phases. The lesson can read the phase-4 group from it.
- **`failed_checks` keeps its meaning** (a count) so every existing table in
  `learn/lessons/` and `docs/superpowers/research/` stays readable. The names
  arrive beside it, not in place of it.
- **The arm is a variant of medium, not a fourth suite.** A fourth suite would
  duplicate five grader files and ten fixtures and would contradict the Getting
  Started page's three suites, for an arm one lesson uses. `easy`, `medium` and
  `hard` keep their default prompts, graders, fixtures and `expected.json`.
- **Both arms send thin prompts.** The only difference between them is which
  file the pointer names. If one arm kept today's detailed prompts, the
  comparison would measure prompt verbosity and the spec layout at once.
- **Default behaviour is byte-identical to today.** Without `--specs`, no
  overlay is applied and `run.json` records `"specs": null`.
- **Deletion is explicit.** The split variant states `specs/roadmap.md` in its
  `delete.json` rather than having the harness infer that a variant which ships
  phase files must drop the joined roadmap.

## Design

### The record

`score_workspace_details` returns the missing expected ids instead of only their
count; `score_workspace` and `qualify` ignore the list as before.
`_run_sessions` writes, beside `failed_checks`:

```json
"missing_checks": ["grader_tests/test_phase4_resolve_reopen.py::test_complaint_identity_is_stable_and_keyword_only"],
"check_groups": {"test_phase1_home.py": {"missing": 0, "total": 4},
                 "test_phase4_resolve_reopen.py": {"missing": 5, "total": 5}}
```

`check_groups` carries every expected test's module, including those with
nothing missing, so a table can say "phase 1 clean, phase 4 absent" without
knowing what was expected.

### The variant

A suite may ship `spec-variants/<name>/`. When `--specs <name>` is passed:

1. `base/` is copied as usual; `start/` and the layout baseline follow it.
2. Every file in the variant except `prompts/` and `delete.json` is copied over
   the workspace, so `AGENTS.md` and `specs/` are replaced by the variant's.
3. Each path in `delete.json` is removed from the workspace.
4. The run's prompts are the variant's `prompts/*.md`, in sorted order; with
   `--single-prompt` they are joined exactly as today.
5. `pristine` is hashed after the overlay, so a variant's own files are never
   reported as writes outside the layout.
6. `run.json` records `"specs": "<name>"`.

An unknown name is a `SystemExit` naming the variants available, like the
existing unknown-suite message.

### The medium data

```
learn/code/suites/medium/spec-variants/
  joined/prompts/01.md … 04.md      # "the stories for Phase N are in specs/roadmap.md"
  split/AGENTS.md                   # pointer: one file per phase in specs/
  split/delete.json                 # ["specs/roadmap.md"]
  split/prompts/01.md … 04.md       # same text, pointing at specs/phase-N.md
  split/specs/phase-1.md … phase-4.md
```

The four phase files are `base/specs/roadmap.md` split at its phase headings,
story text unchanged; the joined arm keeps that file as shipped. The two prompt
sets differ in one sentence each, the one that names the file.

### The stale instrument sentences

LC.24 flipped four sentences that called `ladder/` the measured instrument and
missed three more: `learn/getting-started/harness.md:81-82` ("the ladder is the
measuring instrument"), `learn/getting-started/suite.md:156-158` ("Rates come
from the ladder … which is why findings lessons cite `evals/`") and
`suite.md:165`. They contradict the badge rule `learn/about/evidence.md` now
carries, and the suite page tells a learner that lessons cite a path lesson
pages may not link. The correction lands here, with a dated note in LC.24's
spec rather than an edit to its archived plan.

## Non-goals

- Any run, preregistration, rate or badge. LC.19 owns the two-arm run and page.
- A new suite directory, or a change to `easy`/`medium`/`hard` defaults.
- Editing `ladder/` or `evals/`.
- The three lessons LC.20–LC.23, which may reuse `check_groups` later.

## Tasks

### Task 1: The stale instrument sentences

**Files:**
- Modify: `learn/getting-started/harness.md`, `learn/getting-started/suite.md`,
  `docs/superpowers/specs/2026-10-25-lc24-lesson1-exemplar-design.md`,
  `CHANGELOG.md`
- Test: `tests/learn-site.test.mjs`

**Interfaces:**
- Consumes: LC.24's badge rule in `learn/about/evidence.md`.
- Produces: pages that name the suites as the measured instrument everywhere.

- [ ] **Step 1: Write the failing assertions** in the existing
  `"the harness is the measured instrument"` test:

```js
assert.doesNotMatch(page("getting-started/harness.md"), /ladder is the measuring/);
assert.doesNotMatch(page("getting-started/suite.md"), /Rates come from the ladder/);
assert.doesNotMatch(page("getting-started/suite.md"), /The ladder is the measuring instrument/);
```

- [ ] **Step 2: Run and see it fail.** `node --test tests/learn-site.test.mjs`.

- [ ] **Step 3: Rewrite the three sentences.**

`harness.md:81-82` → ``Two or three sessions are still a lead, not a rate;
lesson 4 explains why, and a rate needs a preregistered run with its arms and n
fixed first.``

`suite.md:156-158` → ``Rates come from a preregistered run on these suites,
with the arms and n fixed before it starts, which is why findings lessons cite a
record in `docs/superpowers/research/` and not one session.``

`suite.md:165` → ``A single session shows you where to look; a preregistered
reference run on llama.cpp, recorded in `docs/superpowers/research/`, is what
findings lessons cite.``

- [ ] **Step 4: Dated note in LC.24's spec**, under the existing correction:
  ``**Dated correction 2026-10-25 (second).** Three further sentences in
  `learn/getting-started/harness.md` and `suite.md` still named the ladder the
  measuring instrument, and the suite page said lessons cite `evals/`.
  Corrected in LC.19A.``

- [ ] **Step 5: Changelog**, under `[Unreleased]` → `### Fixed`: one entry saying
  two Getting Started pages still named the ladder the measuring instrument and
  now name the suites.

- [ ] **Step 6: Run and see it pass, then commit.**

```bash
git add learn tests docs CHANGELOG.md && git commit -m "docs(learn): name the suites, not the ladder, as the measured instrument"
```

### Task 2: `missing_checks` and `check_groups`

**Files:**
- Modify: `learn/code/harness.py`
- Test: `learn/code/tests/test_harness.py`

**Interfaces:**
- Consumes: `suite.expected`, the expected ids already loaded from
  `expected.json`.
- Produces: the record fields Task 3 and LC.19 read.

- [ ] **Step 1: Write the failing tests.** Extend
  `test_score_details_counts_expected_failures` to assert the returned list, add
  a two-module grouping case, and extend `test_run_sessions_writes_metrics`:

```python
assert missing == ["grader_tests/test_add.py::test_add"]
assert harness.check_groups(suite.expected, missing) == {
    "test_add.py": {"missing": 1, "total": 1}}
assert record["missing_checks"] == []
assert record["check_groups"] == {"test_add.py": {"missing": 0, "total": 1}}
```

- [ ] **Step 2: Run and see them fail.**
  `uv run python -m pytest learn/code/tests -q`.

- [ ] **Step 3: Return the names.** `score_workspace_details` returns
  `(passed, tail, missing)` where `missing` is the sorted list of expected ids
  absent from the grader output; the "missing expected tests: …" tail line keeps
  its text. `score_workspace` and `qualify` drop the third value.

- [ ] **Step 4: Add the helper and the fields.**

```python
def check_groups(expected, missing):
    groups = {}
    for test in expected:
        module = test.split("::")[0].rsplit("/", 1)[-1]
        groups.setdefault(module, {"missing": 0, "total": 0})["total"] += 1
    for test in missing:
        module = test.split("::")[0].rsplit("/", 1)[-1]
        groups[module]["missing"] += 1
    return groups
```

`_run_sessions` keeps `"failed_checks": len(missing)` and adds
`"missing_checks"` and `"check_groups"`.

- [ ] **Step 5: Run and see them pass, then commit.**
  `git commit learn/code -m "feat(harness): record which checks failed, grouped by module"`

### Task 3: `--specs joined|split`

**Files:**
- Modify: `learn/code/harness.py`
- Test: `learn/code/tests/test_harness.py`

**Interfaces:**
- Consumes: a suite's `spec-variants/<name>/`, written in Task 4.
- Produces: `run.json`'s `specs` field and the two prompt sets LC.19 runs.

- [ ] **Step 1: Write the failing tests** against a synthetic suite: no variant
  leaves `specs/roadmap.md` and records `specs: None`; `specs="joined"` takes
  its prompts from the variant and leaves the roadmap; `specs="split"` applies
  the overlay, deletes the roadmap and takes the variant's prompts; an unknown
  name raises `SystemExit` naming what exists.

- [ ] **Step 2: Run and see them fail.**

- [ ] **Step 3: Implement** `load_variant` and the five overlay steps in the
  design above; thread `specs` through `run_suite`, `_run_sessions`,
  `run_suites` and the `run` subcommand's `--specs` argument, and add `"specs"`
  to the record.

- [ ] **Step 4: Run and see them pass, then commit.**
  `git commit learn/code -m "feat(harness): --specs swaps the project's spec layout"`

### Task 4: The medium variant data

**Files:**
- Add: `learn/code/suites/medium/spec-variants/joined/prompts/01-04.md`,
  `split/{AGENTS.md,delete.json,prompts/01-04.md,specs/phase-1-4.md}`
- Test: `learn/code/tests/test_harness.py`

**Interfaces:**
- Consumes: `learn/code/suites/medium/base/specs/roadmap.md`, split at its four
  phase headings with the story text unchanged.
- Produces: the two arms LC.19 preregisters.

- [ ] **Step 1: Split the roadmap** into `phase-1.md` … `phase-4.md`, each
  keeping its heading and stories.
- [ ] **Step 2: Write the split `AGENTS.md`**: the medium `AGENTS.md` with the
  pointer sentence changed to "The phased requirements are in `specs/`, one file
  per phase."
- [ ] **Step 3: Write both prompt sets.** Same text in both, thin: name the
  phase, say the stories are in the spec file, say the earlier phases must keep
  working. They differ only in the file the pointer names —
  `specs/roadmap.md` against `specs/phase-N.md`.
- [ ] **Step 4: Add a test** that both variants load, that split leaves no
  `specs/roadmap.md`, and that the two prompt sets are identical except for the
  pointer sentence — so a later edit cannot quietly make the arms differ in
  something else.
- [ ] **Step 5: Commit.**
  `git commit learn/code -m "feat(harness): medium can ship its phases as one roadmap or one file each"`

### Task 5: Docs

**Files:**
- Modify: `learn/getting-started/suite.md`, `learn/getting-started/harness.md`,
  `learn/glossary.md`, `CHANGELOG.md`
- Test: `tests/learn-site.test.mjs`

- [ ] **Step 1: Write the failing assertion** that `suite.md` names the phase
  modules among the graded checks and that `harness.md` documents `--specs`.
- [ ] **Step 2: Document the record.** In suite.md's grading steps, add that the
  run record names the expected tests that did not pass and groups them by
  grader module, so a session failing four of six says which module.
- [ ] **Step 3: Document the flag** in `harness.md` beside `--repeat`:
  `--specs joined|split` uses the suite's variant prompts and spec layout, and
  the record carries `specs`.
- [ ] **Step 4: Extend the glossary's `### failed checks` entry** with the
  per-module grouping, and add `### spec variant` if the page's first use needs
  a definition.
- [ ] **Step 5: Changelog**, `### Added`: the two record fields and the flag.
- [ ] **Step 6: `node --test tests/learn-site.test.mjs`, then commit.**
  `git commit learn tests CHANGELOG.md -m "docs(learn): the phase breakdown and the spec variant"`

### Task 6: Prove both ways

- [ ] **Step 1: Qualify** `uv run python learn/code/harness.py qualify --suite
  medium` — unchanged by this cycle; record the output.
- [ ] **Step 2: Load each variant** through the tests, and confirm an unknown
  name fails with a message that lists `joined` and `split`.
- [ ] **Step 3: Run the whole suite.** `uv run python -m pytest learn/code/tests
  -q` and `npm test`. Record both totals.

### Task 7: Close

**Files:**
- Modify: `ROADMAP.md`, this plan
- Move: this plan to `docs/superpowers/plans/archive/`

- [ ] **Step 1: LC.19A's Status cell** — `complete 2026-10-25 —
  [plan](docs/superpowers/plans/archive/2026-10-25-lc19a-suite-instrument.md).`
  then what shipped, the two totals and the qualification line.
- [ ] **Step 2: LC.19's Status cell** — the instrument now exists; the run and
  page are next, with the arm named.
- [ ] **Step 3: `## Now`** — Active becomes LC.19; Next keeps LC.18 and LC.7A.
- [ ] **Step 4: `## Result`** here, then `lifecycle: closed` and `git mv` to
  `archive/`.
- [ ] **Step 5: Verify and commit.** `node --test tests/docs-caps.test.mjs`,
  `npm test`, `git log --oneline 23cd721..HEAD`, then
  `git commit -m "docs(lc19a): close the cycle"`.

## Risks

- **A variant that drifts from the base.** `spec-variants/split/AGENTS.md` and
  the four phase files restate project facts that live in `base/`. The
  prompt-parity test covers the prompts; the spec text is checked only by
  qualification, which does not read it. A later edit to the base roadmap owes
  the same edit to the split files.
- **A reading without an arm.** `check_groups` is useful on its own but proves
  nothing about spec layout until LC.19's run exists; this cycle must not be
  read as evidence for the lesson.
- **A flag nobody uses.** `--specs` is exercised by unit tests and by LC.19; if
  LC.19 is dropped, the variant data and the overlay are dead weight the repo
  carries. The reopen condition is LC.19's row.

## Result

2026-10-25. Shipped: `run.json` carries `missing_checks` and `check_groups`;
`--specs joined|split` applies a suite's `spec-variants/`, records `specs`, and
ships the flag alongside `--repeat` on the harness page; `medium` carries both
variants — one joined `specs/roadmap.md` with thin briefs, or four phase files
with their own `AGENTS.md` pointer and an explicit `delete.json`; the glossary
defines the per-module grouping under **failed checks** and adds **spec
variant**; and the three
Getting Started sentences that still called the ladder the measuring instrument
are corrected.

Read on the real suite rather than assumed: `known-good` misses 0 checks in all
four modules, `known-broken` misses 1 of 3 in `test_phase3_add.py` and 2 of 5 in
`test_phase4_resolve_reopen.py`. `medium: QUALIFIED`, `learn/code/tests` 57/57,
`npm test` 368/368, `docs-caps` 4/4, `uv run zensical build` clean.

Owed: LC.19's preregistration and its two-arm run (the arm is the instruction
between the joined and split variants at n = 3), then the page.
