# Halved 3-bit Mellum — rungs 1-8 (n=1)

Model: `Mellum2.1-12B-A2.5B-Thinking-3bit` (12B params at 3.502 bits/weight,
5.0 G — the 6-bit re-quantized by `scripts/halve-model.sh`). Direct mode,
`tuned`, guards on, native tool-calling, **no mediation**.

| rung | result | wall | note |
|---|---|---|---|
| 1 | **PASS** | 37s | single-file edit |
| 2 | **PASS** | 105s | |
| 3 | **PASS** | 100s | Python rename across files |
| 4 | FAIL | 194s | edit-precision wobble → full-file `write`, didn't land |
| 5 | FAIL | 269s | |
| 6 | FAIL | 157s | AgentClinic phase 1 — **un-mediated** |
| 7 | FAIL | 268s | AgentClinic phase 2 — **un-mediated** |
| 8 | FAIL | 600s | AgentClinic phase 3 — **un-mediated**, flailed |
| **total** | **3/8** | | |

Clean verdict is the coding rungs: **passes 1-3, fails 4-5.** Rungs 6-8 were
un-mediated (no frozen test placed), so v7 ghost-hunts there as in shipped Mode —
those fails confound quant damage with the no-test setup. Reference: the 6-bit /
shipped worker passes 1-5 (Paul's A-series, 15/15).

Throughput: 3-bit ~133 tok/s vs 6-bit ~112 (faster per token), but flailing eats
it (rung 8 = 600s). "VRAM" (wired): 3-bit ~5 G vs 6-bit ~9 G.
