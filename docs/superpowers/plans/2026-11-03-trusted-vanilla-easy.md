---
phase: LC
feature_cycle: LC.31
cycle: 1
lifecycle: active
---

# Trusted Vanilla Easy baseline implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the user chooses delegation. Implement task-by-task; do not collect model results before Tasks 1–3 pass.

**Goal:** Repair the measuring instrument, then retain six trustworthy Easy
Vanilla Pi sessions for later worker comparisons.

**Architecture:** Extend Andre's existing session runner and grader. Add a
small batch/provenance helper and a pinned `baseline` subcommand to that same
harness, not another Pi launcher. Keep the six-field scorecard separate from
diagnostic traces and existing legacy evidence tables.

**Tech stack:** Python 3.14 via uv, Node's test runner, pinned Pi 1.4.0,
the existing local llama.cpp backend and Q4_K_M model. No new runtime dependency.

**Spec:** [Approved design](../specs/2026-11-03-trusted-vanilla-easy-design.md).

## Delta from Andre's current implementation

This compares against the checkout at `2a7f684`, not historical descriptions of
the bundled worker. Existing capabilities below are source-verified; changes
remain planned until their tests pass. No harness or worker rewrite is needed.

| Area | Andre already has | Add / change / delete |
| --- | --- | --- |
| Vanilla execution | `arm_settings("vanilla")` loads only the recorder; fresh workspace/profile; hidden grader copied after execution | **Keep.** Assert these invariants in the new baseline command; no prompt, skill, tool, or remedy changes. |
| Limits | `wait_or_stall()` enforces a deadline and an open-call-age cutoff | **Keep mechanism. Add** the approved 600/180 values to one canonical command. This is not an output-idle timeout. |
| Pi pin | `scripts/pi-pin.env` pins 1.4.0; installers and run.sh consume it | **Reuse pin. Add** strict collection preflight and resolved executable recording; leave generic exploratory `--pi-binary` support intact. |
| Backend | `scripts/backend.py` starts/checks llama.cpp; default profile names the model and sampling | **Reuse. Add** read-only identity/config verification for collection. Never stop another server or hand-build an oMLX profile. |
| Functional grade | Four expected Easy checks, missing IDs, collection status, known-good/broken qualification | **Keep oracle. Add** explicit passed/total fields to the compact report. Do not expand tests or reinterpret missing checks as executed failures. |
| Code health | Optional Ruff F,E9 and Complexipy threshold 10; Pyrefly advisory | **Change** unchecked health from implied success to explicit not checked. **Add** retained checker results/output and version provenance. Preserve existing checker policy. |
| Outcomes/time | Deadline/stall marker files; trace-derived wall; native settlement rows | **Add** launch-to-exit elapsed time, process status and explicit completion. Preserve artifact grade independently. Retain legacy budget keys; stop using trace span as execution wall in new records. |
| Provider failures | Trace contains provider errors, but summary can count a dead server as model FAIL | **Add** evidence-based infrastructure classification, visible exclusions and stop/resume; no automatic removal of errors after substantive work. |
| Cleanup | Finally sweeps Pi's group and processes with workspace cwd; SIGTERM unwinds | **Add** ownership/locking, verified cleanup and stale-owned-run recovery after SIGKILL. **Reject** FIXES F.5's broad kill-all-under-root interpretation. |
| Request recording | Recorder is loaded last; Pi 1.4 chains returned payloads into later handlers | **Keep unless a regression proves otherwise.** Verify with a controlled rewrite; **correct** FIXES F.1's pre-hook/prompt-swap assumptions with a dated note. |
| Reporting/storage | `run.json`, full trace, mean evidence table, fastest-pass scoreboard; default runs in temp | **Add** a compact per-attempt scorecard and shared batch manifest in ignored durable runs/. Keep legacy tables/scoreboard available; do not use their ranking for this baseline. |
| Documentation | Harness page and historical parallel/GPU baseline scripts | **Change** the harness page to name the canonical local collection command. **Delete no historical script or evidence.** Mark other configurations as different measurements. |

No worker/remedy implementation is added, changed, or deleted. F.7 and the
choice of baseline prerequisites remain a separate discussion. No existing
record or archived plan is edited. The only removals in scope are misleading
current wording and unchecked-success/trace-span assumptions in the new path.

## Global constraints

- Easy only; six counted sessions; Vanilla Pi plus recorder only; cold context.
- Deadline 600 s; tool-call-age cutoff 180 s; sequential fresh sessions.
- Keep model, sampling, suite, hidden grader and quality-check policy unchanged.
- Hidden checks, code health and completion stay separate from the budget.
- Budget is model turns/provider requests, output tokens and execution elapsed.
- Show all attempts; infrastructure exclusions need retained evidence and reasons.
- Raw trace.jsonl, stdout.txt and diff.patch never enter git.
- Update FIXES.md as changes land; changelog accompanies commands/records/docs.
- New tests are demonstrated failing before the corresponding implementation.

## Review focus

1. A correct artifact followed by a hung tool still grades correctly and says stalled/deadline.
2. No native settlement, aborted settlement, or a terminal provider error never says settled.
3. Missing grading/usage evidence says not checked/unknown, rather than passing or zero.
4. SIGKILL recovery never kills another live collection or unrelated server.
5. Resume rejects changed inputs and never reruns a model failure to improve the six results.

## Files and responsibilities

- `learn/code/harness.py`: existing execution/grade path, trustworthy run fields,
  canonical baseline CLI and calls into the batch helper.
- New `learn/code/baseline.py`: batch ownership, preflight/provenance,
  counted/excluded attempt bookkeeping, resume and compact rendering. It never
  launches Pi or duplicates grading; it consumes the harness's existing runner.
- `learn/code/tests/test_harness.py`: execution/record regressions.
- New `learn/code/tests/test_baseline.py`: preflight, ownership, resume and report.
- Existing `ladder/ladder/record-pi.test.mjs`: controlled recorder rewrite check.
- `learn/getting-started/the-harness.md`, `FIXES.md`, `CHANGELOG.md`: user command,
  accurate implementation history, and changes to records/behavior.

## Task 1: Make run outcomes and the six-field scorecard trustworthy

**Interfaces:** `run_suite(...) -> Path` remains compatible. It additionally
writes `execution.json` with elapsed_seconds, exit_code, termination_reason and
cleanup_ok. `run.json` adds completion, elapsed_seconds, code_health,
checks_passed, checks_total and provider_error; retains existing fields.
`quality_ok` is null when not checked; ungraded legacy pass behavior uses
`quality_ok is not False`. A passed artifact never implies settled execution.
`_run_sessions(...)` accepts optional `grade_versions: dict[str, str] | None`
and passes it to grade; the new collector supplies the frozen batch versions.

- [ ] Add failing regression tests: `test_elapsed_includes_silent_tail` asserts
  elapsed includes sleep after the last trace row, excludes grading, and agrees
  with recorded process lifetime; `test_artifact_pass_can_stall` asserts hidden
  pass and completion stalled coexist; `test_settlement_requires_native_evidence`
  covers absent/aborted settlement, nonzero exit, terminal error and recovered
  error followed by clean settlement. Extend fake-Pi fixtures only as needed.
- [ ] Add `test_code_health_not_checked_is_explicit` asserting code_health is
  not checked and quality_ok is null without --grade; a missing checker cannot
  pass. `test_checker_outputs_are_retained` asserts status, tool version and
  stdout/stderr survive in a diagnostic grade.json, outside the compact report.
  `test_collection_error_is_not_four_executed_failures` pins the displayed label.
- [ ] Show each new test red with `uv run --with pytest python -m pytest
  learn/code/tests/test_harness.py -q -k 'elapsed_includes_silent_tail or
  artifact_pass_can_stall or settlement_requires_native_evidence or
  code_health_not_checked or checker_outputs or collection_error'`.
- [ ] Record execution timing/status around Pi launch/wait, always persist it
  through interruption/finally, and derive completion from termination plus
  native events. Set new run.json wall to actual execution elapsed; standalone
  legacy trace analysis remains available and is not relabeled authoritative.
- [ ] Preserve checker results/full output; retain the existing advisory type
  policy. Extend `grade(workspace: Path, *, versions: dict[str, str] | None = None)`
  to accept versions resolved once for the batch; use exact --with package==version
  requirements during collection. Generic grading keeps its existing behavior.
  Preserve unknown token usage as null. Persist provider error evidence;
  zero valid work plus confirmed provider failure is infrastructure, while an
  error after work is flagged for review, not silently excluded.
- [ ] Add `render_scorecard(records: list[dict]) -> str` in baseline.py. Tests
  assert exactly six score fields plus run ID, explicit unknown/not-checked,
  and correct labels for hidden checks not executed. Keep evidence.py's legacy
  means and scoreboard ranking unchanged. Add concise start/completion output
  before/after each session; diagnostic output stays available in retained logs.
- [ ] Add the controlled request-rewrite test using installRecorder and ordered
  handler composition. Audit local Pi's runner.ts emitBeforeProviderRequest;
  document that later handlers receive currentPayload. Do not change the
  recorder if this confirms its existing ordering.
- [ ] Run relevant Python tests, recorder tests and CLI tests; update FIXES
  F.1/F.4 with dated findings/verification and CHANGELOG Unreleased; commit
  `fix(harness): record execution outcome and compact quality budget metrics`.

## Task 2: Recover interrupted collections without leaking or overreaching

**Interfaces:** baseline.py supplies `collection_lock(root: Path)` as a context
manager and `reap_stale_runs(root: Path) -> list[dict]`. run_suite records an
owner identity (PID plus process-start identity), launched child/group and run
workspace before waiting. Existing group/workspace sweep functions are reused.
Collector holds a POSIX advisory lock through the batch; no nested lock inside
run_suite. This local collection path targets macOS/Linux like the current rig.
The lock root is the shared repository runs/ directory, not each timestamped
batch; concurrent baseline invocations therefore contend for the same lock.

- [ ] Add failing `test_sigkill_then_resume_reaps_only_owned_processes`: SIGKILL
  a fixture runner after its detached child starts, resume, assert the stale
  child exits, an unrelated child survives, and recovery is recorded.
  `test_live_collection_is_not_reaped` asserts a second owner refuses access;
  `test_reused_pid_is_not_trusted` covers stale owner identity validation.
- [ ] Add `test_cleanup_failure_stops_before_grading`: a failed verified sweep
  produces error/cleanup_ok false and no hidden-grade invocation while a writer
  could still mutate the workspace. Test graceful SIGTERM as well as SIGKILL.
- [ ] Run those tests red using uv run --with pytest python -m pytest.
- [ ] Implement owner records and lock; only reap stale runs with ownership
  evidence. Verify group/workspace sweeps left no owned process. Refuse an
  unverifiable ownership/cleanup state instead of killing broadly or continuing.
  A crash leaves a readable incomplete attempt for recovery, not a counted pass.
- [ ] Run cleanup regressions on this Mac; run the existing interruption tests.
  Update FIXES F.5 and CHANGELOG, then commit
  `fix(harness): recover owned processes after interrupted collections`.

## Task 3: One pinned, resumable baseline command with shared provenance

**Interfaces:** `uv run python learn/code/harness.py baseline` creates a batch in
`runs/vanilla-easy-<UTC timestamp>/`. `baseline --resume DIR` continues it;
`baseline --dry-run` prints its resolved configuration without contacting the
model. Fixed collection values: suite easy, arm vanilla, repeat target 6,
grade true, deadline 600, stall 180, default profile, no extras/context files.
General exploratory `run` remains available; this command accepts no arm,
model, sampling, remedy, suite or limit overrides.

baseline.py supplies `preflight(pi_binary: Path, profile: Path) -> dict`,
`create_manifest(repo: Path, preflight: dict) -> dict`, and
`validate_resume(saved: dict, current: dict) -> None`. Harness's
`collect_baseline(*, resume: Path | None = None, dry_run: bool = False,
exclude: str | None = None, reason: str | None = None) -> int` qualifies the
suite and invokes _run_sessions
with repeat=1 for each attempt; it never implements a second Pi launch/grade path.

- [ ] Add failing `test_baseline_resolves_pin_and_fixed_arguments`: resolve
  explicit installed Pi candidates (including ~/.local/bin/pi and PATH) against
  scripts/pi-pin.env; an old PATH Pi cannot win silently. A missing pin match
  fails with the existing install guidance, never installs/upgrades on its own.
  Fake binaries remain usable in generic run tests; collection preflight is strict.
- [ ] Add `test_preflight_rejects_wrong_backend_or_model`: fake HTTP responses
  for unhealthy server, oMLX-shaped health, wrong model, mismatched model/config
  identity and incomplete provenance all fail before Pi launches. Reuse backend.py
  settings/version/model-identity helpers where applicable; extend read-only
  probes only where needed. No stop/start/restart side effect in preflight.
- [ ] Add `test_manifest_freezes_shared_inputs`: capture command, resolved Pi,
  running backend build, model file/quantization identity, machine, effective
  profile, checker versions and hashes of harness/recorder/suite/grader.
  Distinguish the running server's identity from an arbitrary binary on PATH.
  Hash model contents once per batch if no verified immutable identity is available.
- [ ] Add `test_resume_rejects_changed_inputs`, `test_six_counts_failures_and_stalls`,
  `test_infrastructure_stops_and_requires_exclusion_reason`, and
  `test_resume_never_repeats_a_counted_attempt`. Store all attempt IDs plus
  counted/excluded/pending-review state and explicit reasons. Exit on an
  infrastructure failure for diagnosis; resume may accept `--exclude RUN_ID
  --reason TEXT` only for an uncounted flagged attempt, preserving the original.
  Incomplete crash attempts remain visible and require classification.
  Compare material input fingerprints on resume, not timestamps, run IDs, or
  a git commit changed only by documentation/evidence updates.
- [ ] Run every new test red, implement the subcommand/helper, then run them green.
  Before counting, verify trace instance identity and expected recorder-only
  launch arguments; invalid/missing identity pauses collection for diagnosis.
  Flush a start notice and compact result after each attempt. Redirect/copy full
  child and checker output to durable per-attempt files without grep/tail loss.
- [ ] Document the canonical command, server-start prerequisite, dry-run/resume,
  exact cutoff meaning, and six-field scorecard in the harness page. Update FIXES
  F.2/F.3/F.6/F.8/F.9 only to the extent implemented; oMLX and worker fixes remain
  deferred. Reconcile CHANGELOG; run relevant tests and commit
  `feat(harness): add pinned resumable Vanilla Easy collection`.

## Task 4: Qualify, collect six, preserve evidence and close

**Interfaces:** completed batch contains batch.json, per-attempt run directories
and scorecard.md. Curated `evals/2026-11-03-vanilla-easy/` contains the compact
scorecard, manifest and exclusion/provenance notes, never raw trace/stdout/diff.
If collection happens on a later date, use its actual date for the evidence path.

- [ ] Run `node --test tests/docs-caps.test.mjs`, `npm test` and
  `uv run --with pytest python -m pytest learn/code/tests -q`. Diagnose failures;
  record pre-existing failures explicitly rather than claiming a clean suite.
  Qualify Easy using the existing harness qualify command. Do not alter the oracle.
- [ ] Commit/checkpoint the verified instrument before counted runs. Print the
  baseline dry-run and inspect the resolved Pi, profile, Vanilla extension list,
  limits and grading. Preflight must pass; if the port holds another service,
  stop and explain instead of replacing it. Start backend.py only if needed and
  compatible with the user's active local services.
- [ ] Run the documented baseline command visibly, with the Mac kept awake.
  Give progress at least once per minute; inspect live trace when a call stalls.
  Count six valid model sessions regardless of success; stop on infrastructure
  failure, retain evidence, diagnose and resume explicitly. No speculative reruns.
- [ ] Verify six counted IDs, all exclusions/reasons, grader absence during
  execution, runtime identities, grade results, and no remaining owned processes.
  Generate the compact scorecard; preserve passing artifacts with stalled/error
  completion as two separate facts. Summaries must not substitute cheap failures
  or a single best pass for the whole sample.
- [ ] Promote compact evidence to evals and preserve raw directories under runs/;
  follow existing research-release rules for raw evidence promotion. State six
  local sessions, coverage limits, configuration identity and reuse conditions.
  Add no claim that the worker is better/worse; it has not been measured here.
- [ ] Update FIXES with implemented changes, verification and baseline location.
  Add glossary/pathology entries only for concepts/findings actually introduced;
  reconcile CHANGELOG with commits since the last release tag. Update LC.31/Now,
  add plan Result, archive this plan, rerun docs caps and npm test after doc edits,
  and commit `eval: retain six-session Vanilla Easy reference`.

## Execution handoff

Recommended: native execution in this session. The tasks share runner/record
interfaces; one implementer avoids repeated context setup, with one fresh
whole-branch review before closing. User approval of this plan and execution
method precedes product edits and collection. FIXES.md is updated as fixes land,
not marked implemented merely because this plan names them.
