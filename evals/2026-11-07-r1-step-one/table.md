# R.1 step one — earning Base against plain Vanilla (counted, n = 12 per arm)

Easy (13 current checks), M5 Max, llama.cpp b12110 on :8001, Pi 1.4.0, thinking on, counted with
the host card that passed all seven items (`~/mellum-runs/r1/host-card.json`), `--grade --stall 180`,
Easy's budget (64 requests / 32,000 output tokens, `wall_safety` 1,200 s). Interleaved
round-robin by `scripts/r1_batch.py` at `r1-easy-remedies` `fa4ea31`; runs under
`~/mellum-runs/r1/step1`, raw traces not committed. Arms, rule and grader identity were fixed
before the first session in the [preregistration](../../docs/superpowers/research/2026-11-07-r1-preregistration.md).

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| vanilla (`--arm vanilla`) | 12 | 10.58 | 0 | 1 | 0 | 0 | 16 | 6285 |
| bounded (`tool/bounded-commands`) | 12 | 10.83 | 1 | 0 | 0 | 1 | 20.5 | 7686.5 |
| fg-server (`guard/foreground-server`) | 12 | 12.00 | 3 | 0 | 0 | 0 | 19 | 6817.5 |
| layout (`prompt/name-the-layout`) | 12 | 9.50 | 0 | 2 | 0 | 0 | 16.5 | 6026 |

Candidate arms are `--arm worker --remedy <unit>`. Means and full passes count every session as
graded; budget medians leave out stalled and censored sessions. Per-session records:
`<arm>-rNN/run.json`; the generated table is `sessions.md`.

## The hooks acted

- bounded: bash calls given the 30 s bound, per session: 9, 12, 6, 3, 9, 5, 3, 6, 6, 8, 11, 41.
- fg-server: foreground starts refused in 4 of 12 sessions (2, 8, 19, 2); two of its three full
  passes (r03, r04) are among them.
- layout: the injected line rode on every request of every session.

## The rule applied

- **Stall handlers** need Vanilla to stall or be censored in at least 2 of 12. Vanilla did in 1
  (r09, a foreground server), so neither `bounded` nor `fg-server` can win. `bounded` would also
  fail the budget limit: 20.5 median requests against 16 × 1.2 = 19.2.
- **`name-the-layout`** needs a mean at least 1 above Vanilla's or 3 more full passes: it is 1.08
  below, with none. It loses.
- **Base is Vanilla**; `preset:base` is empty. Step two runs on the floor.

## Not decided here (a lead)

`fg-server` was judged only on the stall rule, as preregistered. On the quality rule it would
have passed: +1.42 mean checks, 3 full passes against none, 19 median requests (limit 19.2),
6,818 median output tokens (limit 7,542). That is a lead for its own preregistered test, not a
result of this batch.
