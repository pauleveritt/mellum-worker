# R.1 Screen 1 — stall handlers and the layout fragment, a lead (n = 3 per arm)

Easy (13 current checks), M5 Max, llama.cpp b12110 on :8001, Pi 1.4.0, thinking on, counted
(`--host-card`, card passed all seven items), `--grade --stall 180`, Easy's budget (64 requests /
32,000 output tokens). Interleaved round-robin by `scripts/r1_batch.py` at `r1-easy-remedies`
`fa4ea31`; runs under `~/mellum-runs/r1/screen1`, raw traces not committed. This screen decides
only which candidates enter step one ([preregistration](../../docs/superpowers/research/2026-11-07-r1-preregistration.md)).
It is not a rate.

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| vanilla | 3 | 4 | 0 | 2 | 0 | 0 | 24 | 10791 |
| bounded (`tool/bounded-commands`) | 3 | 12 | 0 | 0 | 0 | 0 | 16 | 5708 |
| fg-server (`guard/foreground-server`) | 3 | 11.33 | 0 | 0 | 0 | 0 | 25 | 6642 |
| log-follow (`guard/foreground-log-follow`) | 3 | 7.67 | 0 | 0 | 0 | 0 | 20 | 6168 |
| layout (`prompt/name-the-layout`) | 3 | 7.67 | 0 | 1 | 0 | 1 | 27.5 | 18889 |

Candidate arms are `--arm worker --remedy <unit>`; budget medians leave out stalled and censored
sessions. Per-session records: `<arm>-r0k/run.json`; the generated table is `sessions.md`.

## Did the hook act?

| Arm | r01 | r02 | r03 |
|---|---|---|---|
| bounded: bash calls given the 30 s bound | 7 | 5 | 11 |
| fg-server: foreground starts refused | 0 | 5 | 0 |
| log-follow: foreground follows refused | 0 | 0 | 0 |
| layout: requests carrying the injected line | 65 | 13 | 16 |

## Notes on single sessions

- **vanilla-r02** stalled on a foreground `uvicorn app:app --reload` and failed all 13;
  **vanilla-r03** stalled after 8 requests with no gradable app.
- **log-follow-r01** ended `error`: the model's thinking degenerated into a run of backticks to
  the 16,384-token request cap (`stopReason: length`), and `app.py` was left with a quote-pairing
  `SyntaxError` (`""""`), so no check could run. Its guard never fired.
- **layout-r01** ended `budget` at 32,241 output tokens, 11 of 13; **layout-r02** stalled.

## Decision (screen filter)

`log-follow` is dropped: its hook never acted in three sessions (2026-11-08 correction: it could not be judged at n = 3; it was left out of the next batch, not shown worthless). `bounded`, `fg-server` and
`layout` enter step one; each acted, and none is 2 or more checks below Vanilla.
