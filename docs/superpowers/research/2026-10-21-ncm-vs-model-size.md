# The NCM gate makes a worker try, not able — across model sizes

Date: 2026-10-21.

## What is measured

`extensions/mellum-ncm.ts` (the NCM verify gate) on rung 9, n=1 per model, with
the frozen `test_phase4.py` placed and guards on. The 1.5B also loads
`content-tool-call-assist` (no structured tool calls otherwise).

| model | rung 9 | wall | `mellum-ncm.ts` fires |
|---|---|---|---|
| 6-bit Mellum | **3/3** | 110–145s | **0** (passes first-try) |
| 3-bit Mellum | **FAIL** | 291s | dozens |
| 1.5B Qwen + assist | **FAIL** | 62s | fires, model loops on `pytest` |

Record: [`docs/ladder/2026-10-21-ncm-vs-model-size/`](../../ladder/2026-10-21-ncm-vs-model-size/).

## The finding

`mellum-ncm.ts` forces a worker to keep going until the frozen test is green —
it is a verify/exit gate, not a capability source. Across sizes:

- On the **capable 6-bit** it is **dormant** (0 fires) and non-regressing — the
  model passes first-try, so the gate's active value isn't exercised.
- On the **incapable** models it **fires and they still fail**: the 3-bit makes
  imprecise edits it can't land; the 1.5B (now tool-calling via assist) runs the
  test over and over without editing the code. Forced retries don't add ability.

So the gate's value is confined to a *capable* worker that self-exits with the
test still red (the phase-4 `id` miss) — not demonstrated here, since the 6-bit
doesn't self-exit and the small models can't do the work at all.

## Decision

A verify gate cannot substitute for capability. The route to a smaller worker is
to **add** capability — a LoRA (format, then a policy distill from Mellum's
traces) — not to **gate** an incapable model. Keep `mellum-ncm.ts` as the
exit-gate for capable workers; do not expect it to lift small ones.

## What would falsify this / Risks

- **Falsify (the gate's real value):** a capable worker that self-exits red and
  the gate recovers it to a pass — still the missing A/B.
- **Risks:** n=1 per model, one machine; the 3-bit is a lossy-on-lossy re-quant
  and the 1.5B is cross-family, so "incapable" bundles quant damage, size, and
  family — the shared signal is only that forced retries didn't convert a fail.
