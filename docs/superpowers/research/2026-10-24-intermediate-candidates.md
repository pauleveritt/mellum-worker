# Intermediate candidates from PR #1

Date: 2026-10-24. Status: candidate review, not a design.

## What qualifies as Intermediate

A candidate is Intermediate when it is a **workflow or a baseline** built after
Getting Started: it composes the worker, harness, suites or guards into a way of
working. It is not a single remedy, a prompt variant, a UI experiment or a
research record.

## Promoted to the Intermediate area

### INT.1 — Baseline Worker v2

The current Baseline Worker plus the workspace-confinement guard on branch `lc11b-confinement` (`176922f`). It
changes the default worker, so it needs a re-baseline. Status: candidate; the
guard is a draft and the pathological screen is still owed.

### INT.2 — Flow/examine

The orchestrator, examiner, frozen phase gates, cumulative scoring and
best-of-N. It is a separate architecture and a separate baseline, not a change
to `/mellum`. Status: candidate; needs a spec and a hard llama.cpp run with a
hidden pass.

## Reviewed, not promoted

| Part | Disposition | Why |
| --- | --- | --- |
| Mediated ladder: acceptance test, re-dispatch, effort ramp | Fold into INT.2 | The Flow examiner/gates are the later form; standalone ladder mediation is measurement scaffolding. |
| Tier-1 contract test (`2ca1e22`) | Fold into INT.2 | Shallow structural test; the examiner is the deep gate. |
| `mellum-knowledge` / docs lookup | INT.2 dependency | The examiner uses `lookup`; do not ship it as a separate lesson. |
| `mellum-plan`, `mellum-loop` | Dropped from this extraction | Flow supersedes the external plan/review loop. |
| `mellum-surgical`, `mellum-nonblock` | Defer as guard candidates | They protect writes/blocks; each needs its own pathology screen, like confinement. |
| `mellum-quality`, `mellum-verify` | Defer | Finish/next-concept checks; not required by Flow and not measured on the suites. |
| `mellum-context`, `mellum-rethink`, `mellum-files`, `mellum-vision` | Defer / advanced | Single tools, not an intermediate workflow. |
| Dashboard, feed, replay, pause | Defer / advanced | Operator UI, not a worker baseline. |
| Prompt v8–v11 | Not Intermediate | Test-driven ladder prompt; see the prompt triage. |
| Rungs 10–12 | Evidence, not a phase | Ladder records for the findings track. |

## Rule

Only a workflow or a baseline becomes an INT phase. Everything else stays a
guard candidate, a Flow dependency, a lesson, or a rejected experiment.
