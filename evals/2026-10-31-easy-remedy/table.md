# easy — nonblock + phase-scoped nav-complete acceptance + ncm (local M3 Q4)

| rep | result | miss | turns | tool_calls | wall | run |
|---|---|---|---|---|---|---|
| easy-r0 | PASS | 0 | 99 | 97 | 539s | run1 |
| easy-r1 | PASS | 0 | 20 | 19 | 67s | run1 |
| easy-r2 | PASS | 0 | 19 | 18 | 77s | run1 |
| easy-r3 | PASS | 0 | 19 | 18 | 79s | run2(confirm) |
| easy-r4 | PASS | 0 | 18 | 17 | 58s | run2(confirm) |
| easy-r5 | PASS | 0 | 17 | 16 | 76s | run2(confirm) |

**6/6** across two independent n=3 runs. Bare baseline on the same rig: 1/3 (`evals/baseline/2026-10-30-vanilla-local-m3-q4`).
