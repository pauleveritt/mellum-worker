---
phase: LC
feature_cycle: LC.35
lifecycle: active
---

# Actionable Acceptance Feedback Implementation Plan

> Use superpowers:executing-plans inline, task by task.

**Goal:** Deliver missing launch evidence and an agnostic repair scope contract,
then measure a fresh fixed comparison without weakening acceptance.
**Architecture:** Bounded candidate observations remain untrusted; host assertions
and limits are unchanged. The existing guardian owns inference and shutdown.
**Tech Stack:** Python3.14/uv, Pi1.4.0, local pinned llama.cpp, temporary Docker.
**Spec:** [Design](../specs/2026-11-05-actionable-acceptance-design.md).

## Global Constraints

- No worker/preset/model/tool/sampling changes, hidden feedback or uploads.
- Two repairs;600s task;30s check;180s open-tool; independent8h watchdog.
- Probe reads at most4096 log bytes; host feedback at most350 sanitized chars.
- Fixed20 tasks/arm, fresh S,G alternation;18/20 and budget rule unchanged.
- New tests RED first; preserve all failures and unknown budgets.

## Review Focus

- Candidate logs never become receipt authority or instructions.
- Flooded, malformed and control-character logs remain bounded.
- Exit status is observed before cleanup changes it; valid readiness unchanged.
- Repair instruction stays agnostic and does not permit changing the oracle.
- New protocol is frozen and owned inference stops after the whole cohort.

## Task 1: Diagnostic and repair feedback

**Files:** scripts/containment/probe.py; learn/code/acceptance/easy-phase1/
checker.py and manifest.json; learn/code/acceptance.py; corresponding tests.
**Consumes:** existing fixed startup operation and failed requirement map.
**Produces:** bounded log_tail/launch_exit_code data and agnostic repair feedback.

- [ ] Add failing process-backed probe tests for exit warning, bounded read and
  successful-process cleanup; checker tests for warning delivery, sanitization,
  malformed/hostile logs and unchanged failing authority.
- [ ] Observe RED with focused pytest, implement the smallest changes, observe
  GREEN and refresh the declared checker hash.
- [ ] Add failing Gate regression for current-task cleanup/revert instructions,
  no hidden/successful-check feedback, max8000 and unchanged two-repair limit.
- [ ] Implement the agnostic instruction; verify GREEN; update changelog/FIXES
  and commit locally.

## Task 2: Qualification, registration and fresh review

**Files:** scripts/acceptance_overnight.py; research/2026-11-05-actionable-
acceptance-protocol.md; local qualification records.
**Consumes:** Task1 feedback changes.
**Produces:** frozen qualified image/package, original20/arm order and new protocol.

- [ ] Freeze the dated follow-up protocol as an additional input; assert it is
  included in prepared registration. No collector limits or order change.
- [ ] Build and qualify valid variants, mutations, hostile observations, native
  gate exchanges and compaction. Check real failing startup observation includes
  the runtime warning and stays rejected.
- [ ] Run focused Python/npm/docs; request one fresh whole-change review.
  Fix material findings with RED/GREEN; no speculative polish pass.
- [ ] Commit and prepare the final source/image before starting inference.

## Task 3: Fixed comparison and closure

**Files:** ignored runs/; curated evals/; roadmap/changelog/glossary/pathologies.
**Consumes:** passing qualification/review and frozen protocol.
**Produces:** complete40 or explicitly incomplete outcome, verified shutdown.

- [ ] Run the fresh alternating20/arm cohort unchanged to completion.
- [ ] Report quality, budgets, repairs, semantic/typing limits and candidate rule;
  unknown output stays unknown. No reuse of prior outcomes.
- [ ] Independently verify shutdown and source freeze; package/scan raw locally.
- [ ] Update FIXES and cycle state; close/archive this plan, reconcile changelog,
  pass npm/docs checks and commit locally. If still below trust, diagnose before
  a separately registered next iteration; do not change this cohort.
