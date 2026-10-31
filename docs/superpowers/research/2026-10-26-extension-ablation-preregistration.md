# Extension ablation on rungs 1–12 — what each extension contributes, and which combination passes best

Date: 2026-10-26. Status: preregistration (design fixed before the run). No
results yet. A Mellum ladder ablation to attribute each rung's pass to the
extension(s) responsible and to rank the combinations that pass it.

## The question (from the request)

1. **Bare floor** — with NO extensions, just the model, how far up rungs 1–12
   does Mellum get on its own?
2. **Additive contribution** — add one layer at a time and re-test; each rung
   that newly passes is credited to the layer that unlocked it.
3. **Best combination** — a rung can pass under several combinations; of those,
   **which combination passes it best** (most reliably and most cleanly)?
4. **Sub-agents on vs off** — the decomposition/delegation machinery (the
   `plan`/`examine`/`review` sub-agents the flow spawns, and the mode's
   delegated path) is itself a layer. Does a SINGLE-agent run — the model
   driving the whole loop itself, with the same guards/facts — pass rungs we
   assumed needed sub-agents? I.e. are sub-agents load-bearing, or scaffolding
   the model doesn't need at a given rung?

## What is measured vs conjecture

Nothing measured yet. This note fixes the arms, n, the scoring of "best", and
the attribution rule BEFORE the run, so the result is a decision, not a story.

## The ablatable surface (grounded in the real ladder, not invented)

`run_ladder` loads `pi` with `--no-extensions` and then adds only a few things
explicitly — the rest ride INSIDE the mode bundle (`mellum-worker.ts` imports
`mellum-check`, `mellum-facts`, `mellum-record`, `mellum-learn`, `mellum-last`,
and uses `mellum-guards`). So the independently-toggleable layers are:

- **profile**: `baseline` → `tuned` (sampling / penalty settings)
- **mode**: `direct` (bare worker prompt + tools) → `mode` (the bundle) → `flow`
- **guards**: off → on (`mellum-guards.ts`)
- **facts**: off → on (the `facts` flag in mode)
- **sub-agents (orchestration)**: single-agent (the model runs the whole loop —
  `direct`, and `mode` without delegation) → sub-agents (the `flow` phase
  pipeline, and the mode `delegated` path). This axis partly rides on `mode`
  (direct is single-agent, flow uses sub-agents), so the isolating cell is
  "same guards/facts, single-agent vs sub-agents" — e.g. `tuned+direct+guards`
  (single) vs `tuned+flow+guards` (sub-agents), same rung.

Per-individual-extension granularity (facts vs check vs learn vs last, each
alone) is **out of scope for this run** — it needs `mellum-worker.ts` split so
each sub-feature loads behind its own flag (a refactor), recorded as a
follow-up if a layer's contribution needs unpacking.

## Arms

The additive backbone (answers Q1 + Q2), rungs 1–12:

| # | profile | mode | guards | facts | what it isolates |
|---|---|---|---|---|---|
| A0 | baseline | direct | off | — | the bare model floor |
| A1 | tuned | direct | off | — | + sampling/penalty tuning |
| A2 | tuned | mode | off | off | + the mode bundle (no facts) |
| A3 | tuned | mode | off | on | + facts |
| A4 | tuned | mode | on | on | + guards (the shipped mode config, single-agent) |
| A5 | tuned | mode-delegated | on | on | + sub-agents via delegation (vs A4: isolates sub-agents) |
| A6 | tuned | flow | on | on | the flow phase pipeline (sub-agents) |

The combination sweep (answers Q3) adds the off-backbone combos that could also
pass a rung — e.g. `tuned+direct+guards` (A1+guards, the old `a0`),
`baseline+mode`, `tuned+mode+guards+facts-off` — pruned to the meaningful ones
(facts only applies with mode; flow is its own mode). Any combo that passes a
rung is eligible to be its "best".

## Scoring "best" (fixed now)

For a rung, rank the combinations that pass it by:

1. **Pass-rate** across reps (3/3 beats 2/3 beats 1/3) — reliability first.
2. Tie-break on **cleanliness**, from the ladder's own metrics (lower is
   better, in order): `tool_errors`, `anchor_fail`, `nudges`, `reentries`,
   then `requests`, then `wall_s`. These columns already exist in the ladder
   table (see `evals/2026-10-09-ablation-a0-replace/table.md`).

The **best combination** for a rung is the top of that ranking. The
**responsible layer** (Q2) is the first backbone arm at which the rung reaches
a passing pass-rate.

## Protocol

- Model: Mellum 2.1 6-bit via oMLX; rungs 1–12; **n = 3 reps** per arm per rung
  (screen-plus; a default claim would want more).
- Scoring oracle: the ladder's own pass/fail per rung (`result`), never a
  proxy. Everything via `uv run`; `scripts/watch_ladder.py` visible per the
  skill; records promoted to `evals/<date>-extension-ablation/`.
- Runs sequentially on the single GPU, **queued behind the live Qwen/Mellum
  flow comparison**.

## What would falsify / risks

- **n = 3 is a screen, not a rate** — a combo that passes 2/3 vs 3/3 may be
  noise; a "best" decided on one rep's cleanliness is a lead, not a verdict.
- **The mode layer is a composite** — "mode unlocked rung R" means the bundle
  did, not a single file; Path B (the refactor) is the only way to attribute
  inside it.
- **Additive order-dependence** — crediting a rung to the first layer that
  unlocks it can hide that a later layer would also have; the combination sweep
  mitigates this by scoring off-backbone combos too.
- **Rungs are not independent of profile** — `tuned` changes sampling, so a
  rung's pass can shift on resampling alone; the pass-rate-first scoring is
  meant to absorb that, n permitting.
