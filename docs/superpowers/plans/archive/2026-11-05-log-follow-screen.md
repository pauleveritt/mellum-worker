---
phase: LC
feature_cycle: LC.38
lifecycle: closed
---

# Foreground Log-Follow Screen Implementation Plan

> Use superpowers:executing-plans inline; one fresh final implementation review.

**Goal:** Block the measured foreground log follower and screen6 fresh gated tasks.
**Architecture:** One explicit guard unit; shared shell classifier; screen-only recipe.
**Tech Stack:** TypeScript/Node tests, Python/uv collector, Pi/local llama.cpp/Docker.
**Spec:** [Design](../../specs/2026-11-05-log-follow-screen-design.md).

## Global Constraints

- No worker/preset/assertion/feedback/model/sampling/default-comparison change.
- Screen adds only explicit guard/foreground-log-follow; selected names recorded.
- Two repairs;600s task;180s tool;30s check;8h guardian;660s reserve.
- All six retained, no mid-cohort edit/retry, screen_only; raw/publication held.

## Review Focus

- Follow flags in options versus operands/filenames, quoted data, -- boundary.
- Help/version/finite snapshots and detached groups remain allowed.
- Foreground follower after background server is blocked before either executes.
- Shared wrapper extraction preserves foreground-server behavior.
- Screen/default recipes and frozen metadata remain distinct and truthful.

## Task 1: Explicit log-follow guard and frozen screen recipe

**Files:** extensions/mellum-guards.ts; remedies/guard/foreground-log-follow.ts;
tests/mellum-server-guard.test.mjs; tests/remedy-units.test.mjs;
learn/code/harness.py; learn/code/tests/test_harness.py;
scripts/acceptance_overnight.py; learn/code/tests/test_acceptance_overnight.py.
**Consumes:** existing shell scanning/wrappers and guard hook installation.
**Produces:** logFollowGuard:Guard; screen-selected explicit remedy metadata.

- [x] Add failing unit consumer cases for compound detached server + foreground
  follower, -f/-F/--follow/clustered flags/wrappers, finite snapshots/queries,
  option operands/--/quoted data/background groups. Observe RED.
- [x] Extract wrapper normalization as needed, implement tail-follow detection
  and truthful finite-snapshot guidance, install only its tool_call hook/meta.
  Existing server guard regressions remain GREEN.
- [x] Add failing selected-recipe registration test; screen appends new guard,
  comparison retains prior list. Record remedies in shared collection metadata,
  use selected list in actual harness; new protocol. Focused Python GREEN.
- [x] Reproduce current-refusal counting gap RED; recognize old/current guard
  text with instance/call deduplication GREEN. Dated trace corrections for prior
  screens preserve original records/scores.
- [x] Changelog/FIXES and local commit; npm/docs GREEN, one fresh final review
  and material RED/GREEN fix pass if needed. Prepare new qualified image and
  native fake-provider blocked-call probe with immutable source/hash receipt.

## Task 2: Fixed six-task screen and closure

**Files:** ignored runs/; curated evals/; cycle/pathology records as warranted.
**Consumes:** reviewed qualified source/image/protocol and exact selected recipe.
**Produces:** six retained outcomes or integrity abort; independent shutdown.

- [x] Run collector --run-screen unchanged through all6; analyze quality/budgets,
  guard attempts/repair behavior/semantics/unknowns. No promotion.
- [x] Independently verify shutdown/freeze; scan/archive raw locally. Curate,
  update FIXES/changelog, close/archive plan/roadmap, glossary/pathology if new.
  npm/docs GREEN, local evidence commit/checkpoint. No public push/upload.

## Result

2026-11-05: explicit log-follow guard, exact selected-recipe metadata and current
refusal accounting shipped locally. Fresh six-task screen4/6 formally usable;
373 requests/183186 output, both failures retained. G1 edited protected
dependencies and could not be graded; G6 still failed real startup. No follower
attempt occurred; uncounted native control/guard qualification proves only that
fixture's interception and transport. No reliability/default promotion.
Independent88-resource shutdown and125-input freeze clean. Full results, budget,
semantic reservations, source/review and local raw manifest are in
[the evidence](../../../../evals/2026-11-05-log-follow-screen/README.md).
