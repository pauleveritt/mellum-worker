# 0003: Checkpoints are chosen on screens, Medium first, then faulty calls

- **Date:** 2026-11-27
- **Status:** Accepted

## Context

The held-out pair margin picks candidate checkpoints, but it doesn't predict builds: the final tools adapter
had a positive margin and went 0/3 on Medium, while its update-15 checkpoint (best held-out margin, less
trained) went 3/6. Round 2 cut faulty calls on Medium to 3.2 per 100 but passed fewer builds.

## Decision

- Candidates: every checkpoint at an evaluation, ranked by held-out margin; only a positive margin is converted.
- Winner: screened on Easy, Medium and the Python eval with the same llama.cpp build, Q4_K_M, harness preset
  and deadlines as every other model. Judge Medium passes first, then faulty calls per 100.
- A screen of a few runs is a lead, not a rate; a one-build gap at n=6 decides nothing on its own.

## Consequences

Update 15 of the tools tune is Tsunami. A claim that a tune builds more working software needs a
preregistered Medium comparison at n of 10 or more.

## Evidence

Scorecard rows: base Medium 2/3 (6.6 faults/100); final tools 0/3 (9.5); update 15 3/6 (5.3); round 2 2/6 (3.2).
Run folders `runs/2026-11-27-tools15-medium*`, `runs/2026-11-27-tools2-medium`.
