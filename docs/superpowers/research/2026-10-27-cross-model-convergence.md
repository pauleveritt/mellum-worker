# Cross-model convergence on the flow — a second 12B hits the same wall

Date: 2026-10-27. Lifecycle: screen (directional, n=1). The point of this run
was to swap a *different* model onto the unchanged flow and see where it breaks.
As first run, examine never completed, so there was no grade. A dated follow-up
(**Update 2026-10-28**, below) adds a third cascadable knob — a content/
over-generation cap — that lets the same model terminate examine and reach a
hidden grade; that supersedes the "no grade" statements in the original screen.
See also `2026-10-27-dense-phase-wall-levers.md` (the wall) and
`2026-10-27-proxy-oracle-gap.md` (the examine gate).

## What is measured / What is conjecture

**Measured.** The flow is model-agnostic in structure, but two bits of its
model-calling config were tuned to the default worker and had to be made
cascadable before a second model could run it at all:

1. The pinned profile carried the worker's own `thinkingFormat`, so a bare
   `--model` swap mis-templated reasoning for a server that templates it itself.
   Fixed with `--thinking-format openai` + a one-place `MELLUM_FLOW_THINKING`
   knob for the sub-agents (unset = the worker's calls are byte-identical).
2. Only the coder loaded the loop-breaker. The read-only phases had none, so a
   model that does not converge in a read role could spin a phase unbounded.
   Fixed with the `mellum-loopguard` extension on plan/review_plan/examine/
   review_code (trips only on unbroken identical no-op calls).

With both in place, a network-served 12B instruction model (vLLM, 64k context,
thinking templated server-side) drove the flow on the easy smoke:

| Phase | Behaviour on the second model |
|-------|-------------------------------|
| plan | converged, ~154 events, clean exit |
| review_plan | converged, ~92 events, after a brief `ls "."` stutter |
| examine | did NOT converge: read context, then poured out an unbounded **content** stream (3173 events / ~255s, still going when stopped) toward the 32000-token cap — it never made the stop-and-write decision |

The single-call protocol is clean (a one-shot tool call returns well-formed
JSON args), and plan/review_plan prove the result round-trip works. So examine's
failure is not a calling or parsing bug. The loop-breaker removed the *tool-call*
runaway (the old `ls .` ×1000); the same non-convergence then reappeared in the
*content* channel, which a repeat-call guard cannot cap.

**Conjecture.** The flow's dense-phase wall is a **convergence / throughput**
property of a fixed small model under an open-ended role, not a property of the
default worker, its quantization, or the calling layer. examine is the sharp
case because its terminal action is to *emit* the acceptance test and stop — a
decision the model must make alone, with its own reasoning stripped between
turns. A model that rides live reasoning to "enough, write it" clears it; one
that does not either loops tool calls (capped now) or over-generates content
(not capped). Two different 12B models now show the wall on the same phase.

## What would falsify this / Risks

- **n = 1, one model, one server, easy smoke.** This is a screen, a lead — not a
  rate and not a graded comparison. A second model behaving differently, or this
  model converging on a quieter server or at a different context size, weakens it.
- **No hidden grade.** examine never emitted, so the flow never reached a grade;
  the claim is about *where* it stalls, not a score. A run that reaches a grade
  (e.g. with a content/over-generation cap on examine) is the real test.
- **Confound: the over-generation could be a prompt-fit artefact**, not a pure
  capacity ceiling — the examine prompt pushes "be EXHAUSTIVE", and on a fresh
  workspace there are no earlier gates to anchor it. Keeping the prompt fixed
  across models is deliberate (agnostic), but a model-neutral examine prompt is
  an untried lever that would separate fit from capacity.
- **The open lever is still adaptive decomposition** (per the dense-phase-wall
  note) plus, new here, a *stop-and-emit* bound on examine's content length —
  the loop-breaker's content-channel analogue. The content bound is now built
  and shown to reach a grade (**Update 2026-10-28**); adaptive decomposition is
  still unmeasured.

## Update 2026-10-28 — the content cap reaches a grade

The screen above ended with two open content-channel levers: a per-phase output
ceiling, and an arg-agnostic step budget for the runaway the exact-match
loop-breaker misses. Both are now built as cascadable knobs (no-ops for the
default worker when unset) and re-run on the same network 12B:

1. `MELLUM_FLOW_MAXTOKENS` caps a phase's output tokens (examine ran at 12000,
   down from the worker's 32000), so the content stream cannot run unbounded.
2. The `mellum-loopguard` step budget blocks after a generous call count with a
   "you already have every result — produce your final answer now" nudge. It is
   arg-agnostic, so it catches the varying-arg runaway (`.`, `./`, `./probe_N`)
   that never trips the identical-call breaker.

With both in place the same model reached a hidden grade on the exact seed where
the default worker stalls:

| Run | Hidden | Phases | Visible |
|-----|--------|--------|---------|
| easy smoke (full pipeline) | 4/4 | 1/1 | PASS |
| hard, seeded phases 5→7 | 26/34 | 3/7 | PASS |

**What this changes.** The "no grade" conclusion was an artefact of an uncapped
content channel, not a hard ceiling: examine *can* be made to terminate, and the
flow then grades. The dense-phase wall is still real — 3/7 phases, not 7/7 — but
it now produces a number, which is the comparison that matters against a worker
that gets none there.

**The honest texture of 26/34.** The phase-5 transcript shows the model fighting
its own plumbing, not the problem: repeated failed `write migrations.py` calls
drove ~15 turns of `ls`/`cat`-heredoc/absolute-path workarounds before the file
landed, and it still cleared phase 7's gate (`try0`, `try1` PASS). A share of the
8 missing points is this write-tool friction, a model-calling lead worth chasing
next — and still agnostic, nothing codes to the eval.

**New risks.** The cap value (12000) is a lever, not a measured default; too low
would truncate a legitimate examine. n is still 1 per arm. The 3/7 phase count is
a single seeded run, not a rate.
