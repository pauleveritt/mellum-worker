# F.6 screen — settle-only + bounded on the held pod (n = 6, a lead)

Same pod, commit, host card, budgets, stall setting and suite files as
[the F.6 batch](../2026-11-08-f6-easy/table.md), run serially straight after it, 2026-11-08 20:57 to
21:16 UTC. `--arm vanilla --remedy tool/bounded-commands,check/mediated-test-settle`
([arms.json](arms.json)); `MELLUM_BOUND_SECONDS` unset, so 30 s. Runs under
`~/mellum-runs/f6/f6-settle-bounded`, raw traces not committed. A screen at n = 6 is a lead, not a
rate. Read in the [note](../../docs/superpowers/research/2026-11-08-f6-held-pod.md).

| Arm | n | Mean checks | Full passes | Stalled | Censored | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|---|---|
| settle-only+bounded | 6 | 12.83 | 5 | 0 | 0 | 0 | 31.50 | 15830 |

## Misses per check

| Check | settle-only+bounded (of 6) |
|---|---|
| test_layout_ends_body_with_bootstrap5_cdn_bundle | 1 |
