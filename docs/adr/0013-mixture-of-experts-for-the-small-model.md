# 0013: A mixture-of-experts effect for the small model, deferred behind the tool-calling proof

- **Date:** 2026-11-28
- **Status:** Deferred (revisit when the 1.5B's behaviour is right and it clearly runs out of capacity)

## Context

A mixture of experts (MoE) replaces each layer's single feed-forward block with several expert blocks and a router
that sends each token through only the top one or two: more parameters held, the same compute per token. Mellum
is built this way (12B total, 2.5B active). The 1.5B is dense. Its current gap is behaviour (the tool-call format
and habits), not capacity, so MoE would not close it.

## Options, cheapest first

1. **Harness routing per request:** separate LoRA adapters for different kinds of work, the harness picks one per
   turn; llama.cpp already loads several adapters and sets their weight per request. Coarse, not per token; the
   same pattern as the thinking switch (0012).
2. **A mixture of LoRA experts:** frozen base, several small LoRA adapters per layer and a tiny router choosing per
   token (for example tool-call syntax, code edits, shell). Cheap to train with the current tooling; llama.cpp
   cannot serve a per-token router over adapters, so it needs custom serving or folding into a known layout.
3. **Upcycling:** copy each trained MLP into N experts, add a router that starts uniform, keep training until they
   specialise. A real MoE that llama.cpp can serve (Qwen2-MoE layout), but about N times the MLP memory (4
   experts: roughly 4-5B parameters in total) and the most training.

## Decision

Deferred. If revisited: option 1 first, then option 2 as a small-model experiment, and upcycling only if the 1.5B
clearly runs out of capacity after its behaviour is right. Any of them is measured like every other change:
calls that parse, faulty calls, BFCL, then Easy (0010).

## Consequences

No GPU spent on it now.
