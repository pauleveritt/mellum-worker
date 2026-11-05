---
phase: LC
feature_cycle: LC.34
cycle: 1
lifecycle: closed
---

# Protected Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add an explicit protected completion gate and measure bounded repair
against the same selective-remedy control, with complete quality/budget records.

**Architecture:** Pi's settle hook requests checks; a host controller owns the
deadline, allowance, snapshot and receipt. Trusted assertions run outside
candidate execution; a separate contained candidate produces bounded probe
observations. The host independently rechecks the final artifact.

**Tech Stack:** Pi 1.4.0, TypeScript/Node 24, Python 3.14 via uv, existing
temporary Docker adapter, pinned local llama.cpp build 11669.

**Spec:** [Protected acceptance design](../../specs/2026-11-04-protected-acceptance-design.md).

## Global Constraints

- Thin worker and presets unchanged; opt-in `check/external-acceptance` only.
- Two repairs; at most three settle checks and one final independent check.
- Shared 600s task deadline, 30s/check within remaining time, 180s open-tool cutoff.
- Repair feedback at most 8,000 characters; never include hidden-grader output.
- Twenty fresh sequential tasks/arm; alternate S,G; eight-hour batch safety cap.
- Frozen previous M5 Max/Pi/llama.cpp/model/sampling/tools; no Runpod or uploads.
- RED before implementation for each new test; atomic pushed commits.
- Run Python with uv; retain raw traces only in ignored `runs/`.

## Review Focus

1. Forged/missing/stale model mailbox data must never become host acceptance.
2. Candidate imports, pytest plugins and early exit must not own assertions.
3. Final exhausted check, post-check mutation and no remaining deadline fail closed.
4. Repair continuation preserves task injections and accounts for compaction.
5. Controller death/cutoff removes only owned resources and preserves partial work.

## File responsibilities and interfaces

- `learn/code/acceptance.py`: host-only package validation, state machine,
  receipts and feedback. Define `AcceptancePackage.load(path: Path)`;
  `Gate(task_id: str, package: AcceptancePackage, deadline_at: float,
  max_repairs: int = 2)`; `Gate.apply(result: dict, snapshot_sha256: str,
  *, final: bool = False) -> dict`; `Gate.remaining() -> float`.
- `learn/code/acceptance_containment.py`: host adapter, mailbox, snapshots and
  check deadlines. Define `check_snapshot(snapshot: Path, package:
  AcceptancePackage, image: str, control: Path, timeout: float) -> dict` and
  `run_model_with_gate(container, argv: list[str], gate: Gate, workspace:
  str, control: Path, output) -> subprocess.CompletedProcess`.
- `remedies/check/external-acceptance.ts`: asynchronous settle exchange,
  `install(pi, options?)`; no acceptance assertions or trusted counters.
- `learn/code/acceptance/easy-phase1/{manifest.json,checker.py}`: explicit
  requirement coverage and trusted assertions derived only from public specs.
  Checker exports `evaluate(snapshot: Path, probe, remaining) -> dict`.
- `learn/code/acceptance_probe.py`: host-side `CandidateProbe(image: str,
  snapshot: Path, control: Path)` context manager; `run(name: str, inputs:
  dict, timeout: float) -> dict` selects a fixed, bounded candidate operation.
  Candidate operations live in `scripts/containment/probe.py`; no arbitrary
  model-selected command or host path.
- `learn/code/acceptance_qualification.py`: oracle variants, seeded omissions,
  tampering and actual-Pi qualification; writes hashed qualification evidence.
- `scripts/acceptance_overnight.py`: frozen collection, ownership/watchdog,
  reconciliation, reporting; `--prepare`, `--run`, `--recover` entry modes.

## Task 1: Host state machine and receipt contract

**Files:** Create `learn/code/acceptance.py` and
`learn/code/tests/test_acceptance.py`.
**Consumes:** frozen package path, task identity, monotonic deadline.
**Produces:** `AcceptancePackage`, `Gate` and validated host decisions above.

- [x] Write `test_initial_pass`, `test_two_repairs_and_last_failure`,
  `test_final_recheck_cannot_repair`, `test_shared_deadline` and
  `test_invalid_package_or_result`: assert pass is possible only with every
  declared requirement, empty/missing/duplicate IDs fail, invalid limits fail,
  repairs never exceed two and the final failed check is retained. Include
  bool-as-integer, nonfinite timeout and malformed status inputs.
- [x] Run `uv run --with pytest pytest learn/code/tests/test_acceptance.py -q`;
  observe failures before creating production code.
- [x] Implement the interfaces. Package hash covers manifest, public spec hashes
  and every declared runner/probe file; reject links/path traversal. Results
  contain requirement ID, pass/fail and bounded observation. Host owns sequence,
  snapshots, timing, terminal status and max feedback size. Checksum changes,
  incomplete results and checker exceptions are terminal, never repairable.
- [x] Repeat focused tests; add explicit final-pass versus Pi-abort separation.
- [x] Update CHANGELOG/FIXES and commit this independently tested foundation.

## Task 2: Contained exchange and opt-in remedy

**Files:** Create `learn/code/acceptance_containment.py`,
`remedies/check/external-acceptance.ts`, `tests/external-acceptance.test.mjs`;
modify `learn/code/containment.py`, `learn/code/harness.py`,
`scripts/containment/entry.py`, `scripts/containment/Dockerfile` and
`learn/code/tests/test_containment.py`.
**Consumes:** Task 1 interfaces and existing `Container` ownership/extraction.
**Produces:** live same-task checks plus host-authoritative terminal receipt.

- [x] Write failing tests for unavailable-controller preflight, pass without
  continuation, fail with continuation, exhausted final check, stale/duplicate
  exchange IDs, malformed/oversized mailbox and timeout. Assert disabling a
  remedy cannot erase host state and no injection is duplicated on continuation.
- [x] Run node/Python focused tests and retain the RED output.
- [x] Add optional `run_name: str | None` and `gate_config: dict | None` to
  `run_suite`; validate the host-chosen run name. Gate config supplies only the
  task ID and constant mailbox path in the container, not the package path.
  Native runs reject the protected remedy without a controller before inference.
- [x] Add `Container.snapshot(path: str, destination: Path)`: pause, safely
  export regular files and always unpause; keep existing final export behavior.
  Include new generic Python/probe sources in image copying and source hashes.
- [x] Implement `run_model_with_gate`: bounded subprocess polling, constant
  `/attempt/gate/request.json` mailbox, atomic replies, snapshot path selected
  solely by host task ID. Process each observed request once. Host caps total
  settle checks, waits and checks by remaining time; preserve journal before
  replying. Gate-on and gate-off share the same model runner and settings.
- [x] Implement the remedy at `agent_before_settle`. Failed requirements plus
  host-approved repair allowance return custom-message entries and `continue`;
  pass/exhaustion/error ends inference. Host terminal state distinguishes these.
  Check errors cannot yield accepted completion even if Pi swallows hook errors.
- [x] Before container removal, freeze/export final artifact and run the
  independent host-selected check with remaining time; no extra inference.
  Cross-check child exit, abort/completion trace and host terminal state.
- [x] Run focused tests plus fake-provider actual-Pi pass, repair and exhausted
  tasks. Refresh remedy discovery using the repository's existing generator.
  Update CHANGELOG/FIXES and commit.

## Task 3: Qualified external Phase 1 assertions

**Files:** Create package, probe and qualification files from the file map;
create `learn/code/tests/test_acceptance_checker.py` and
`learn/code/acceptance/fixtures/`; modify image sources as needed.
**Consumes:** Task 1 package/result schema; Task 2 snapshot and timeout adapter.
**Produces:** `check_snapshot` using qualified, complete requirement coverage.

- [x] Write failing checker tests for two valid variants and individual seeded
  omissions for every Phase 1 requirement. Cover title override with differing
  valid block names, extra charset meta, Bootstrap markup variants, nested hero
  content, uvicorn object/reload failure, main-guard import side effects and 422.
  Add corrupted syntax, empty tests, modified base inputs and early models.py.
- [x] Observe RED with the exact focused pytest command before implementation.
- [x] Implement trusted host-side static/HTML assertions and `CandidateProbe`.
  The probe container receives only the candidate snapshot and fixed helper,
  no checker package, host sockets, inference or credentials. Candidate imports,
  startup, Jinja render and project pytest execute there; host assertions inspect
  only bounded data. Use prewarmed pinned dependencies, fresh subprocesses and
  per-probe remaining-time limits. Reap startup/reloader descendants in finally.
- [x] Matrix every public Phase 1 clause and applicable project constraint to
  stable requirement IDs in manifest. Label semantic proxies and manual limits;
  do not infer requirements from hidden tests. JSON must contain every ID once.
- [x] Seed malicious conftest/plugin/config, `exit(0)`, forged mailbox/receipt,
  mutable package and post-settle artifact. Prove these cannot change checker
  assertions/host receipt or cause false acceptance; distinguish invalid
  candidate observations from broken checker infrastructure.
- [x] Qualify both valid builds and every mutation in actual containers; block
  collection on any mismatch. Hash checker/spec/fixtures and all results.
- [x] Run focused tests, existing containment qualification and full npm suite.
  Update CHANGELOG/FIXES and commit; no counted run yet.

## Task 4: Budget instrument, overnight controller and registration

**Files:** Create `learn/code/acceptance_budget.py`,
`scripts/acceptance_overnight.py`, `learn/code/tests/test_acceptance_budget.py`,
`learn/code/tests/test_acceptance_overnight.py` and
`docs/superpowers/research/2026-11-04-protected-acceptance-protocol.md`;
modify `extensions/mellum-recorder.ts` only for measured compaction gaps.
**Consumes:** Tasks 1–3; existing baseline ownership, manifests and scorecard.
**Produces:** frozen preparation, bounded collection and independent budget sum.

- [x] Write RED tests for all-generation accounting (failed request, thinking,
  compaction and unknown usage), interval association, total/per-usable budget,
  all-fail zero denominator, altered manifest, occupied port, identity mismatch,
  controller death and too little batch time to start a full task.
- [x] Implement passive reconciliation against host relay/server timings. Never
  replace missing usage with a partial sum. Keep unknown request classification
  explicit; total inference accounting must still include it. Add native
  compaction completion/failure trace events if qualification shows need.
- [x] Implement preparation/build/qualification before server launch, then live
  actual-Pi qualification (including forced compaction), source/runtime/model
  readbacks, frozen manifest and sequential S,G order repeated twenty times.
  Reuse qualified local argv/profile from controlled6 without retuning.
- [x] Implement a separate eight-hour identity-checked watchdog plus finally
  cleanup; recover only recorded owned processes/containers/volumes. Stop on
  integrity or qualification failure. Reserve 600s plus 60s cleanup before
  starting each task; bounded grading and shutdown obey the global cutoff.
- [x] Write the preregistration before collection: all usability components,
  exact 18/20 candidate threshold, at least control successes, no higher output
  tokens per usable result, unknown-budget/no-decision rule, Wilson intervals,
  infrastructure exclusions, no optional stopping and local upload hold.
- [x] Run RED/GREEN tests, `npm test`, docs caps and site build; request a fresh
  whole-change review per execution skill. Fix consequential findings with
  regressions. Commit implementation and registration; retain no raw in Git.

## Task 5: Overnight execution, analysis and close

**Files:** local `runs/<batch>/`; curated `evals/<batch>/`; roadmap, changelog,
glossary/pathologies if new concepts or observed failures require them.
**Consumes:** passing review, preparation/qualification and frozen registration.
**Produces:** complete or explicitly incomplete comparison and verified shutdown.

- [x] Start only the qualified frozen batch. Retain all forty planned outcomes,
  initial and repair snapshots, checker receipts and every inference request.
  If cutoff/integrity stops collection, report incomplete; do not lower n.
- [x] Regrade S and G final artifacts identically with independent acceptance,
  hidden, health, layout and nonempty project tests. Audit semantic proxy limits
  manually without changing the registered outcome definition.
- [x] Report all quality components, initial versus repaired outcomes, rescued
  tasks, gate false passes/failures, totals/medians/distributions, repair budget,
  Wilson intervals and candidate rule. No cross-task or later-phase claims.
- [x] Independently verify owned inference, guardian, containers and volumes
  stopped; package and scan raw locally, keep upload hold. Preserve setup and
  infrastructure budgets separately; never discard model failure costs.
- [x] Update FIXES/CHANGELOG and cycle status, reconcile evidence claims,
  verify docs/npm, append Result and archive plan only after cycle is complete.

## Self-review

Tasks 1–2 own lifecycle/bounds and forged control input; Task 3 owns checker
coverage and candidate/assertion isolation; Task 4 owns complete accounting,
registration and shutdown; Task 5 owns final measurement and closure. All five
Review Focus items have named regressions above. No implementation or counted
task has started as of this plan's creation.

## Result

Completed 2026-11-05: explicit protected gate, qualified host assertions, two
bounded same-task repairs, independent final verification, compaction accounting
and guardian-owned shutdown. Fresh review findings fixed with regressions.

The fixed forty-task cohort produced selective1/20 versus gated11/20 usable,
29 repairs, hidden80/80 and health19/20 per arm. The gate missed18/20. G12
interrupted output remains unknown, so the registered joint decision is
no-decision. No preset or reliability default is promoted. Two oracle correction
cohorts remain separate qualification costs; none of their outcomes is reused.

[Evidence](../../../../evals/2026-11-05-protected-acceptance/README.md) includes
every task, scoped budgets, semantic/typing limits and independent shutdown
verification across237 ownership records. Inputs unchanged; owned inference and
resources stopped. Raw upload remains held. Local commits await explicit
public-push approval after automatic approval review rejected publication.

Final verification:121 focused Python tests and665/665 npm tests passed;
document caps and Zensical build clean. Changelog reconciled for this cycle.
