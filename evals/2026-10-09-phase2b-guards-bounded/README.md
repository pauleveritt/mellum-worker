# Phase 2b: the bounded nudge

Date: 2026-10-08. Phase 1d's settings (direct mode, greedy, request cap
16,384, presence penalty 0.5, prompt v3 appended under Pi's base prompt)
with the guard extension's configuration overridden through
`MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}'`: the
empty-final nudge may fire three times per run instead of once, and the
loop breaker is live (it refuses the sixth identical tool call in a window
of twenty). The override is recorded in each `run.json` as `guards_env`.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase2b-guards-bounded
```

## Result

| rung | 1d (nudge cap 1) | 2b (nudge cap 3 + loop breaker) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 2/3 | 3/3 |
| 5 | 3/3 | 3/3 |
| total | 14/15 | **15/15** |

| measure (15 runs) | 1d | 2b |
| --- | --- | --- |
| nudges fired (runs) | 1 (1) | 7 (6) |
| nudges fired with the tests not yet green | 1 | 7 |
| runs green after their last nudge | 0 of 1 | 6 of 6 |
| second nudge in one run | — | 1 (rung 3 r1) |
| loop-breaker refusals | — | 0 |
| empty final text | 1 | 0 |
| requests per run, mean / max | 13.1 / 20 | 16.5 / 36 |
| tool errors | 11 | 26 (anchor failures 3; two whole-file `write`s to existing files, neither shrinking) |
| wall seconds per run, mean (untrusted) | 51 | 62 |

## Reading

**Every nudge was needed and every nudged run finished green.** Seven
empty turns in six runs, all before the tests passed; one run needed two
nudges; none needed three. The worst run (rung 5 r3) took 36 requests and
9 tool errors but ended with the tests passing and a 606-character report.
The loop breaker never had to refuse anything. The thrash phase 2 saw (31
requests under one nudge, sampled) did not recur under greedy decoding.

**The empty turn is now handled, not fixed.** It happened in six of
fifteen runs here versus one of fifteen in 1d under the same settings,
which says the rate is noisy across days, not that the cap changed the
model. What the cap changes is the outcome: with one nudge, 1d's rung 4 r3
died on its second empty turn; here rung 3 r1 had two and finished.

**Cost of the bound.** A run can now spend up to three extra requests on
nudges and keep going; with the loop breaker live and the deadline, a
pathological run is bounded by the deadline, not by the nudge count. The
mean request count rose 25% over 1d, almost all of it in the two rung 5
runs that worked through tool errors.

The configuration becomes the guard extension's default (`ENABLED`), and
the reference for the lean-down ablation.

## Caveats

Three repeats; greedy decoding that is not bit-reproducible on this
server; the nudge count difference between 1d and 2b (1 vs 7) under
identical settings is itself a measure of day-to-day variance.

Raw traces, stdout and diffs: [`phase2b-guards-bounded.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase2b-guards-bounded.tar.gz).
