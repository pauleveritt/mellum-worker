# Local Q4 baseline — thin worker, 2026-11-01

M3 Max (48GB, Metal), llama-server Q4_K_M, context 50k, n=3, medium deadline 1800s.
Measured on `refactor-thin-worker`: the worker is mode + commands only; all remediation is in
remedy units. `easycheck-preseteasy` is the thin worker + `preset:easy` on the easy suite —
the tier confirmation that easy still passes once the remedies are layered back on.

| config | pass | turns (reps) | wall (reps) |
|---|---|---|---|
| bare-easy | 1/3 | 17 11 20 | 0:54 0:21 0:48 |
| bare-medium | 1/3 | 45 76 58 | 5:22 11:07 6:57 |
| easycheck-preseteasy | 3/3 | 62 71 78 | 3:49 4:09 4:22 |
| worker-easy | 2/3 | 35 76 34 | 3:34 3:52 2:02 |
| worker-medium | 0/3 | 69 79 82 | 4:07 5:10 6:42 |
