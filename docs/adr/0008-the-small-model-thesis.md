# 0008: The goal is to prove a small model becomes powerful when fine-tuned and harnessed properly

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

GPU is limited to one Apple M3 Max. The owner's belief is that a small model becomes powerful if it is
fine-tuned properly and harnessed properly. The work so far tuned a 12B model (Mellum 2.1, 2.5B active) and
showed tidier tool calls but no proven pass-rate gain (0003, 0004). A 1.5B model trains in hours, not days.

## Decision

- The fine-tune work sets out to prove that claim. The vehicle is DeepSeek-R1-Distill-Qwen-1.5B: it starts with
  no tool calling at all (0005, 0006), so any working agent behaviour is something fine-tuning and the harness
  added.
- The claim is judged on the same suites and harness as every other model, against named baselines: the base
  1.5B (no tool calling) and Mellum 2.1 12B base. Reported with passes: requests, tokens per second, memory.
- Experiments are ranked by how directly they move the proof per GPU-hour. Side ideas (a draft head, concept
  modelling) earn GPU only when they serve it; speed work counts because a fast small model can afford more
  attempts within the same budget.
- Steps toward the proof, each a gate for the next:
  1. the 1.5B calls tools in a parseable format (supervised training on new tokens);
  2. it passes Easy runs at all;
  3. on-policy preference training on its own runs (0002) lifts Easy and Medium;
  4. a preregistered comparison against Mellum 12B base on Medium, at n of 10 or more, with cost.

- The small model is also the testbed: a concept (new tokens, a draft head, a concept head, a harness remedy)
  is tried on the 1.5B first because it costs a fraction of the GPU, then carried to larger models (Mellum
  12B) if it holds. A result that transfers is re-measured on the larger model, never assumed: earlier levers
  proved tier-dependent (a wash on easy, a real win on medium).

## Consequences

Work that doesn't move a step gets deferred. A step that fails is a learning, recorded as an ADR, not hidden.

## Evidence

To come; the research note `docs/superpowers/research/2026-11-28-tool-tokens-1-5b.md` logs each step.
