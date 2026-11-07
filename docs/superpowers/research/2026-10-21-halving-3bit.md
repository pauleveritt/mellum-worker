# Halving Mellum to 3-bit: how far does a cheaper worker get?

Date: 2026-10-21.

## What is measured

The shipped 6-bit Mellum re-quantized to 3-bit (`scripts/halve-model.sh`:
dequantize → 3-bit, group 64; **3.502 bits/weight**, 5.0 G vs the 6-bit's
9.2 G), run on ladder rungs 1-8, direct mode, `tuned`, guards on, native
tool-calling, n=1, **no mediation**.

| | 6-bit (reference) | 3-bit (halved) |
|---|---|---|
| rungs 1-3 (single-file edits) | pass | **pass** |
| rungs 4-5 (harder/multi-file) | pass (A-series 15/15 on 1-5) | **fail** |
| rungs 6-8 (AgentClinic, un-mediated) | — | fail |
| rung 1-8 total | — | **3/8** |
| throughput | ~112 tok/s | ~133 tok/s |
| size / wired | 9.2 G / ~9 G | 5.0 G / ~5 G |

Record: [`evals/2026-10-21-halving-3bit/`](../../ladder/2026-10-21-halving-3bit/).

## What is conjecture

The bits taken by the halving are **load-bearing past a single-spot edit**: the
3-bit keeps simple single-file fixes (1-3) and loses precise multi-file work
(the rung-4 failure is an edit `oldText` mismatch it couldn't recover, falling
back to a full-file `write` that didn't land). The quant damage shows as
edit-precision loss, not total incoherence.

## The finding

Halving to 3-bit by re-quantization is **not a viable worker**: it degrades to
trivial edits only. The higher token rate (~133 vs ~112 tok/s) and smaller
footprint (~5 G vs ~9 G wired) don't pay off, because the rungs it can't do are
where it burns the most time flailing (rung 8 = 600 s). This is the mirror of
the LoRA idea (add trained parameters to *restore* behaviour): PTQ halving
*strips* it.

For contrast, a cross-family small model (Qwen2.5-Coder-1.5B-4bit, ~179 tok/s)
scored **0/8** plain — it does not emit structured tool calls at all (1 turn,
instant stop); with the `content-tool-call-assist` plugin it tool-calls but
flails (loops on an ineffective command on rung 1). So below Mellum's size the
worker role needs both a tool-calling fix *and* a capability it doesn't have.

## Decision

Keep the 6-bit as the worker. Record 3-bit halving as a **negative result**: it
does not hold past trivial edits. If a smaller worker is wanted, the path is a
**LoRA** (format first, then a policy distill from Mellum's traces) — not
post-training quantization.

## What would falsify this / Risks

- **Falsify:** a 3-bit converted from the **source** weights (not re-quantized
  from the 6-bit) might hold rungs 4-5 — the current result can't separate
  halving damage from double-quant. A **4-bit** halve (gentler) might keep more.
- **Risks:** n=1; rungs 6-8 un-mediated (v7 ghost-hunt confounds those fails
  with quant damage — the clean signal is rungs 1-5); lossy-on-lossy re-quant.
