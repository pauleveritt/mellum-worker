# R.1 step three — the overnight (counted, n = 24 per arm)

Same host and settings as [step two](../2026-11-07-r1-step-two/table.md), with the host card refreshed
(`~/mellum-runs/r1/host-card-overnight.json`, sha256 `65563a8d7df59429…`). 120 sessions, arms
interleaved round-robin, 2026-11-07 to 2026-11-08. Handler arms run as `--arm worker --remedy
<unit>`; the mediated arms add `check/mediated-test`. Runs under `~/mellum-runs/r1/step3`, raw traces
not committed; the rule is "Step three" in the
[preregistration](../../docs/superpowers/research/2026-11-07-r1-preregistration.md).

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| vanilla | 24 | 11.33 | 0 | 4 | 0 | 1 | 21 | 7,842 |
| fg-server | 24 | 11.38 | 2 | 0 | 0 | 0 | 21 | 7,246.5 |
| bounded | 24 | 12.04 | 5 | 0 | 0 | 0 | 22.5 | 7,967.5 |
| mediated+fg-server | 24 | 11.04 | 15 | 7 | 0 | 12 | 47 | 27,028 |
| mediated+bounded | 24 | 11.75 | 18 | 0 | 0 | 20 | 61 | 25,787 |

Means and full passes count every session; budget medians leave out stalled and censored ones.
Per-session records: `<arm>-rNN/run.json`; the generated table is `sessions.md`.

## The rule applied

- **Base.** The bar is +1 mean check or 6 more full passes than Vanilla, with median requests at most 25.2
  and median output tokens at most 9,410. `fg-server`: +0.05 checks, +2 full passes; it fails.
  `bounded`: +0.71 checks, +5 full passes; it fails by one full pass. Both are inside the budget.
  **Base stays Vanilla; `preset:base` stays `[]`.**
- **`preset:easy`.** Base is Vanilla, so both mediated arms are judged against Vanilla. They clear
  quality (+15 and +18 full passes) and fail budget: 47 and 61 median requests against 25.2,
  about 26,000 median output tokens against 9,410. **No mediated arm wins; `preset:easy` is Base, `[]`.**

## Stalls (reported, not a gate)

Vanilla stalled in 4 of 24 sessions; `fg-server` and `bounded` in none. Step one's stall rule (at
least 2 Vanilla stalls, a handler at half or fewer, checks within 1, budget within 20%) would have
let both handlers in on this data. Step three's rule does not gate on stalls. It was fixed before
these runs and stands; the stall result is a lead for the next preregistered run.

With the mediated test on, `fg-server` did not hold: mediated+fg-server stalled in 7 of 24, five on
`tail -f <log>` (r02, r05, r07, r12, r23) and two on `find / -name …` (r09, r15). `bounded`
bounds every call, and mediated+bounded stalled in none.

## The mediated arms' budget (diagnosed)

- 32 of 48 mediated sessions ended on the 64-request or 32,000-token budget. 33 reached 13/13 on the
  hidden grade, and 26 final workspaces pass the mediated test.
- The test is a superset of the oracle. Its extra checks are what sent sessions back most often:
  a page's own `<title>` block, the `app.py` launch with reload, and the project's own tests.
- **A defect in our test, now fixed.** When the model's own server already held the port, `python
  app.py` died at once and the launch check reported an empty log: it raised with log text read
  before the exit. Ten sessions hit it at least once (bounded r01, r06, r08, r11, r17, r23;
  fg-server r12, r18, r21, r24), and r01 spent its turns finding and killing servers. Fixed in
  `eaf48a3d`. Ten sessions cannot carry a median of 61 against a 25.2 limit, so the result stands.
