# Rung 9: shipped Mode vs direct+mediated

| config | rung 9 | wall | turns |
|---|---|---|---|
| direct + mediated (v7, frozen test, redispatch, ramp) | **3/3** | ~272s | ~20–30 |
| shipped Mode (v7 + guards + facts + 7 tools, no mediation) — r1 | FAIL | 402s | 82 |
| shipped Mode — r2 | FAIL | 250s | 56 |
| shipped Mode — r3 | FAIL | 373s | 68 |
| **shipped Mode total** | **0/3** | | |

Shipped-Mode baseline reused from `evals/2026-10-21-shipped-mode-rung9/`;
mediated baseline from `evals/2026-10-20-mediated-6-9-v7/` (rung 9).
The extensions are engaged; the mediation (absent here) is the lever.
