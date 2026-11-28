# 0002: Preference pairs come from the model's own runs, judged by hidden tests

- **Date:** 2026-11-27
- **Status:** Accepted

## Context

DPO teaches a preference between two answers to the same context. Pairs from another model's work teach habits
the tuned model doesn't have. The model's own runs, graded by the suites' hidden tests, give pairs that differ
only in what made a run pass or fail.

## Decision

- Pairs are cut from Mellum's own recorded runs: phase pairs (a passing phase against a failing one), step
  pairs (a failed call against the clean retry), and pathology pairs (shell, outside search, unused import,
  re-read after a failed edit, scratch-file cleanup). Each shares everything before one act and scores only
  the part that differs.
- The hidden grade decides winners; a phase that broke an earlier phase counts as failed; contaminated runs
  are out unless the trace never shows the grader canary.
- Tools before knowledge: improve tool calling first (`--no-knowledge`), teach new Python idioms only after.
- Training: IPO loss (beta 10), LoRA rank 8 scale 2.0 on 16 layers, lr 2e-5, accumulation 4, 2,048-token
  chunks, one epoch, evaluation every 15 updates.

## Consequences

The tune can only prefer habits the base already shows sometimes. A model with no tool calling at all has no
successful calls to prefer, so it needs supervised training first (see 0005).

## Evidence

`learn/finetune/build_dpo_phases.py`, `phase_pairs.py`, `pathology_pairs.py`; sets `data_dpo_mix_tools`
(Tsunami) and `data_dpo_mix_tools_v2` (round 2).
