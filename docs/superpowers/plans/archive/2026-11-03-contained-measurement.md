---
phase: LC
feature_cycle: LC.33
cycle: 1
lifecycle: closed
---

# Contained measurement implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation and one fresh final review.

**Goal:** Protect the Mac and sibling attempts while diagnosing transport and prompt-budget failures.

**Architecture:** Keep host orchestration; run Pi/tools and grading in separate
networkless containers. Relay inference over exec pipes. Add passive native
transport observation and correct context accounting.

**Tech stack:** Python, Node diagnostics channels, Docker Desktop, existing uv/Pi harness.

**Spec:** [contained measurement](../specs/2026-11-03-contained-measurement-design.md).

## Global constraints

- No counted runs, model/remedy/grader changes or historical record rewrites.
- Pi 1.4.0, Node 24.22.1, Python 3.14.2, uv 0.11.6; image content-addressed.
- No host mounts/network/Docker socket; grading is contained too.
- No retries or model-payload changes; diagnostics redact sensitive material.
- Native educational runs are unconfined; trusted collection fails closed.

## Review focus

- Malicious output paths/links must never escape host extraction.
- Killing a CLI or host runner must not leave an unowned live container.
- Agent-controlled environment/config must not expose host credentials.
- Body truncation and pre-header failure need distinct retained boundaries.
- Missing/cache usage must not become fabricated complete budget totals.

## Task 1: Prompt accounting and passive client diagnostics

Files: `learn/code/harness.py`, `extensions/mellum-recorder.ts`, new
`extensions/lib/transport-observer.mjs`, corresponding Python and Node tests.

Interfaces: `context_usage(rows)` returns full/uncached maxima; observer
`installTransportObserver({write, requestId})` returns an unsubscribe function.

- [x] Add failing cached/raw/missing/error usage regressions and diagnostic
  refusal/header/trailer/error/redaction/noninterference tests; observe RED.
- [x] Implement conservative accounting and passive Undici channels, with
  per-request identity and visible sink failures; preserve output accounting.
- [x] Run targeted tests; update changelog/FIXES and commit/push this fix.

## Task 2: Contained execution and inference relay

Files: new `learn/code/containment.py`, `scripts/containment/` image/relay/export
utilities; new `learn/code/tests/test_containment.py` and Node relay tests.

Interfaces: runtime inspect/build pins image; attempt create/execute/export/remove
owns exact container IDs. A checker runner executes only in a grading container.

- [x] Add failing policy, safe extraction, route restriction, streaming and
  ownership regressions; observe RED before implementations.
- [x] Build image without hidden graders; implement non-root/networkless
  execution, bounded exports and relay over exec pipes. Restrict routes to
  inference; preserve bytes and retain upstream boundaries/correlation IDs.
- [x] Prove edits, subprocesses, private loopback, fake SSE and grading; inject
  refusal/reset/truncation. Verify no real inference and no native fallback.
- [x] Update changelog/FIXES and commit/push the contained runner.

## Task 3: Harness integration and qualification gate

Files: `learn/code/harness.py`, `learn/code/baseline.py`, existing tests, new
qualification command/docs and compact qualification results.

Interfaces: explicit image on safe runs; baseline requires exact policy/image
qualification, freezes it in material and rejects native references/resume drift.

- [x] Add failing collector fail-closed, reference/resume drift, contained
  grading and exact-owned-container recovery regressions; observe RED.
- [x] Integrate execution/graders and image/runtime provenance; preserve old
  native educational behavior with explicit unconfined provenance.
- [x] Run real host/sibling sentinel qualification and interrupted recovery on
  this Mac. Retain compact evidence; failure blocks counted collection.
- [x] Run targeted tests, full npm suite, docs caps and site build. Obtain a
  fresh whole-change review, fix material findings with RED/GREEN tests, update
  roadmap/glossary/pathologies/changelog/FIXES, close/archive and commit/push.

## Execution record

User requested implementation after the forensic findings. Native execution in
this session; existing `paul/initial-fixes` branch retained to preserve the
ongoing setup work and local user-owned FIXES. Design choices are the
implementer's; Docker runner is new measurement infrastructure, not a remedy.


## Result

2026-11-03: instrumentation shipped in `7e9f3da`; contained execution and
collector gate shipped with this closing record. All 25 real fake-provider
checks passed; both arm launches passed the collector identity check. No
counted inference or new comparison was collected. The Runpod Pod was stopped.
[Qualification, review findings and limits](../../research/2026-11-03-contained-measurement.md).

Ruling: keep the observer self-contained in the recorder — run-local recorder
copies must work without another dependency. Ruling: combine tasks 2 and 3 in
one atomic fix — containment is usable only with its collector gate and
qualification. Ruling: use bounded tmpfs-backed named volumes — direct tmpfs
cannot be exported paused. Recovery removes both uniquely labeled resources.

Fresh final review's four material findings received failing-first fixes:
host watchdog, exported-control trust, late relay frames and duplicate usage IDs.
The internal `grade_run=False` health-check mismatch is deferred and documented.
Verification: npm test 640/640, targeted Python harness/collector/containment
162/162 followed by the expanded containment suite16/16, Ruff F/E9 clean;
document caps and site build checked at close. Historical evidence is unchanged.
