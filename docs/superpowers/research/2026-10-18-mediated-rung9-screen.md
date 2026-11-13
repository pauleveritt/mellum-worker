# Mediated rung-9 screen: an external frozen test moved rung 9 from FAIL to PASS

Date: 2026-10-18. A design input for M.11 (the mediated test). A screen, n = 1,
not a preregistered run. Run on real Pi 1.3.0 via `run_ladder --mode direct
--backend mlx-lm` against a local `mlx_lm.server` (prompt cache on, thinking
forced) serving the 6-bit Mellum weights — **not oMLX**, so numbers here are a
lead about the mechanism, not a measured rate and not a claim about the shipped
worker.

## What is measured

Two scored rung-9 runs (AgentClinic Phase 4) through the real harness, n = 1 each:

| rung 9, real Pi + `run_ladder` | result | turns | wall | note |
| --- | --- | --- | --- | --- |
| **stock** (no acceptance test; the worker writes its own) | **FAIL** | 44 | 600 s (deadline) | the id-miss class; ran out of budget |
| **mediated** (`--acceptance-test test_phase4.py --redispatch 4 --guards`) | **PASS** | 20 | 194 s | converged in **one attempt**; no re-dispatch fired |

The mediated run's scored `pass` is load-bearing: the ladder's `check_agentclinic`
returns pass only when the visible tests **and** the hidden oracle pass, existing
tests are unedited, and nothing is written outside the write-list. So **the hidden
oracle the worker never saw is green**, with the frozen acceptance test unedited.
The worker implemented a distinct/stable auto `id` + `status` in `models.py`,
resolve/reopen 303 routes in `app.py`, and the "Resolved" badge in the template,
then verified with the test command and stopped.

Two supporting facts:
- **Golden-solution check (model-free):** a hand-written correct Phase-4 solution
  passes both the acceptance test and the hidden oracle in ~0.5 s, so the oracle
  is satisfiable and self-consistent — a FAIL is the model's doing, not an
  impossible target. The re-dispatch loop and placement are covered by fast unit
  tests with a fake worker. So the pipeline was validated before spending model
  time (see [the exit-gate note](2026-10-18-harness-exit-gate.md)).
- **Two harness bugs were found and fixed on the way**, both mine, not the model:
  the acceptance test must be named `test_*.py` or `pytest tests` never collects
  it (the worker thrashed renaming it); and an unguided worker hung its whole
  deadline on `python app.py` (a blocking server). The mediated task now tells
  the worker to verify only with the test command and not start servers.

## What is conjecture

- That the PASS reproduces (n = 1).
- **Attribution.** The mediated run differs from stock by more than "a test was
  placed": it also had the no-servers task guidance and an available (unused)
  re-dispatch budget, and ran on the tuned prompt-cached server. So this is a
  lead for the mediated *approach* (external frozen oracle + guardrails), not for
  the placed test in isolation.
- That it transfers to oMLX, to rungs 6-8, or to a preregistered rungs 6-9 run
  against A21 (9/12).

## What would falsify this

- A preregistered rungs 6-9 run (n >= 3 per arm) where mediated does not beat
  stock, or where the rung-9 PASS does not reproduce.
- A trace showing the PASS came from the worker weakening or evading the frozen
  test (it did not here: `tests_unchanged` true, write-list clean).

## Risks

- n = 1, a screen, confounded (mediated test vs no-servers guidance vs
  re-dispatch vs the tuned server) — do not cite as a rate.
- The server is `mlx_lm.server`, not the measured oMLX; a shipped claim needs the
  measured backend.
- The no-servers line in the task edges toward coaching the worker; M.11 cautions
  against the main model solving the task. Keep such guidance to generic domain
  rules (how to verify), never task-specific hints.

## What follows

Per the M.11 row, a moved rung-9 screen is what makes the preregistered rungs 6-9
run and then the Mode-command spec owed. The freeze-the-oracle guard and the
worker bash-timeout ("Execution bounds") remain their own BACKLOG items.

## Effort

2026-10-18: **~3.2 h active** (21 commits, 16:44–19:50) within a **~5.4 h
session** (clone ~14:24 → ~19:50; the difference is exploration, model runs and
waits, not hands-on). Span measured from git commit timestamps, not a timer.
That span covers the whole day's work this note caps: the mlx-lm backend +
`--model-id` + sampling flags, the exit-gate SDD records, the `mellum-dev` skill
+ CI + `EXAMPLE.md`, and the mediated-test path (`--acceptance-test`,
`--redispatch`, the pytest-collectable-name and no-servers fixes) ending in this
screen.
