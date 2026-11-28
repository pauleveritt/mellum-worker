# Preregistration: mediated vs stock on rungs 6-9

Date: 2026-10-18. Fixed **before** any run of this comparison, per `docs/sdd.md`
("preregistered runs decide"). Follows the [rung-9 screen](2026-10-18-mediated-rung9-screen.md)
(n=1) that moved rung 9 from FAIL to PASS; this run decides whether that holds
across rungs 6-9.

## Question

Does the **mediated** approach (a hand-written failing acceptance test placed and
frozen in the workspace, the task "make it pass" with verify-only/no-servers
guidance, `--redispatch 4`, `--guards`) beat the **stock** worker (writes its own
tests) on AgentClinic rungs 6-9?

## Arms (fixed)

Both arms: real Pi 1.3.0 -> `run_ladder --mode direct --backend mlx-lm --base-url
http://127.0.0.1:11500/v1 --model-id <served path> --guards --profile tuned
--deadline 600`, against the local `mlx_lm.server` (prompt cache on, thinking
forced) serving the 6-bit weights.

- **A — stock:** no `--acceptance-test`. The worker writes its own tests.
- **B — mediated:** `--acceptance-test <phase test> --redispatch 4`, one
  hand-written test per phase, authored from that phase's spec by the main model
  (not the worker), named `test_*.py`. Phase 4's exists (`test_phase4.py`);
  phases 1-3 are owed before arm B can run.

  **Amendment (2026-10-18, before any arm-B run):** a greedy `--redispatch`
  re-runs the same deterministic decode, so the retries added nothing beyond the
  appended failure text. Arm B now runs with the default temperature ramp
  (`--redispatch-temperature-step 0.25` up to `--redispatch-temperature-cap 0.5`,
  seed moving with the attempt and continuing past the cap), so each retry
  explores a new path without going hot — a screen showed a 0→1.0 ramp corrupts
  the worker's JSON tool calls and thrashes the app, so the cap stays low and
  reseeding carries the later retries. Arm A (stock, no `--redispatch`) is
  unaffected and its runs stand. This changes arm B's retry mechanism only; the
  question, n, scoring and decision rule are unchanged.

Arm B differs from A by the whole mediated bundle (placed test + no-servers
guidance + re-dispatch), not the placed test alone — so this decides the
*approach*, not the placed test in isolation.

## n and scope

Rungs **6, 7, 8, 9**, **n = 3** per (rung x arm) = **12 runs per arm, 24 total**.

## Scoring (fixed)

Each run is scored by the ladder's `check_agentclinic`: pass iff the visible
test command passes, the **hidden oracle** passes, existing tests are unedited,
and nothing is written outside the write-list. Primary metric: **pass count /12
per arm**. Secondary (reported, not decisive): wall seconds, requests, whether
the deadline was hit, `redispatch_attempts` (arm B).

## Decision rule (fixed before results)

- **Promote the mediated approach** (to an M.11 Mode-command spec) iff arm B's
  pass count is **strictly greater than** arm A's **and** arm B is **>= 9/12**
  (matching or beating the A21 baseline of 9/12).
- If arm B > arm A but < 9/12: a partial lead; iterate, do not spec yet.
- If arm B <= arm A: the mediated approach does not carry rungs 6-9; record and
  reconsider.

Raw traces (`trace.jsonl`, `stdout.txt`, `diff.patch`) are not committed; they go
to a `research-2026-10-18` release if published. This run is on `mlx_lm.server`,
not oMLX, so its result is a harness finding about the approach; a shipped claim
needs the measured oMLX backend.
