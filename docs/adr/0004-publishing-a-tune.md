# 0004: Publish only after checks and a smoke test, private first, public on a clear win

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

A named public model invites people to treat it as an upgrade. Tsunami's screens show tidier tool calls but no
proven pass-rate gain over base.

## Decision

- `learn/finetune/publish_hf.py` dry run first: architecture and chat template must match the base, the card is
  generated from the results and the training set, and a live llama-server must return a parsed tool call.
- Upload creates the repository private. Making it public is the owner's decision, taken only after a clear
  win (for example a preregistered Medium comparison) and, if wanted, well-known benchmarks (BFCL, EvalPlus).
- The card states where an early checkpoint stopped in its run, and never claims more than the screens show.

## Consequences

Tsunami (`andrevanzuydam/Mellum2.1-12B-A2.5B-Thinking-tsunami`) is uploaded private and stays private for now.

## Evidence

Upload 2026-11-28: card, SHA256SUMS, results.json, adapter, 8.07 GB GGUF; `tests/test_publish_hf.py`.
