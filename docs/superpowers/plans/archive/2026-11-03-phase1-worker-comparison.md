---
phase: LC
feature_cycle: LC.32
cycle: 1
lifecycle: closed
---

# Phase 1 baseline comparison implementation plan

> Use superpowers:executing-plans inline, with one fresh instrument review.

**Goal:** retain six thin Baseline Worker Phase 1 sessions comparable to the
existing Vanilla reference, using the same trusted collector.

**Architecture:** parameterize only arm selection and arm-specific provenance in
baseline.py/harness.py. Shared inputs are checked against the saved reference;
execution, scoring, limits and failure accounting are reused unchanged.

**Tech stack:** existing Python via uv, Pi 1.4.0, recorder, Runpod llama.cpp.
**Spec:** [authorized protocol](../../research/2026-11-03-phase1-worker-comparison.md).
The user approved this scope in chat; no new model/remedy behavior is designed.

## Global constraints

Six sequential Easy Phase 1 worker sessions; recorder plus thin worker only.
Same backend/model/profile/checkers/Pi, 600s deadline, 180s open-call cutoff.
Keep the saved Vanilla record immutable. No prompt, remedy or oracle changes.
Keep raw evidence outside Git. Preserve unknown token totals and failed attempts.

## Review focus

Wrong-arm resume; fake worker activation; reference mismatches silently accepted;
worker source mutation during collection; outcome/scoring changes hidden in the
collector refactor; accidental global worker-record writes.

## Task 1: Arm-aware trusted collector

Consumes existing collector, reference manifest and worker implementation.
Produces arm-aware manifest/identity/reference checks and CLI selection.

- [x] Add failing tests for worker selection/provenance, mode activation, exact
  extension order, wrong-arm resume, shared-input mismatch and reference identity.
  Expected: new cases fail before implementation.
- [x] Add baseline --arm worker --reference PATH; default Vanilla unchanged.
  Validate reference scope/completion/six counted and shared material. Allow only
  reviewed harness/baseline hash changes plus explicit worker arm/source delta.
  Pin supplemental Pi runtime hashes from the retained reference; record launch
  env and keep worker's own mode records private to the run. No score changes.
- [x] Run baseline/runner tests and npm test; docs caps; update docs/changelog/FIXES.
  Expected: complete existing and new checks pass; dry-run shows exact arm.
- [x] Commit/checkpoint; request one fresh review of only this instrument delta.
  Reproduce/fix Important issues test-first; no counted runs before it passes.

## Task 2: Collect, compare and preserve

Consumes verified collector, compatibility report and frozen reference.
Produces six counted worker records and a descriptive Phase 1 comparison.

- [x] Preflight live backend/runtime/shared inputs, qualify Easy both ways, check
  ports/ownership. Print dry-run. Expected: compatible reference; no model call.
- [x] Run visibly under caffeinate. Review ambiguous errors explicitly and count
  model failures/stalls. Expected: six counted worker attempts, no cherry-picking.
- [x] Audit runtime/activation/extensions/settings, grading order and cleanup.
  Compare quality counts and request/elapsed medians; token incompleteness stays
  explicit. Preserve all artifacts/raw evidence with checksums and unique assets.
- [x] Update FIXES/changelog/roadmap, add Result and archive plan. Verify docs caps,
  npm test and docs build as appropriate. Commit/push the compact comparison.

## Result

2026-11-03: collector instrument378217f adds strict worker/reference selection,
native activation/runtime/source provenance and private mode destinations without
changing model, remedies, scoring or limits. One fresh review found one Important
post-execution integrity gap, fixed with a sixth-session drift regression
RED→GREEN; npm635/635 and docs caps passed before collection.

Six worker attempts retained, no exclusions/replacements:5/6 hidden-all-pass,6/6
health,1settled/5stalled,0passing-and-settled. Vanilla:4/6,6/6,2/4,1 respectively.
Worker requests137total/19.5median versus91/15; elapsed1246.636s/224.7755s versus
901.611s/202.0585s. Unknown output totals3worker/2Vanilla; no full token comparison.
All137 worker requests, native clamp, activation and cleanup audited. No default
promoted; existing foreground-server/ineffective-self-check pathologies cover the
observations and no new terminology was introduced. Compact scorecard and raw
evidence provenance: [retained comparison](../../../../evals/2026-11-03-worker-easy/README.md).
