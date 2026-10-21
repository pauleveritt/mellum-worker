# Rung 9 ablation — pass rate and wall time (n=3)

| arm | change from the win | pass/n | avg wall | re-dispatches |
|---|---|---|---|---|
| win (baseline) | — (all four v7 changes) | 3/3 | 272s | 2 |
| A — v6 prompt | v6 worker prompt | 3/3 | 701s | 2–3 |
| B — whole-dir | `pytest tests` | 3/3 | 3075s | 2 |
| C — grep/find | grep/find back in tools | 3/3 | 348s | 2–3 |
| **D — fixed-high** | no ramp, `--thinking high` | **3/3** | **163s** | **0** |

Baseline reused from `docs/ladder/2026-10-20-mediated-6-9-v7/` (rung 9).
No arm fell below 3/3 → no change is load-bearing for the crack; the differences
are cost. Fixed-high passes first-try and fastest.
