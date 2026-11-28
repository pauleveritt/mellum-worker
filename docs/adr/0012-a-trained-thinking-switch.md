# 0012: Thinking on and off is a trained switch, a control token, not a template trick

- **Date:** 2026-11-28
- **Status:** Proposed (to be measured on the 1.5B, then Mellum)

## Context

Thinking is 80% of the 1.5B's completion tokens. Models given an empty `<think></think>` they were never trained
on turn thinking off unreliably, and DeepSeek-R1-Distill was trained only to think. Mellum has no reasoning
dial at all; shorter thinking there came from a prompt. A switch the harness can set per turn would let the
small model think when a step is hard (after a failure, when planning) and skip it for routine calls.

## Decision

- Add control tokens with the same token surgery as the tool markers (0005): `<｜think▁on｜>` and
  `<｜think▁off｜>` in spare rows, placed by the template at the start of the assistant turn.
- Train both modes on the same contexts: *on* = the teacher's thinking then the call; *off* = an empty thinking
  block then the same call. The decision in the *off* target still comes from a teacher that thought.
- Measure, per mode: obedience (thinks when on, none when off; the bar is every turn), calls that parse, faulty
  calls per 100, and the Easy screen; plus speed and tokens.
- A Pi extension sets the switch per turn (for example on after a failed call or test, off for reads), measured
  as a remedy like any other (0009).
- If it holds on the 1.5B, add the same switch to Mellum and re-measure there (0008).

## Consequences

One training set yields both modes, so the cost is one extra copy of each example without its thinking, which
is short. Training a whole run in one pass (loss on every turn) becomes possible in the *off* mode, since history
then matches inference.

## Evidence

To come. Token split: research note `docs/superpowers/research/2026-11-28-tool-tokens-1-5b.md`.
