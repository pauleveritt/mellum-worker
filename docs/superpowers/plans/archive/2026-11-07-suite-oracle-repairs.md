---
phase: F
feature_cycle: F.4
cycle: 1
lifecycle: closed
---
# F.4 — Suite oracle repairs implementation plan

## For Andre

Implement the approved [design](../../specs/2026-11-07-suite-oracle-repairs-design.md).
Goal: grades follow the written contracts and cannot be changed through workspace
pytest configuration. Preserve old briefs and assertion bundles; no model-rate claim.
Use standard-library Python, the existing uv locks, pytest and real fixture builds.
Execute test-first; independent grader repairs may run in parallel after snapshots.

## Global constraints

- Work in `codex/suite-oracle-fixes`, cut from `integration`; preserve the main checkout.
- Keep worker/remedies/settings unchanged; no suite values in generic harness code.
- Keep tuple-returning score APIs compatible; new record fields are additive.
- Every new regression must fail against the old behavior before its repair.
- Original prompts/specs and retained grader bundles are immutable.
- Keep specs at 100 lines and plans/research at 150; archive no existing plan edits.

## Review focus

- Generic suites without base metadata still grade; collection errors stay distinguishable.
- Legitimate project conftests work while hidden grading ignores workspace hooks/config.
- Alternate valid page titles, board order and timestamp mechanisms remain accepted.
- Database mutations and migrations cannot pollute another check or the submitted workspace.
- Historical assertions and unknown old records cannot masquerade as current grading.

## Task 1: Preserve and identify assertion bundles

Files: `learn/code/grader_history.py`, `harness.py`, suite `grader-versions/`,
`tests/test_grader_history.py`; original-byte manifest under the audit evidence.
Interfaces: `select_grader(suite, name)` returns a replaced Suite;
`grader_identity(suite) -> dict` records revision, assertion digest and runner policy.
- [x] RED: historical timestamp post-init build scores differently with old/current
  assertions; unknown bundle rejected; original materialized bytes match saved hashes.
- [x] Run `uv run --with pytest python -m pytest -v tests/test_grader_history.py`:
  expected assertion failures before implementation, then all pass after it.
- [x] Retain `bc5db20` and `16cf9f9^` assertions/expected/dependency inputs; add explicit
  `--grader` to run/qualify, default current, and record its identity in new runs.
- [x] Commit this independently, with its Unreleased entry; recheck the changelog.

## Task 2: Trusted runner and truthful component outcomes

Files: `learn/code/grading.py`, `grading_worker.py`, `harness.py`,
`tests/test_grading.py`, affected harness integration tests.
Interfaces: `evaluate(workspace, suite) -> dict` supplies hidden tuple components,
project-test outcome and required-test integrity; public score tuple remains unchanged.
- [x] RED: known-broken + no-op conftest stays failed; workspace pytest config,
  forged PASSED stdout and edited metadata cannot control hidden results.
- [x] RED: added failing project test fails overall; legitimate project conftest
  succeeds; deleted/edited required tests fail; layout reports deleted paths.
- [x] Run `uv run --with pytest python -m pytest -v tests/test_grading.py`:
  expected targeted failures, then all pass.
- [x] Grade disposable copies with trusted suite dependencies/config and sanitized
  environment; external hidden tests, structured reports, independently reset checks.
  Preserve application cwd, generic suites and collection-error semantics.
- [x] Record separate hidden/project/quality components and identity; no automatic
  historical rescore or new layout pass gate. Commit and reconcile Unreleased.

## Task 3: Shared page, model and transition contracts

Files: all suites' Phase 1 graders/contracts; Medium/Hard Phase 2–4 graders;
`tests/test_shared_suite_contracts.py`; expected IDs only if checks are added.
Consumes: trusted runner resets checks independently; direct grader tests still work.
- [x] RED: redirect/HTML4/comment-brand, disconnected controls, false state words,
  global mutation, dropped old complaints, twice-reversed board and bad ID mutants fail.
- [x] RED: newest-first display and per-instance post-init timestamps must pass.
- [x] Run `uv run --with pytest python -m pytest -v tests/test_shared_suite_contracts.py`:
  each new defect regression fails before its repair, then the whole file passes.
- [x] Assert direct HTTP/DOM semantics, exact seed/date, usable associated controls,
  target-only mutation, retained records, integer/global identity and per-action order.
  Do not prescribe an initial board order or implementation mechanism.
- [x] Commit owned files independently; parent maintains the shared changelog.

## Task 4: Complete Easy Phase 1 acceptance

Files: Easy additional hidden checks, `expected.json`, `tests/test_easy_contracts.py`.
Do not edit Phase 1 shared files owned by Task 3 or historical bundles.
- [x] RED: missing inheritance/assets/title override/hero/welcome/launcher and broken
  own-test cases fail; alternative valid markup/title mechanisms remain accepted.
- [x] Run `uv run --with pytest python -m pytest -v tests/test_easy_contracts.py`:
  expected targeted failures, then all pass with positive fixture controls.
- [x] Add independent checks of existing Acceptance only, including a bounded launcher
  probe with process cleanup and isolated port; do not hardcode a hero CSS class.
- [x] Commit owned files; parent reconciles Unreleased and checks original bytes.

## Task 5: Hard archive, database and migration contracts

Files: Hard Phase 5/6/Visits/migration graders, Hard roadmap/tech-stack,
`tests/test_hard_contracts.py`; expected IDs if extended.
- [x] RED: malformed/missing audit, archive side effects/location/repeat, empty/non-view,
  wrong index, nonnullable note, rerun data changes and constant reports fail.
- [x] RED: omitted visits options, strict response types, boundaries and private row
  variations distinguish incorrect implementations; required SQL contracts are checked.
- [x] Run `uv run --with pytest python -m pytest -v tests/test_hard_contracts.py`:
  each regression fails before its fix; all real known-good controls then pass.
- [x] Apply migrations to pristine data through the real command; compare schema/data,
  complete view membership and permitted backfill. Clarify contradictory source wording
  without changing historical variants. Commit owned files; parent maintains changelog.

## Task 6: Reconcile variants, evidence and whole-branch review

Files: active Medium joined/split prompts, suite layout policies, single-source tests,
learning glossary/pathologies/harness guide, changelog, roadmap and this plan.
- [x] RED: active variants obey thin-pointer policy; original bytes remain unchanged;
  every expected check exists; complete fixtures pass current and historical assertions.
- [x] Run relevant tests, then all `learn/code/tests` through `uv run --with pytest`,
  ladder `uv run python -m pytest`, `npm test`, caps and `uv run zensical build`.
  Expected: all pass; report any pre-existing skips without inventing model results.
- [x] Independent whole-branch review against the spec; fix substantiated findings
  with failing regressions. Record exact check counts and corrected mutation outcomes.
- [x] Reconcile Unreleased, add introduced glossary/failure shapes, close roadmap state,
  append Result and archive this plan. Commit the verified cycle close.

## Ladder run

No model/ladder measurement: deterministic builds prove oracle repairs, not a rate.
Run ladder unit tests for integration coverage; R.1 preregisters its model comparison.

## Persuasion → enforcement

No Pi hook is applicable to offline grading. Trusted execution, assertion coverage,
independent state and explicit grader identity enforce the contracts after exit.

## Close

Follow [the cycle procedure](../../../sdd.md#branches-and-worktrees). Rebase only if
integration moved; squash the reviewed cycle into `integration` without switching
the main checkout. Verify equal trees, archive the managed worktree from a retained
checkout, then delete `codex/suite-oracle-fixes`. Do not push without a request.

## Result

Closed 2026-11-07. Trusted grading, aligned current contracts, thirteen Easy checks,
retained historical inputs and grader provenance shipped. All nine independent-review
findings were fixed with failing witnesses; 38 review/runner/scoreboard tests pass.
`npm test`: 643 passed, 3 skipped; ladder: 223 passed. All twelve historical fixture
controls matched. No model run or rate claim. [Evidence](../../research/2026-11-07-suite-oracle-repairs.md).
