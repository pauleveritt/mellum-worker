---
phase: M.7C
cycle: 1
lifecycle: closed
---

# M.7C Pi harness telemetry implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Reconstruct two existing ladder smoke runs with verified Pi launch,
correlated observational evidence, and unchanged legacy scoring.

**Architecture:** Extend the existing runner and `trace.jsonl` recorder.
Keep launch preflight and trace validation in two small Python modules,
without moving unrelated runner code. Shipped extensions remain unchanged.

**Tech stack:** Python 3.14, uv/pytest, Node 24 built-ins and node:test,
Pi 1.1.0 extension hooks, existing pi-subagents and oMLX.

**Spec:** [M.7C design](../../specs/2026-10-11-m7c-pi-harness-telemetry-design.md),
approved by Paul on 2026-10-11. Read `docs/sdd.md` before editing records.

## Global constraints

- Research baseline exactly Pi 1.1.0, isolated installation; no global upgrade
  or new shipped Pi minimum. Default CLI selection remains `pi` for other runs.
- Preserve prompt, tools, sampling, guards, shipped schema-2 records and `learn`.
- Keep legacy event types/payloads and historical scores unchanged.
- Missing native fields remain unknown, not zero or false.
- No suite, judge, dashboard, scheduler, generalized host adapter or recovery policy.
- Exactly two initial counted smokes: existing rung 1, Mode and Worker.
- Raw traces, stdout and patches stay outside Git; reviewed assets have hashes.
- Every new test is seen failing first. No new dependency or npm lifecycle script.

## Review focus

1. Executable paths containing spaces or symlinks resolve without shell parsing.
2. A Worker inherits an alternate runtime override: counted evidence must detect
   the mismatch rather than trust the parent's version.
3. A stream event outside an observed request boundary keeps a null association.
4. A truncated final trace line preserves earlier records and reports incomplete evidence.
5. A tool ID reused in another instance never merges the two executions.

Each condition has an owning test below. Native execution is recommended:
three tightly related tasks, no shipped behavior change, one final review.

## File map

- Create `ladder/ladder/pi_launch.py`: selected executable and fixture preflight.
- Modify `ladder/ladder/run_ladder.py`: integration and runner outcome metadata.
- Modify `ladder/ladder/record-pi.js`: read-only event capture.
- Create `ladder/ladder/pi_trace.py`: tolerant trace reading and integrity summary.
- Create `ladder/ladder/record-pi.test.mjs`: fake-hook tests, automatically included
  in the existing `npm test` glob.
- Create `ladder/tests/test_pi_launch.py`, `ladder/tests/test_pi_trace.py`;
  extend `test_runner.py` and `test_score.py` only where integration needs them.
- Create small fixtures under `tests/fixtures/telemetry/`, with `README.md` provenance.
- Update `docs/recipe.md`, `CHANGELOG.md` alongside changed ladder commands/records.
- Create `evals/2026-10-11-smoke-m7c/` records and a short M.7C research finding;
  update `evals/PROVENANCE.md` and `ROADMAP.md` at closure.

## Task 1: Verified launch

**Files:** `pi_launch.py`, `run_ladder.py`, `test_pi_launch.py`,
`test_runner.py`, `docs/recipe.md`, `CHANGELOG.md`.

**Interfaces:**

- `resolve_pi(executable: str) -> dict`: returns resolved `executable`,
  reported `version`; raises `RuntimeError` with a useful diagnostic on failure.
- `workspace_preflight(ws: Path, fixture: str, parent_env: dict[str, str])
  -> tuple[dict[str, str], dict]`: returns launch environment and sanitized
  provenance; raises `RuntimeError` before model launch on an invalid environment.
- `run_once(..., pi_executable: str = "pi") -> dict`: keyword appended to
  its existing interface. Existing argument builders remain unchanged;
  replace their leading executable at the launch boundary for every mode/step.

- [x] Write tests named `test_resolve_pi_path_and_symlink`,
  `test_selected_pi_used_for_version_and_launch`,
  `test_python_preflight_uses_fixture_environment`,
  `test_preflight_failure_never_launches_pi`, and
  `test_delegated_runtime_override_is_selected_pi`.
  Use controlled fake executables/subprocess responses, no server or model.
  Assert argv is a list; resolved path is used for both version/launch;
  Python comes from fixture `.venv`, not the ladder; failed import stops launch;
  inherited `PI_SUBAGENT_PI_BINARY` is replaced with the selected executable.
  Key assertions after arranging controlled executable/environment inputs:

  ```python
  assert launched_argv[0] == resolved["executable"]
  assert version_argv == [resolved["executable"], "--version"]
  assert env["VIRTUAL_ENV"] == str(ws / ".venv")
  assert env["PI_SUBAGENT_PI_BINARY"] == resolved["executable"]
  assert model_launches == []  # failed import case
  ```

  Add `test_non_python_preflight_records_node`: Node identity present,
  fixture Python absent, and no unrelated Python environment is inherited.
- [x] Run from `ladder/`: `uv run python -m pytest tests/test_pi_launch.py tests/test_runner.py -q`.
  Confirm each new assertion fails for the missing behavior before implementing it.
- [x] Implement the two helpers and `--pi-executable` CLI option, default `pi`.
  Resolve/probe once per ladder invocation and record provenance per run.
  Missing executable, unsuccessful version probe and failed fixture sync/import
  are actionable preflight failures, not `unknown` for counted new launches.
- [x] Keep existing offline fixture sync; check its return status. For Python
  fixtures, put verified `.venv/bin` first in PATH and set VIRTUAL_ENV to that
  fixture only, after `child_env` removes the inherited ladder environment.
  Probe `sys.executable` and `pytest`; AgentClinic also probes `fastapi`,
  `turbohtml`, `httpx`. For rung 1's JavaScript fixture, record Node identity
  and mark Python preflight not applicable. Use argument lists, never shell text.
- [x] Set `PI_SUBAGENT_PI_BINARY` to the selected resolved executable for
  delegated runs, using the installed host's existing supported override.
  Capture the installed pi-subagents Git revision (or explicitly unknown);
  final counted compatibility proof requires an identified revision.
  Do not patch pi-subagents or invent another launcher.
- [x] Add `run.json.launch` containing command argv, cwd, Pi path/version,
  Node identity, optional fixture Python path and checked imports, and
  pi-subagents revision when delegated. Do not serialize auth/settings or
  the whole environment. New metadata is additive; preserve old fields.
- [x] Run the targeted tests, then from `ladder/` run
  `uv run python -m pytest`, and from repo root run `npm test`.
  Expected: zero failures. Adapt existing mocks only for the new launch boundary.
- [x] Document the new option beside the ladder command in `docs/recipe.md`;
  add its user-facing Unreleased entry. Review diff and changelog since v0.1.6;
  commit as `feat(ladder): verify selected Pi and fixture environment`.

## Task 2: Additive observation and honest lifecycle evidence

**Files:** `record-pi.js`, `record-pi.test.mjs`, `pi_trace.py`,
`test_pi_trace.py`, `run_ladder.py`, `test_runner.py`, `CHANGELOG.md`.

**Interfaces:**

- Keep recorder's default `install(pi)`; expose
  `installRecorder(pi, options = {})` for tests. Options inject `write(record)`,
  `diagnose(text)`, clocks and runtime identity; default wrapper uses local
  JSONL append and stderr. No new exported host abstraction.
- Event metadata: `traceSchema: 1`, `runId`, `instanceId`, `seq`, `timestamp`
  (UTC ISO), `elapsedMs` (local monotonic), `pid`, `requestId` (nullable).
  Retain native `toolCallId` and `parentToolCallId` when present.
- `load_trace(path: Path) -> tuple[list[dict], list[str]]`: preserves valid
  records in order and returns parse diagnostics instead of discarding the file.
- `summarize_trace(events: list[dict], diagnostics: list[str], stderr: str,
  expected_pi: dict) -> dict`: returns `status` (`ok`, `incomplete`, `legacy`),
  `issues`, and per-instance runtime/settlement/open-call evidence.
  This checks instrumentation integrity, not task success.

- [x] Add fake-hook tests for `metadata and request association`,
  `two instances sharing a PID`, `unassociated chunks after settlement`,
  `blocked and unfinished tools`, `optional native duration and abort`,
  `sink failure is diagnostic only`, and `observer leaves inputs and returns unchanged`.
  Assert distinct instance UUIDs and local sequences; old payloads unchanged;
  chunks keep their original data; absent duration/abort stays absent;
  all observer return values are undefined. Freeze input objects.
  Key assertions for captured records and the input snapshot:

  ```javascript
  assert.notEqual(first.instanceId, second.instanceId);
  assert.deepEqual(request.payload, originalPayload);
  assert.equal(orphanChunk.requestId, null);
  assert.equal(Object.hasOwn(blockedEnd, "durationMs"), false);
  assert.deepEqual(guardReturnsWithRecorder, guardReturnsWithoutRecorder);
  ```
- [x] Add Python tests for truncated/malformed lines, missing instance metadata,
  runtime mismatch, stderr sink diagnostics, and same tool ID in two instances.
  Assert earlier valid events survive; no false complete proof; unfinished calls
  remain visible; native zero duration is preserved when actually present.
- [x] Add runner tests for normal exit, signal exit and deadline, including
  timeout stderr preservation. Assert process exit never implies settlement
  or correctness, and absent settlement is recorded rather than synthesized.
- [x] Run `node --test ladder/ladder/record-pi.test.mjs`; from `ladder/` run
  `uv run python -m pytest tests/test_pi_trace.py tests/test_runner.py -q`.
  Confirm the new cases fail before implementation.
- [x] Extend recorder in place. Emit `instance_start` with observed Pi package
  version/entry path, process execPath and cwd. Allocate UUID per installation,
  never by PID; read runner UUID from `MELLUM_TRACE_RUN_ID`.
  Keep exactly one legacy request/call/result event per original hook firing.
- [x] Add `provider_stream_event`, assistant-only `message_end`,
  `tool_execution_start`, `tool_execution_end`, `agent_start`, `agent_end`,
  `agent_settled`. Preserve optional native durations and full parsed chunks;
  do not add headers/credentials or network export. Keep request counters
  compatible; add instance-local request IDs. Clear active request at message
  completion/settlement, never attach orphan chunks to the previous request.
- [x] Tool association comes from the observed assistant message's native
  call IDs; request/tool links not supported by evidence remain null with
  an explicit ambiguity diagnostic. Never infer cross-instance parentage.
  Sink failure prints a stable `mellum-trace:` diagnostic and never propagates
  a new guard decision or payload modification.
- [x] Implement `load_trace` and `summarize_trace`; `legacy` preserves missing
  evidence as unknown. Integrity checks require instance identity and consistent
  sequence/run IDs; deadline or explicit abort alone does not mean corruption.
  A runtime mismatch or missing expected instance metadata is incomplete evidence.
- [x] Runner supplies one run UUID to the recorder and adds `run.json.telemetry`
  and `run.json.process`: exit code/signal, deadline flag, monotonic elapsed
  time and settlement observation. Keep existing stdout, legacy wall field,
  table and scoring. Read delegated parent lifecycle from existing JSON stdout;
  child lifecycle from the trace. Do not add parent provider requests to the
  Worker's legacy stream. Retain timeout stdout and stderr for diagnostics.
- [x] Verify Node targeted tests, all ladder pytest tests and `npm test`.
  Add the Unreleased description of observational records; review and commit
  as `feat(ladder): correlate Pi telemetry without changing scores`.

## Task 3: Compatibility proof and two smokes, then stop

**Files:** fixtures `tests/fixtures/telemetry/`, `test_score.py`,
`record-pi.test.mjs`, `test_pi_trace.py`, `evals/2026-10-11-smoke-m7c/`,
`evals/PROVENANCE.md`, M.7C research finding, roadmap and this plan.

**Interfaces:** Consume Tasks 1–2 launch/trace functions and metadata.
Use existing `score(...).as_row()`, rung checks and `archive_raw`; add no new CLI.

- [x] Reuse existing A10 rung-1 replay fixture as legacy evidence. Extract one
  short Pi 1.1 event sequence from retained October 11 evidence; preserve its
  identities/ordering and include observed final/settlement data, not the
  parent's final text substituted for a child's response. Record source archive
  hash and exact sanitization in fixture README. No raw experiment dump in Git.
  Store that small sanitized sequence as `pi110.events.json`, not a raw
  `trace.jsonl`; include its source/transformation record in the README.
- [x] Add `test_additive_telemetry_preserves_legacy_score` with exact assertion
  `score(augmented, paths, lines).as_row() == score(legacy, paths, lines).as_row()`.
  Add recorded-sequence replay through recorder hooks, checking normalized
  final versus chunks and instance runtime identity. Do not mutate source records.
- [x] Add deterministic comparison using shipped guard hooks with/without
  recorder installed: same request objects and every guard return value.
  No payload replacement, blocking or continuation added by observers.
- [x] Demonstrate each new regression assertion fails when its pinned behavior
  is broken, restore it, then run `npm test` and from `ladder/`
  `uv run python -m pytest`. Expected: all tests pass with no model calls.
- [x] Obtain an isolated Pi 1.1.0 executable using the existing temporary
  research installation or a pinned temporary install. Verify its package
  identity plus the loaded pi-subagents revision; leave global packages intact.
  Run the existing read-only setup check and inspect measured server/provider
  values. Do not change prompt/sampling/guards to make a smoke succeed.
- [x] Run from `ladder/` with the selected absolute executable substituted for
  `<pi-1.1.0>`: `uv run python -m ladder.run_ladder --pi-executable <pi-1.1.0> --profile baseline --mode mode --rung 1 --repeat 1 --out ../evals/2026-10-11-smoke-m7c`.
  Then run the same command with `--mode delegated --guards`. These are the
  two initial counted attempts; retain the existing 600-second runner deadline.
  Check observed Mellum requests use max_tokens 16,384, thinking on and sampling
  1/0.95/20, plus measured server-only settings. The `baseline` server profile's
  4,096 cap is request-overridden for these hosts, not a new worker setting.
- [x] Inspect launch identities, child identity, complete telemetry, request/
  chunk/call relationships, normalized reply, settlements and runner outcomes.
  Record existing rung checks separately. Inspect any failed attempt before
  rerunning; repeat only after fixing a concrete defect. Stop if a host issue
  requires a new subsystem; document the limitation rather than widening scope.
- [x] Write the short finding with measured/conjecture headers, falsifiers
  and risks. Report the two attempts individually, not a reliability rate or
  Pi-version comparison. `smoke-m7c/README.md` links records and explains how
  each was reconstructed; raw traces remain untracked.
- [x] Review raw contents, archive with existing `ladder.archive_raw`, publish
  reviewed assets to the appropriate `research-YYYY-MM-DD` release, and record
  hashes/URLs in PROVENANCE and smoke README. Verify published bytes against
  hashes. Never upload mirrored auth/config files or silently edit the earlier
  October 11 preservation manifest.
- [x] Run final `npm test`, ladder pytest, docs cap tests and `git diff --check`.
  Reconcile Unreleased with `git log v0.1.6..HEAD --oneline`; update M.7C Status
  and Now, prune only resolved backlog entries. Add dated `## Result`, change
  lifecycle to closed, replace any fence over 15 lines with a shipped reference,
  and move this plan to `plans/archive/` with links adjusted before archiving.
  Review the whole branch, then commit closure as `docs: close M.7C telemetry`.

## Stop rule

Stop once deterministic compatibility checks pass and both smoke attempts
can be reconstructed with reviewed provenance. Honest failed task checks do
not authorize a benchmark campaign. A host blocker is recorded as an incomplete
phase outcome, not marked complete. M.7D/M.7E retain the subsequent work.

## Result

2026-10-11: M.7C implemented verified Pi selection/fixture preflight and
additive research-only instance/request/tool, parsed-stream and lifecycle
telemetry. Shipped prompt, tools, sampling, guards, everyday schema-2 records
and scoring remain unchanged. The inherited ladder virtualenv/PATH leak is
resolved; deadline cleanup and broader scorer work remain later phases.

Deterministic legacy/Pi-1.1 replay and shipped-hook comparison pass; all new
regressions were shown failing before restoration/implementation. Exactly two
initial rung-1 smokes (Mode and Worker) passed task and unchanged-tests checks,
with identified Pi 1.1.0 runtimes, measured request settings and telemetry ok.
No reruns. Reviewed raw evidence was published with a downloaded hash check.
See [finding](../../research/2026-10-11-m7c-pi-harness-telemetry.md) and
[attempts](../../../ladder/smoke-m7c/README.md).

Final verification: 298 Node tests, 178 ladder pytest tests, document caps
and diff checks passed. Final independent branch review: one Important multi-step process/launch finding fixed with four RED→GREEN
regressions; one Minor duplicated-stderr finding deferred. No second review..
M.7D is next to brainstorm; no eval framework or comparative claim ships.
