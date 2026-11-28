# 0007: N-gram speculation is the baseline a trained draft head must beat

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

The goal is our own speculative head for the 1.5B. llama.cpp (0.9.0) serves n-gram speculation with no extra
model, and draft heads of the EAGLE-3, MTP, DFlash and DSpark types. No published draft shares the 1.5B's
vocabulary with its new tokens. Agent turns repeat text already in the context (edits, paths, test output),
which is what n-gram speculation exploits.

## Decision

- First measure `--spec-type ngram-mod` on recorded agent turns of the trained 1.5B: tokens per second,
  acceptance length, and identical outputs against no speculation.
- Then train our own draft head on the trained 1.5B's outputs (so it shares the new tokens) and test it on the
  same turns. Keep it only if it beats n-gram.

## Consequences

The draft head is judged against a free alternative, not against no speculation.

## Evidence

To come: plan step 5 and 6 in `docs/superpowers/plans/2026-11-28-r1d-tool-tokens.md`.
