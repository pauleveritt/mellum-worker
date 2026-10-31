# Agent-decided flow vs forced flow — design and preregistration

Date: 2026-10-25. Status: design + preregistration, no result yet. A prototype
and the run that will decide whether it replaces the forced flow as a default.

## What is measured (so far)

Nothing yet. This note fixes the arms, n, scoring and rule BEFORE the run, so
the comparison is a decision, not a story told after.

## What is conjecture

The current flow (`extensions/mellum-flow.ts`) forces a fixed six-step pipeline —
`plan → review_plan → examine → code → review_code → test` — as discrete tools
the orchestrator must call in order. Conjecture: **the load-bearing part is the
frozen external oracle, not the prescribed step sequence.** Forcing all six
steps on every task is slow (6+ model calls per task) and the forced separate
examiner is where this session's brittleness came from (redirect-following,
dangling fence, substring collision, destructive reseed, mis-counted delta). A
flow that enforces only the invariants and lets the agent choose its own steps
should be at least as capable and faster, with less gate brittleness.

## The two arms

- **forced** (control): today's flow. Orchestrator calls the six phase tools in
  the prescribed order; the examiner writes the gate; `code` builds to pass it.
- **free** (prototype): the harness enforces only two invariants and lets the
  agent decide everything between them —
  1. **An external, frozen acceptance test exists** before any build — one
     `examine` pass writes it, the harness freezes it, and the agent cannot edit
     or weaken it (freeze-the-oracle).
  2. **Exit is verified, never self-declared** — "done" means the harness
     re-runs the frozen test and it passes; on failure the agent is re-dispatched
     on the same workspace (bounded), exactly like the ladder's mediated
     `--acceptance-test` + `--redispatch`.
  Between those the agent has ordinary coding tools (`read/edit/bash/write/
  lookup/test`) and drives itself — plan, code, test, iterate — as it judges,
  with no forced step order.

This is the M.11 "mediated acceptance test" direction (see `AGENTS.md` "don't
trust the worker's self-exit" and the exit-gate note), brought into the flow.

## Why the forced flow exists (so we don't lose the reason)

The measured problem: this FIXED small model, left to drive itself, under-
structures and declares done on incomplete self-authored tests. The forced flow
guarantees it plans and writes a gate. The **free** arm keeps that guarantee
(the frozen oracle + verified exit) while dropping the rigid step order — so it
should not reintroduce the self-exit failure.

## Preregistration (the deciding run)

- **Suites / rungs:** the hard suite end-to-end (7 phases) and ladder rungs 6-12
  (the AgentClinic phases), both arms, same fixed model (Mellum 2.1 6-bit via
  oMLX), same guards.
- **n:** 3 sessions per arm per target (screens first; this is the deciding run,
  so n>1).
- **Scoring:** the hidden grader (`score_workspace` / the rung `_hidden_pN`), the
  real oracle — never the examiner's own gate. Report pass-rate and wall-clock.
- **Decision rule:** adopt **free** as the default only if its hidden pass-rate
  is >= forced's AND it is faster (fewer model calls / less wall-clock), with no
  new self-exit regressions. If it passes less, keep forced; record the loss.
- **Everything through `uv run`; the live watcher visible per skill section 9.**

## What would falsify / risks

- **Falsified** if free's hidden pass-rate drops below forced — the step
  scaffolding was doing real work for this model, not just the oracle.
- **Self-exit risk:** without forced steps the agent may stop early; the
  verified-exit invariant must prevent it. Watch for runs that "finish" with the
  frozen test still failing.
- **Who writes the gate:** `examine` still authors it, so the examiner
  brittleness could persist in the free arm; the harness guarantees
  (fixture restore, per-phase scoring, schema injection, git checkpoints) stay
  in force for both arms.
- n=3 is a screen-plus, not a rate; a default change still wants a ladder record
  under `evals/`.
