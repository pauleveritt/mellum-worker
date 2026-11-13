# Next Concept Modelling for the worker — a concept-grain loop

Date: 2026-10-20. A design note for the maintainer. This is a **lead**, not a
measured result: it proposes an architecture and says how we would screen it.

## TL;DR

Make the worker's unit of decision a **concept** (one semantic step toward the
goal) instead of a token or a free-form turn. A planner predicts the *next
concept*, the model realizes it as code, a test verifies it, and the loop
predicts the next concept. The base model does not change — this is a harness
layer on top of the existing mediated loop.

## At a glance

| aspect | token-grain (today) | concept-grain (NCM) |
|---|---|---|
| unit of decision | next token / one free-form turn | next **concept** — one spec step |
| plan | implicit in the prompt | explicit: planner emits the next step |
| verify | whole frozen test after the turn | that concept's assertions, per step |
| retry (re-dispatch) | resample seed/temp on the whole task | re-predict the next concept from its failure |
| "done" | worker's self-judgement (the phase-4 miss) | every spec concept covered (embedding / NCM check) |
| base model | fixed token-level model | **unchanged** — harness layer only |

## The idea

"Next Concept Modelling" is prediction at the grain of concepts rather than
tokens (the Large-Concept-Model lineage: reason over sentence/step embeddings,
predict the next concept, then expand to text). We cannot re-objective the
worker model — it is a fixed token-level autoregressive model served locally —
so we apply the *approach* as scaffolding: lift the decision grain from "next
token" to "next step toward the spec".

## Why now — what the ablation says

The 12/12 mediated win on rungs 6–9 stacked four changes (specialized prompt,
focused test command, trimmed tools, fail-fast effort ramp). The single-variable
ablation (this session) toggled each back on rung 9, the historical ceiling:

- v6 prompt → still 3/3
- whole-directory test command → still 3/3 (but ~10× the wall time)
- grep/find tools restored → still 3/3

i.e. **none of the token-level tweaks move the pass rate** — they move cost. The
lift is the **mediated frozen-test + re-dispatch loop**: an external, complete,
unweakenable test plus several *scored* attempts. (Arm D — fixed-high budget,
no ramp — is the last check; results fold into the ablation note.)

Concept-grain modelling is the natural generalization of that loop: if repeated
*scored* attempts are what works, run the scoring and the attempts at the grain
of **individual spec concepts**, not the whole task at once. That should help
most where the ceiling actually was — the multi-step phases (rungs 8–9), where a
single pass stalls or self-exits on an incomplete, self-authored notion of done.

## How it maps to the worker and the ladder

A concept = one sub-goal of the spec, phrased semantically. The hand-written
frozen phase test already encodes them as independent `test_*` functions (phase
4: stable integer ids; default open; resolve/reopen change status + 303; listing
order preserved). The loop:

```
plan    : spec + repo state + last failure  ─►  NEXT CONCEPT (one step)
realize : NEXT CONCEPT                        ─►  the worker edits code (bounded)
verify  : the concept's assertions            ─►  pass? advance : re-model concept
```

- **Planner** emits one next concept. Cheapest: a constrained "thinking" pass
  that outputs a single step. Stronger: a small distilled concept-proposer
  trained on `(state, spec, failure) → next step`.
- **Realizer** is today's bounded "make X pass" worker, unchanged.
- **Re-model on failure** lifts the current re-dispatch from "resample tokens"
  to "re-predict the next concept", fed the concept-level failure.

## Optional metric half (where the name comes from)

Embed each concept and the spec/failure in a shared space and pick the next
concept by nearest prototype (a Nearest-Class-Mean-style routing). This also
gives a principled **done-detector**: stop when every spec concept is covered by
passing assertions — directly attacking the self-exit miss where the worker
declares done against an incomplete test. Cost: a small embedding model in the
serving path.

## Integration points

- A **planner stage** before `run_single` in `ladder/ladder/run_ladder.py` that
  decomposes the acceptance test/spec into an ordered concept list.
- **Per-concept acceptance**: run the frozen test after each concept, advance
  only as that concept's assertions go green (the test is already one function
  per concept).
- **Concept-level `redispatch_message`**: hand back "concept N still unmet:
  <failure>" instead of the whole dump.
- The distilled proposer is a separate artifact, measured before any claim.

## How we would screen it

Rungs 8–9, n≥3, mediated, against the current mediated loop as the control
(same frozen tests, same scorer). Report pass rate **and** wall time — the
concept loop adds planner turns, so it must earn its cost, not just match pass
rate. Pre-register arms, n and scoring per the usual rule before any deciding
run.

## Caveats

The base model stays token-level; NCM here is scaffolding plus an optional
embedding model plus an optional distilled proposer — not a new base model. It
is a lead motivated by the ablation, unmeasured until the rung-8/9 screen.
