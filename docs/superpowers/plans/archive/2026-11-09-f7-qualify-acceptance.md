---
phase: F
feature_cycle: F.7
cycle: 7
lifecycle: closed
---

# F.7 — Qualified phase acceptance

## For Andre

**[Design](../../specs/2026-11-09-f7-qualify-acceptance-design.md); executed natively.** **What changes:** Medium's grader stops rejecting valid `Status: Open` markup and gains a
cross-path ID check; the original stays selectable as bundle `658bbea5`. Easy gains a selectable
four-phase bundle. Every written Easy/Medium requirement is mapped, by test, to a check or a
reasoned gap. **What to look at:** the matrix in the [research note](../../research/2026-11-09-f7-qualify-acceptance.md),
including how your `test_medium.py` and `67f0138f` graders fare on the same builds.

## Global constraints

- No model or GPU run; no change to prompts, remedies, presets, budgets or harness run paths.
- Recorded scores stand. Medium original digest `bb62e770…`; Easy `current` digest `33764460…`, 13 checks.
- Medium `current` ends at 19 checks. Mediated tests are written from the roadmap, not the grader.
- No suite-specific predicate may name r02/r03 markup or values. Hard is unchanged.
- Every new test is seen failing before its code. Commit explicit paths, atomically; no push.

## Review focus (each has a test in its owning task)

- `Status: Open` with the word only in nested markup: `<p><strong>Status:</strong> Open</p>` passes.
- A `<div>` holding the caption and the action form together passes; text beside it is not read as the label.
- `Status: Not Open` and a card carrying both words fail, on hidden and mediated.
- A valid allocator that is not `itertools.count` (`__post_init__` with a module counter) passes.
- A complaint built directly but never stored must still advance allocation for the route.

## Task 1: Retain the original Medium grader and witness builds

**Files:** `learn/code/grader_history.py` (add `'658bbea5': '658bbea5'` to `BUNDLES`; `f7-roadmap`
follows in Task 4); create `suites/medium/grader-versions/658bbea5/{grader/,base/,mediated/,expected.json,revision.json}`
from `git show 658bbea5`; create `suites/medium/fixtures/witnesses/{base-r02,base-r03}/{app.py,models.py,templates/}`
and `PROVENANCE.json` (run directory, sha256 of each file). Test: new `learn/code/tests/test_phase_acceptance.py`.
Update the `--grader` help text in `harness.py`.

1. Failing tests: `test_medium_original_bundle_matches_git_bytes` (including `mediated/`),
   `test_medium_original_bundle_reproduces_recorded_digest` (`grader_identity(...)['assertion_digest']`
   equals `bb62e770424152f7ec2cac47158224a6cf1378ebda73536924158b68e3f77788` and every
   `evals/2026-11-09-medium-final-screen/*/run.json`),
   `test_witness_builds_replay_their_recorded_misses_on_the_original_bundle` (r02 and r03 each
   miss exactly the four named checks; project tests pass).
2. Run; expect `unknown grader` and missing fixture failures.
3. Copy bytes with `git show`; copy builds from `~/mellum-runs/f6/medium-final-screen/`.
4. Run; expect pass. Commit, with a `CHANGELOG` line for the new `--grader` value.

## Task 2: Correct the Medium status label

**Files:** `suites/medium/grader/test_phase4_resolve_reopen.py`, `suites/medium/mediated/test_04_resolve_reopen.py`, the test file.

**Interface:** `_state_label(node) -> str | None` in the grader: visible text excluding descendant
forms and controls; returns `Open`/`Resolved` for the exact word or for that word after a
case-insensitive `Status`/`State` caption and colon, else `None`. The mediated test gets its own
roadmap-derived label reading.

1. Failing tests, using known-good with `complaints.html` edits: accepted `<p>Status: Open</p>`,
   `<p><strong>Status:</strong> Open</p>`, `<div>State: Open <form>…</form></div>`, the badge form;
   rejected `Status: Not Open`, both words, a `hidden` label, state only in the complaint text.
   Also `test_witness_builds_miss_only_identity_on_current` (r02/r03 pass all three route/order
   checks). Each case runs against hidden `current` and the mediated file.
2. Run; expect positives to fail on hidden and the negation cases to fail on mediated.
3. Implement; keep the existing outer-label skip and `labels == {status.capitalize()}`.
4. Run with `test_oracle_review.py` and `test_shared_suite_contracts.py`. Commit with `CHANGELOG`.

## Task 3: Cover shared ID allocation

**Files:** `suites/medium/grader/test_phase4_resolve_reopen.py` (add
`test_complaint_ids_increase_across_direct_and_route_creation`), `suites/medium/expected.json` (19),
`suites/medium/mediated/test_04_resolve_reopen.py` (add `test_direct_and_posted_complaints_share_one_rising_id_sequence`).

1. Failing tests: mutants on known-good, each rejected by hidden and mediated — separate route
   counter starting at 1,000,000 (must first be shown **passing** the `658bbea5` bundle), renumber
   on append, route overwrite with `max(stored)+1`; plus an ID-repaired r02 and r03 that pass all
   19. Positives: module counter in `__post_init__`; a direct complaint never stored.
2. Run; expect the mutants to survive. Sequence for both checks: direct, route, direct, route;
   integer ids; strictly increasing; earlier ids (and seeds) unchanged.
3. Implement; retain `test_complaint_identity_is_stable_and_keyword_only` unchanged.
4. Run; `harness qualify --suite medium` and `--grader 658bbea5` both print QUALIFIED. Commit with `CHANGELOG`.

## Task 4: Easy four-phase bundle

**Files:** `suites/easy/grader-versions/f7-roadmap/{grader/,base/,mediated/,expected.json,revision.json}`;
add `'f7-roadmap'` to `BUNDLES`. The bundle's grader holds Easy's 13 Phase-1 checks byte-identical,
plus `test_phase2_board.py`, `test_phase3_add.py`, `test_phase4_resolve_reopen.py`, authored from
Easy's roadmap. Mediated `test_02…04` live here only, so a Phase-1 request hands over what it does today.

1. Failing tests: bundle selects and known-good passes all; `test_easy_current_identity_is_unchanged`
   (digest `337644606cd9d203a25b456dfb495fdc50f3ecc516c0096a6904cb78cbe629b5`, 13 checks);
   `test_easy_phase1_bytes_are_identical_in_bundle`; Easy-specific rejections on hidden and
   mediated: `Status: Open` (roadmap: "badge reading exactly"), a non-UTC timestamp, a board
   without Bootstrap `.card`; Medium's Task 2–3 ID and label negatives ported.
2. Run; expect `unknown grader`.
3. Author the checks; share only `_contract` helpers. Implement.
4. `harness qualify --suite easy --grader f7-roadmap` prints QUALIFIED, and bare `--suite easy` still does. Commit with `CHANGELOG`.

## Task 5: Requirement map, enforced

**Files:** `suites/medium/acceptance-map.json`, `suites/easy/acceptance-map.json`, test file.

**Shape:** a list of `{id, phase, source, requirement, hidden: [...], mediated: [...], status, reason?}`,
status in `covered | mediated-only | hidden-only | gap`.

1. Failing tests: `test_every_roadmap_phase_bullet_is_mapped` (parse phase-section `- ` bullets from
   `base/specs/roadmap.md`, joined lines), `test_named_checks_exist` (hidden ids in the resolved
   bundle's `expected`, mediated names found by `ast` in the bundle or `mediated/`),
   `test_a_gap_states_its_reason`.
2. Run; expect missing-file failures. Write both maps, with tech-stack and layout entries.
3. Any `hidden-only` entry for a written requirement means a mediated gap: repair test first (Task 6).
4. Run; commit.

## Task 6: Qualification matrix and Andre comparison

**Files:** `docs/superpowers/research/2026-11-09-f7-qualify-acceptance/sources/` (pinned copies of
`test_medium.py` and his `67f0138f` Easy and Medium `grader/`, with `manifest.json` sha256),
`learn/code/qualify_matrix.py`, generated `matrix.json` beside them, test file.

**Interface:** `uv run python learn/code/qualify_matrix.py [--write]` runs every witness through
each checker and prints the table; without `--write` it exits non-zero if the result differs from
the committed `matrix.json`. Medium columns: `658bbea5`, `current`, mediated, Andre `test_medium`,
Andre grader. Easy Phase 1 witnesses: `redirect`, `no_nav`, `no_title`, `no_viewport`, `missing_home_template`.

1. Failing test: `test_matrix_matches_committed_result` and `test_matrix_sources_match_manifest`.
2. Implement, generate, and read the result. Any mutant `current` rejects and mediated accepts is
   a superset gap: repair mediated, test first. Any written requirement Andre catches and ours
   misses is added to mediated and mapped.
3. Run; commit.

## Ladder run

None; deterministic replay decides ([spec](../../specs/2026-11-09-f7-qualify-acceptance-design.md#ladder-run)).

## Persuasion → enforcement

No Pi hook applies to offline grading. `grader_history` digests, retention and map tests, and the
matrix check make drift fail `npm test`; no prompt text is added.

## Close

Research note and evidence; ROADMAP F.7 status and `## Now`; BACKLOG entry for Hard's shared label
predicate (reopen: before R.3); glossary (requirement map) and any new pathology; `## Result`, then
archive this plan. Run `node --test tests/docs-caps.test.mjs`, `npm test`, ladder pytest and the
docs build; reconcile `[Unreleased]`. Then a fresh whole-branch review. The [squash into `integration`](../../../sdd.md#branches-and-worktrees)
waits for Paul: F.7 starts from `codex/phase-worker-roadmap`, which `integration` does not yet contain.
Worktree and branch removal follow that merge, using the owning tool from a retained checkout.

## Result

2026-11-09. Shipped: Medium's status correction and cross-path ID check (19 hidden checks), the
`658bbea5` bundle reproducing digest `bb62e770…`, Easy's `f7-roadmap` bundle (30 checks), enforced
requirement maps, and a qualification matrix ([note](../../research/2026-11-09-f7-qualify-acceptance.md)).
Deterministic only: no model or GPU ran, no remedy, preset or F.8 work, no recorded score changed.
Deviations: mediated gaps the matrix and a fresh review surfaced were repaired in this cycle, as the
design allowed; Easy's Phase-1 mediated original is retained in its bundle; `test_matrix_matches_committed_result`
became a live replay of a sample of rows, since a full recomputation takes about 15 minutes. Squashed into `integration`
on 2026-11-09, after the roadmap commit it builds on; tree equality verified.
