# Session progress — 2026-10-18

A progress snapshot for reporting: what is validated, the mechanisms shipped
this session, the finished stock baseline, and what is still open.

## Validated (evidence in hand)

1. **Harness green, test-first** — 316 node + 206 ladder tests.
2. **Mellum drives Pi's agent loop natively** — emits JSON tool calls, edits
   files, passes rungs on real `pi -p`. Observed live; the core viability fact.
3. **Mediated test (M.11) works end-to-end on real Pi** — mediated rung-9 PASS
   (one worker, converged first attempt, hidden oracle green) vs stock rung-9
   FAIL. Recorded as an n=1 lead (5cb550f).
4. **Freeze-the-oracle validated without full runs** — phase 1-3 mediated tests
   pass 9/9 against the golden fixture; the rung 6 + 9 mediated tests were
   confirmed **supersets of the ladder's hidden oracle** (7/7 against the
   complete `agentclinic-done` implementation).
5. **Pi is a tool-call-format gate, not a size gate** — a model works on Pi iff
   it emits JSON tool calls; code-block models need an adapter, regardless of
   size.

## Shipped this session (new mechanisms)

- **Temperature-grown + seeded re-dispatch** (aa5f6f3) — retries ramp the
  temperature 0 -> 0.2 -> ... -> 1.0 and move the seed, so a retry explores a new
  path instead of re-running the same greedy decode.
- **Re-dispatch on a timed-out attempt** (107b480) — a timeout is still a failing
  frozen test, so it re-dispatches a fresh worker rather than aborting the loop.
- **Small deadline slicing** (operating technique) — one long attempt becomes a
  relay of short, fresh-context, escalating-temperature workers on one
  cumulative workspace; bounded cost `<= (N+1) x deadline`. Fights both stuck
  trajectories and context bloat (each slice drops the accumulated transcript).
- **"Complete"-check recipe** in the mellum-dev skill §6 (543b717) — a mediated
  acceptance test must be a superset of the hidden oracle and dry-run green on
  `agentclinic-done` / red on the known failure mode.

## Stock baseline (preregistered, finished)

Stock arm A, rungs 6-9, n=3, on `mlx_lm.server`:

| rung | result |
|------|--------|
| 6 | 1/3 |
| 7 | 3/3 |
| 8 | 1/3 |
| 9 | 0/3 |
| total | 5/12 |

Rung 9 at 0/3 is the historical wall (the Phase 4 auto-`id` miss). Rungs 6/8
dropped to deadline hits — a slow-backend artifact, not a capability drop (one
rung-6 run built a correct app and was cut off before writing its tests). The
past best, A21 on oMLX, was 9/12 (rungs 6-8 perfect, rung 9 0/3), 0 deadline
hits.

## In flight / open

- **oMLX is not installed on this machine** (no app, binary, or package), so the
  apples-to-apples comparison against A21's 9/12 is blocked until an oMLX server
  is up on :8001.
- **Mediated demo (rung 6 + 9)** with small deadline slicing was run on
  `mlx_lm.server`; the re-dispatch temperature ramp was confirmed firing live
  (slice 1 relaunched at temperature 0.2, seed 43, on the accumulating
  workspace).
- The **preregistered mediated arm B** (amended to use the ramp) is still owed on
  a fast backend to decide promotion against the 9/12 rule.

## Concept proposed (not built)

**Orchestrator + small-coder split** — Mellum tool-calls and orchestrates; a
small model writes code via a `write_code` tool and Mellum writes the result.
An appealing cost play; the risk is handoff overhead and dropped cross-cutting
requirements. Backlog candidate, gated by a frozen acceptance test.
