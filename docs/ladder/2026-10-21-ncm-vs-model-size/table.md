# `mellum-ncm.ts` (NCM verify gate) × model size — rung 9

All with the frozen `test_phase4.py` placed and `mellum-ncm.ts` loaded via
`--pi-extension`; guards on. The 1.5B also carries `content-tool-call-assist`
(it cannot tool-call otherwise).

| model | rung 9 | wall | gate fires | what happened |
|---|---|---|---|---|
| 6-bit Mellum (Mode) | **3/3** | 110–145s | **0** | passes first-try; gate dormant. ([record](../2026-10-21-mode-ncm-rung9/)) |
| 3-bit Mellum | **FAIL** | 291s | dozens | forced back repeatedly; imprecise edits, never lands |
| 1.5B Qwen + assist | **FAIL** | 62s | fires | tool-calls (via assist) but loops running `pytest` without editing |

**The gate makes a worker *try*; it cannot make it *able*.** The only pass is
the capable 6-bit — which didn't need the gate at all.
