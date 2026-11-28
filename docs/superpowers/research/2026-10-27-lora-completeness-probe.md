# LoRA completeness probe — preregistration

Date: 2026-10-27. Lifecycle: run (directional, n=1 per arm) — see Result.

## Result (2026-10-27)

Run as directional screens, not the full preregistered n=3. The probe's hypothesis
(a completeness LoRA closes the dense-phase gap) did **not** hold: a corrected
tool-call adapter (200 samples) on the 6-bit base failed phase 5 the same as base,
and retraining on 8-bit stalled. The adapter fixed tool-call *mechanics* (the
earlier flat-dump adapter had degraded them) but not completeness on the dense
phase. Combined with the 8-bit precision screen, the wall reads as a model
throughput ceiling, with quantization ruled out. Full cross-lever write-up:
`2026-10-27-dense-phase-wall-levers.md`. The open lever is adaptive decomposition,
not more LoRA samples.

## What is measured / What is conjecture

**Measured (the lead this probe tests).** On the hard suite, the fixed model's
dominant failure is *systematic omission*: it builds the salient requirement of
a multi-requirement phase and silently drops the rest, identically at
temperatures 0.3 and 1.2, so best-of-N cannot rescue it. Phase 5 ("Archive &
Audit") fails its gate across all runs, including gate+feedback. See
`2026-10-27-proxy-oracle-gap.md` and `flow-coder-feedback`.

**Conjecture (H1).** The omission is a *behavioural / instruction-following*
gap — the model can emit each requirement but does not attend to all of them —
and a small LoRA adapter trained to complete every enumerated requirement
raises the hidden grade on hard, with adapter-off held as the control.

**The competing explanation (H0).** No lift. The gap is a *capacity* ceiling on
the dense phase, or *quantization* loss in the 6-bit weights — neither of which
a light adapter moves. A null is itself a result: it redirects effort from
behaviour to capacity/precision.

## Arms

| Arm | Model | Flow config |
|-----|-------|-------------|
| A (control) | Mellum 2.1 12B-A2.5B Thinking, 6-bit, no adapter | spec-coverage gate + `MELLUM_CODER_FEEDBACK=1` |
| B (treatment) | same base + LoRA adapter | identical to A |

Everything but the adapter is held fixed: same suite (hard), same settings
(`--thinking medium --context-window 40000 --attempts 6 --concurrency 1
--retry-concurrency 2`), same prompts, same gate, same grader.

## The dataset — independent, never the eval

The agnostic rule is load-bearing here: the adapter data must share **no**
routes, tables, columns, exact strings, or app identity with the hard suite or
its grader. Training on the eval would make any lift meaningless.

- **Shape.** Each example is an independent multi-requirement coding task: a
  spec that enumerates N ≥ 3 requirements (routes, columns, exact status codes,
  a migration that must be written **and** applied **and** tracked **and**
  idempotent, a report endpoint with an exact JSON shape) plus a reference
  solution that satisfies **all** N, plus a per-requirement checker.
- **Domains.** Several apps unrelated to a complaints/tickets tracker — e.g. a
  notes API, an inventory service, a bookings ledger — with their own schemas
  and routes, so nothing leaks from the eval's domain.
- **Over-represent the failing shapes.** The second endpoint, the
  apply-and-track step of a migration, the exact status code, the exact JSON
  keys — the requirements the model drops now.
- **Format.** Train in the model's own chat/tool format so the behaviour
  transfers to the flow; include the "fix from a named failing assertion
  without regressing the rest" shape (the feedback-under-load capability).
- **Size.** A probe, not a production tune — start at a few hundred verified
  examples.
- **No ghosts.** Every reference must pass its own per-requirement checker
  before it enters the set; a reference that does not actually satisfy all N is
  dropped, not included.
- **Independence guard.** An automated check rejects the set if any hard-suite
  route, column, or exact literal appears; generation provenance is recorded.

## Training (MLX)

- `mlx-lm` LoRA on the same 6-bit base the eval uses (apples-to-apples with the
  control), modest rank (start r=16), attention + MLP projections, a few
  hundred steps, low learning rate. Light by design.
- A full-precision arm is a **follow-up**, not part of this probe — it is how we
  later separate quantization from the trained weights, once we know whether the
  adapter moves anything at all.

## Eval protocol and decision rule

- Run the flow ladder on hard for each arm, **n = 3 runs per arm** (screens →
  rates; one run is a lead, per `docs/sdd.md`).
- **Primary metric:** hidden grade /34 (mean across the 3 runs).
- **Secondary:** does phase 5 ever clear its gate; phases-passed; which of the
  known 8 misses close.
- **Decision rule, fixed in advance.** Call it a lift only if B's mean hidden
  grade exceeds A's by **≥ 2 checks** *and* phase 5 clears its gate in **≥ 1**
  B-run. Otherwise: no lift — the signal points at capacity or quantization, and
  the full-precision arm is the next step.
- Runs are sequenced, not concurrent: oMLX is single-GPU, so the six runs queue.

## What would falsify this / Risks

- **Confounded null.** No lift could mean capacity *or* quantization *or* a
  too-small/weak dataset — the three are not separated by this probe alone. The
  full-precision follow-up and a dataset-size sweep are the disambiguators;
  state the null as "no lift under this adapter," not "untrainable."
- **Leakage.** Any overlap between the adapter data and the eval invalidates the
  result; the independence guard and a manual spot-check gate the data.
- **Overfit to task shapes.** The adapter could learn the training domains
  without generalising; the hard suite is held out precisely to catch this.
- **Ghost references.** A reference that does not satisfy all N teaches the wrong
  target; per-requirement verification is mandatory before inclusion.
- **Cost.** Training plus 6 ladder runs (~3–4 h each on oMLX) is real compute;
  budget it before starting, and keep the dataset small until a first signal.
- **Scope.** This changes the model, which is outside the harness-only remit of
  the main project — it is an explicit experiment to generate training signal
  for the model team, run and recorded as such, not a shipped harness change.
