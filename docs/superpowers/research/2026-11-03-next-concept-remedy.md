# Next-Concept Modeling as a coding remedy

- **What is measured:** nothing yet — this is the design and the preregistration
  for a coarse-to-fine remedy. The v1 prose unit (`prompt/concept-sketch`) ships
  unmeasured, a lead.
- **What is conjecture:** that building code coarse-to-fine — sketch the whole
  app, then fill the bodies — beats one-shot file-by-file on the multi-phase
  tiers, and that an enforced version beats the prose one (the session's
  enforce-vs-prose result).

## The idea, from the paper

HazyResearch/ncm (Next-Concept Modeling, Kumbong et al. 2026) generates text
coarse-to-fine: a tokenizer turns a sequence into a hierarchy of discrete codes,
and a transformer predicts that hierarchy from coarse levels to fine, positions
within a level in parallel — a rough sketch progressively refined. We cannot run
that architecture here (the model is fixed Mellum on llama.cpp). What carries
over is the **method**: produce the coarse concepts first, then refine to detail,
rather than finishing one piece before the next exists.

For code the mapping is:

- **Coarse (the concepts):** every file the spec implies, laid out as a skeleton
  — imports, the classes and functions with their real signatures, each body a
  stub, plus a one-line plan per requirement.
- **Fine:** fill the bodies one at a time, running the tests after each — and,
  the paper's parallel twist, each file's body could be refined by its own
  subagent at once.

The failure it targets: a small model builds one file to completion, then the
next, and the layout drifts, imports dangle, and an earlier phase breaks — the
same pathology the per-phase flow addresses, approached from the other side
(sketch-first instead of phase-gated).

## v1 — prose (shipped, a lead)

`remedies/prompt/concept-sketch.ts` appends one instruction to each user message:
sketch all files first, then fill bodies one at a time. It is the cheapest test
of the idea. We expect it to land unreliably — the session's enforce-vs-prose
run showed the model reads prose rules (even `AGENTS.md`'s "do not start
servers") and ignores them. So v1 is the baseline for v2, not the answer.

## v2 — enforced (designed, to build)

A harness extension (sibling to `mellum-flow`) that makes the two passes real,
so they do not depend on the model obeying prose:

1. **Sketch pass.** First turn runs under an instruction to emit skeletons only.
   On settle, a check confirms each spec-named file exists and parses (Python
   `ast.parse`) with stubbed bodies; if not, re-dispatch. The skeleton is frozen
   as a checkpoint.
2. **Refine passes.** Then, one file (or one spec requirement) at a time, dispatch
   "fill this body; keep every other file's signatures unchanged", verifying with
   the project's tests after each. Optionally parallel: one subagent per file,
   each handed the frozen skeleton, results merged — the paper's parallel level.
3. **Freeze the layout.** Between passes a guard blocks a `write` that changes a
   file's signatures or moves it, so refinement cannot re-tangle the layout.

The enforcement is the point: the structure holds whether or not the model
"remembers" to work coarse-to-fine.

## Arms, n, rule

Measure on **medium and hard** (easy is one phase, so coarse-to-fine has little
to bite on), `--arm worker`, cold, n=3, judged on the hidden grader:

| cell | remedy |
|---|---|
| baseline | the tier's measured preset |
| + v1 prose | preset + `prompt/concept-sketch` |
| v2 enforced | the enforced extension, once built |
| flow (reference) | `workflow/spec-driven-flow` — the other multi-phase approach |

**Decision rule.** If v1 lifts the tier, keep it and still build v2. If v1 does
nothing (the likely case) but v2 lifts it, that is another enforce-over-prose
data point and the remedy is the enforced one. If neither beats the flow, the
flow already covers this ground and the remedy is redundant.

## What would falsify / risks

- **Falsifies the idea:** coarse-to-fine (even enforced) does not beat one-shot
  or the flow on medium/hard.
- **Risk:** the sketch pass can waste turns on a model that writes thin stubs;
  the refine pass can still break a frozen signature. n=3 is a screen.

## Result

_(pending — v1 shipped, v2 and the runs to come)_
