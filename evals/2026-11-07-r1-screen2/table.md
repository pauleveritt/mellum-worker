# R.1 Screen 2 — the step-two units on Base, a lead (n = 3 per arm)

Same host, card and settings as [step one](../2026-11-07-r1-step-one/table.md). Step one left
`preset:base` empty, so Base is Vanilla and each unit runs as `--arm vanilla --remedy <unit>`;
the Vanilla arm is both the anchor and Base. Runs under `~/mellum-runs/r1/screen2`, raw traces not
committed. This screen decides only which units enter step two
([preregistration](../../docs/superpowers/research/2026-11-07-r1-preregistration.md)). It is not a rate.

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| vanilla | 3 | 12.33 | 1 | 0 | 0 | 0 | 26 | 8473 |
| compile-import (`check/compile-import`) | 3 | 9 | 0 | 0 | 0 | 0 | 18 | 6679 |
| mediated-test (`check/mediated-test`) | 3 | 13 | 3 | 1 | 0 | 1 | 39 | 27599 |

## Did the hook act?

- **compile-import:** no `.py` write failed to compile and no written module failed to import in
  any of the three sessions, so it never sent a message. Its 4/13 session (r01) returned the
  rendered page as a plain string, which FastAPI serves as JSON: a model bug the unit cannot see.
- **mediated-test:** the test was shown in every session (it rides on 32–42 requests each); the
  settle check sent the model back in r02. r02 then ended `stalled` on a foreground
  `uv run --offline python app.py`, after its workspace already passed all 13; r03 ended `budget`
  at 32,132 output tokens, also at 13/13.

## Decision (screen filter)

`compile-import` is dropped (2026-11-08 correction: it could not be judged at n = 3): its hook never acted (and it is 3.33 checks below Vanilla, mostly the
one unrelated session). `mediated-test` enters step two, against Vanilla.

A lead, not a finding: the shown test launches the app with `uv run --offline python app.py`, the
command r02 then ran in the foreground.
