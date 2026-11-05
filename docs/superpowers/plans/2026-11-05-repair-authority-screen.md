---
phase: LC
feature_cycle: LC.37
lifecycle: active
---

# Repair Authority Screen Implementation Plan

> Use superpowers:executing-plans inline; one fresh final implementation review.

**Goal:** Screen authoritative, preservation-aware external repair feedback.
**Architecture:** Change host feedback only; reuse the protected gate and collector.
**Tech Stack:** Python/uv/Pi/temporary Docker/local llama.cpp.
**Spec:** [Design](../specs/2026-11-05-repair-authority-screen-design.md).

## Global Constraints

- Unchanged assertions, worker/remedies/tools/model/backend; no benchmark answers.
- Two repairs;600s task;180s tool;30s check;8h guardian;660s start reserve.
- Feedback8000-character cap; logs untrusted; failed observations preserved.
- Fixed fresh6G, no mid-cohort changes/replacements, screen_only; raw held.

## Review Focus

- Passing requirement observations must not become instructions or bloat feedback.
- Failed diagnostics remain visible when adding passing names near the cap.
- No altered gate limits/state/final authority or protected-package assertions.
- New screen protocol freezes correctly while default40 comparison is unchanged.
- Honest costs/shutdown and semantic limits survive every failure.

## Task 1: Repair feedback and fresh registration

**Files:** learn/code/acceptance.py; learn/code/tests/test_acceptance.py;
scripts/acceptance_overnight.py; learn/code/tests/test_acceptance_overnight.py;
CHANGELOG.md; local FIXES.md.
**Consumes:** Gate.apply(result,snapshot_sha256,final=False)->receipt.
**Produces:** same receipt schema/authority, separate passing-name checklist.

- [ ] Add failing receipt test with generic passing/failing names: failed
  observation retained, passing name listed without its observation; existing
  feedback boundedness/repair-state tests remain. Observe RED.
- [ ] Replace repair guidance with external authority, missing-required-tests and
  preserve-passing text; append passing names after failed observations. No
  suite literals or assertion changes. Focused Python GREEN.
- [ ] Update selected screen protocol path and expected registration test to new
  protocol; default comparison unchanged. Changelog/FIXES and local commit.
- [ ] Full npm/docs GREEN; fresh whole-cycle reviewer, one material RED/GREEN fix
  pass if needed; prepare fresh qualified screen image, verify exact6G/freeze.

## Task 2: Six fresh tasks and closure

**Files:** ignored runs/; curated evals/; cycle/pathology records as warranted.
**Consumes:** reviewed qualified source/image/protocol; same collector --run-screen.
**Produces:** all6 outcomes or explicit integrity abort and independent shutdown.

- [ ] Run fixed6 unchanged; retain every cost/failure. Analyze components,
  trace/repair behavior, semantics and unknown totals, not final-message success.
- [ ] Independently verify shutdown/freeze; scan/archive raw locally. Curate,
  reconcile changelog/FIXES, close/archive plan and roadmap. Existing glossary/
  pathology entries reused unless new concept/shape. npm/docs GREEN, local commit.
- [ ] Further iteration requires a material observed defect; ordinary model
  failure may falsify the hypothesis without licensing a favorable retry.
