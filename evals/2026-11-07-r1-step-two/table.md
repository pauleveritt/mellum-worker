# R.1 step two — the mediated test on Base (counted, n = 12 per arm)

Same host, card and settings as [step one](../2026-11-07-r1-step-one/table.md). Step one left Base
as Vanilla, so the Vanilla arm is both the anchor and Base, and the unit runs as
`--arm vanilla --remedy check/mediated-test`. `check/compile-import` was dropped by
[Screen 2](../2026-11-07-r1-screen2/table.md). Runs under `~/mellum-runs/r1/step2`, raw traces not
committed; rule in the [preregistration](../../docs/superpowers/research/2026-11-07-r1-preregistration.md).

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| vanilla (= Base) | 12 | 10.67 | 0 | 2 | 0 | 0 | 15.5 | 6683 |
| mediated-test | 12 | 10.33 | 4 | 10 | 0 | 1 | 29.5 | 21505 |

Means and full passes count every session as graded; budget medians leave out stalled and
censored sessions, which for `mediated-test` leaves two (r02, 22 requests; r08, a `budget` ending
at 37). Per-session records: `<arm>-rNN/run.json`; the generated table is `sessions.md`.

## The rule applied

- Quality: 4 more full passes than Base clears the bar (3 out of 12); mean checks, 0.33 lower,
  does not.
- Budget: 29.5 median requests against 15.5 × 1.2 = 18.6, and 21,505 median output tokens
  against 8,020. It fails.
- **The mediated test loses on Base.** `preset:easy` is decided by step three, preregistered after
  this result.

## The stalls (a lead, not a result)

Ten of its twelve sessions stalled, against two for Vanilla. The ones read ended on a foreground
`uv run python app.py` or `uvicorn app:app --reload` (r01, r03), and one on `find / -name …`
looking for the `app` module before it existed (r06). Several had already passed all 13 checks
when they stalled (r09, r10, r12). The shown test launches the app with
`uv run --offline python app.py` and opens with `import app`: showing it may steer the model into
both. Step three pairs the unit with each stall handler.
