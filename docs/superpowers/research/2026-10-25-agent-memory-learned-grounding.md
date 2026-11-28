# Agent memory — learned, portable grounding (almost a skill)

Date: 2026-10-25. Status: design + working prototype (`learn/code/memory.py`,
33 tests); the deciding with-vs-without run on the fixed model is preregistered
below, not yet run. Builds on the free arm
([2026-10-25-agent-decided-flow.md](2026-10-25-agent-decided-flow.md)).

## What is measured (so far)

The MECHANISM, not the model uplift. The prototype and its tests show:

- The store round-trips to a portable `memory.jsonl` and reloads on another
  process (the "ship it to another machine" path).
- The agnostic guard refuses the obvious answer-leaks — a route path, a quoted
  literal, a multi-digit expected value — and a mutation test confirms the
  negative case is a real gate (disable the guard, the leak is accepted).
- Retrieval ranks lessons by situation overlap and returns nothing for an
  unrelated phase (no grounding noise).
- `distill` maps a failure signature (general, read off a pytest/traceback) to a
  general, agnostic lesson, and returns nothing when it learns nothing general.
- Wired into the free arm, a matching lesson is injected into the coder build
  (like a skill) and a new general lesson is distilled from a gate failure and
  persisted — the run learns from its own mistake.
- A mechanism demo: given the lessons a phase needs, grounding solves it in 1
  round vs 2 when the agent must discover them. This is plumbing, deterministic,
  NOT a model measurement.

## What is conjecture

That injecting learned general lessons raises the FIXED small model's hidden
pass-rate and/or lowers the rounds it needs; that the lessons transfer across
suites and machines; and that fine-tuning on the corpus beats in-context
grounding for a model whose prompt-following is unreliable. None of this is
measured yet.

## The idea — three tiers, one store

A hand-written skill is portable, general procedural grounding an author curated
up front. This memory is the SAME shape, grown from the agent's own failures.

1. **In-context grounding (now, cheap).** `memory.jsonl` of `{situation,
   lesson}` rows. Before a build, retrieve the few lessons whose situation
   matches this phase and inject them. For a fixed small model this lands
   *unreliably* (prompt rules do — the project's standing lesson), so it is a
   lead, not a guarantee.
2. **Fine-tune corpus (portable, reliable).** The same store plus the full
   `prompt → passing-diff` trajectories the free arm already produces, exported
   as supervised data. Fine-tuning writes the lessons into the weights — the
   dependable form of grounding, and literally "ship it with the smaller
   model."
3. **Shipped grounding.** The distilled file travels with the model (a system
   preamble or a retrieval index) so a fresh machine starts already grounded.

The free arm is the data source: it records, per phase, the gate-failure text
and whether the agent eventually solved it — exactly the mistake → correction
signal a lesson is distilled from.

## The one rule that makes or breaks it — stay agnostic

A lesson is GENERAL discipline ("inspect the real columns before reading a
store; never invent a column name"), never the suite's answers ("the visits
table has a date column"). The second is the hidden grader's answer; storing it
turns the memory into a cache of the oracle and every pass after it is
meaningless — the same "never code to the eval" rule as the rest of the harness.

`agnostic_ok` is the guard. It is a BACKSTOP, not a proof: it catches route
paths, quoted literals and multi-digit values, but a bare sentence like "the X
table has a Y column" slips past it. So two more defences carry the rule — the
distiller only emits general discipline keyed to failure signatures, and a
human reviews `memory.jsonl` before it grounds a decisive run or ships with a
model. Only the `lesson` is ever injected (and guarded); the `situation` is
local retrieval metadata, never shown to the model.

## Preregistration (the deciding run)

- **Arms:** `no-memory` (free arm, control) and `memory` (free arm with
  `--memory memory.jsonl`, learning within the run). Plus a `seeded-memory` arm
  — a hand-reviewed `memory.jsonl` carried in cold — for the cross-machine /
  ship-with-model claim.
- **Suites:** the hard suite end-to-end (7 phases) and ladder rungs 6-12, same
  fixed model (Mellum 2.1 6-bit via oMLX), same guards, everything via `uv run`,
  the live watcher on screen.
- **n:** 3 per arm per target (screens first; this decides a default, so n>1).
- **Scoring:** the hidden grader (the real oracle), never the frozen gate.
  Report hidden pass-rate AND rounds-to-solve (`phase_rounds`), AND an
  agnosticism audit of the committed `memory.jsonl`.
- **Decision rule:** adopt memory grounding as a default only if its hidden
  pass-rate is >= `no-memory` AND rounds fall, with ZERO answer-leaks in the
  reviewed memory file. A single leaked answer voids the arm. If in-context does
  not move the needle, that is the signal to measure the fine-tune tier, not to
  loosen the guard.

## What would falsify this / Risks

- **Falsified** if `memory` does not beat `no-memory` on the hidden grade — then
  in-context grounding does not transfer for this model and the fine-tune tier
  is the real test (expected, given the prompt-reliability lesson).
- **Agnosticism leak:** the guard is necessary, not sufficient; a leaked answer
  makes every downstream pass meaningless. Mitigation: distiller discipline +
  human review + the audit in the decision rule.
- **Retrieval noise / coarse distiller:** irrelevant or wrong lessons could
  mislead the coder; retrieval returns nothing on no overlap, and the distiller
  emits nothing when it learns nothing general, but both are crude.
- **Over-fitting the memory to one suite:** situations carry task words, so a
  memory grown on one suite may retrieve poorly on another; the cross-suite
  transfer is part of what the preregistered run measures, not an assumption.
