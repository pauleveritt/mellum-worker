# Plan-mode worker thrash — the direct nudge, the stall rethink, guards to sub-agents

**What is measured:** an easy plan-arm screen (n=3 per arm) that compares the
shipped plan loop with and without a *worker-direct* nudge, while every worker
runs under a 25-call turn cap with a one-shot stall rethink, the guards carried
to the delegated sub-agents, and a new `exists` guard — all wrapped in a hard
per-rep wall/stall backstop. **What is conjecture:** that the worker-direct
nudge is the lever that moves the grade; that the real cause of the thrash is
the architect's step decomposition, not the worker's turn count; and that
grounding the worker's edit on exact retrieved bytes would remove it.

## Provenance

The runs exercise the **real shipped extension** (`extensions/mellum-worker.ts`,
the `PLAN` branch), the **real local model** (Mellum Q4_K_M via llama-server on
`:8001`), and the **real hidden grader** (`learn/code/suites/easy/grader`, 4
checks). They are driven through `pi -p` from a scratchpad driver, **not**
through `run_ladder` — so this is a screen of the shipped loop, not a
ladder-recorded result. Each rep starts from a clean `suites/easy/base` seed in
its own workspace; the prompt is `suites/easy/prompts/01.md` only.

## What was on for both arms

- `preset:easy` + `guard/repeat-loops` + `guard/turn-cap` + `guard/outside-workspace`
  + `guard/exists`, `MELLUM_TURN_CAP=25`, per-rep backstop `DEADLINE=480s STALL=150s`.
- The guards are carried to the architect's spawned sub-agents via `guardArgs()`
  (everything except `turn-cap`, which the architect is exempt from — a
  many-step plan legitimately needs more than 25 of its own turns).
- The only difference between arms is `MELLUM_DELEGATE_WORKER_DIRECT=1`, which
  appends one line to each worker's brief: implement the step doc directly, do
  not re-derive the earlier steps' decisions.

## Result (easy, n=3 each)

| cond | r1 | r2 | r3 | mean grade | mean wall | worker turns/step (clean rep) |
|---|---|---|---|---|---|---|
| default | 0 (DEADLINE) | 0 | 4 | **1.33/4** | ~366s | ~42–47 total |
| worker-direct | 4 | 4 (DEADLINE) | 4 | **4.00/4** | ~346s | 12 / 18 / 21 |

Three things the logs show, beyond the tally:

1. **The worker-direct nudge is the lever.** It is the only variable between the
   arms and it takes the mean grade from 1.33 to 4.00. In the clean direct rep
   the three workers ran 12 / 18 / 21 turns — inside the 10–25 target.

2. **The turn cap + stall rethink fire correctly, and do not rescue.** In
   `default r1` a worker hit the 25-call cap, was stopped with a summary, and a
   fresh worker was re-dispatched for the same step (the rethink built in
   `doTaskPlan`). The replacement repeated the same struggle and the rep still
   hit the 480s wall → scored 0. The cap stops the thrash; the rethink hands a
   fresh worker the *same inconsistent step doc*, so it loops again.

3. **The root cause is the step decomposition, not the turn count.** The
   stalling workers loop on an edit whose `old_string` is not in the file — the
   step doc describes an edit to `app.py` whose anchor text a prior step never
   wrote, and the hero section is split across the wrong step. A worker that
   builds `old_string` from assumption cannot match it, reads the file again,
   tries again, and burns its budget. The direct nudge helps only because a
   focused worker reaches a matching edit sooner — it does not fix the doc.

## Two defects this screen surfaced

- **`exists` guard gap.** `uv run --frozen python -m pytest tests` (a missing
  `tests/` dir) slips past `missingReadPath` because the command's first token
  is `uv`, not one of the read-runner names the scan keys on. The thrash it was
  meant to catch still appears; worker-direct contained it by other means.
- **A long verification tail.** `worker-direct r2` graded 4/4 yet still tripped
  the 480s wall: the implementation was complete, but the run kept re-reading
  files and re-running an empty `pytest` until the backstop killed it. Runs are
  not yet smooth even when they are correct.

## Why not Groundwire for the exact-text edit

The failing worker fabricates an edit anchor. The fix is to make the anchor a
*verbatim slice of the real file*, not a generated guess — which is exactly the
problem a retrieval + verification layer (Groundwire) solves. It keeps each
file's exact bytes in a span registry and lets the model reference a span by a
handle that is post-filled verbatim ("quoting is an extraction problem, not a
search problem"); its lexical retrieval returns a distinctive identifier
byte-for-byte at 100% recall regardless of corpus size.
We are not using it yet for three reasons, each a design choice rather than an
oversight:

- **Nothing to ground against at decompose time.** The architect splits the
  spec in plan mode *before* the files exist, so grounding belongs at the
  worker's edit, not the up-front plan.
- **The package is a dependency in another repo.** mellum-worker ships
  dependency-free and the remedy architecture adds nothing by default; wiring a
  retrieval layer is a deliberate remedy unit, not a default.
- **It is unmeasured here.** No remedy unit exists, so it would be a conjecture
  with no run behind it.

The lightest grounded-edit remedy needs no dependency at all: require an edit's
`old_string` to be a verbatim slice of a file read in the same turn (a guard or
nudge). Groundwire earns its place when the file or corpus is too large to read
wholesale — the off-GPU, size-invariant case. Either way this is the next
lever, and it is conjecture until a run backs it.

## Decision

- Keep the worker-direct nudge as the **lead**. It is a screen at n=3 on one
  easy prompt via the scratch driver, not a rate — promoting it to a default
  needs a preregistered `run_ladder` run across rungs, and a medium/hard screen
  to check the nudge does not starve a tier that genuinely needs re-derivation.
- All five mechanisms (worker-direct, `guardArgs` to sub-agents, `MELLUM_TURN_CAP`,
  the stall rethink, `guard/exists`) stay **off by default** — `MELLUM_TURN_CAP`
  unset means the 200-call frozen default, `MELLUM_DELEGATE_WORKER_DIRECT` unset
  means no nudge, and `guard/exists` is opt-in like every unit. Shipped
  behaviour is unchanged.
- The next lever is the **architect decomposition / grounded edit**, not more
  turn budget.

## What would falsify this / Risks

- **Falsifies the nudge:** a preregistered ladder run where worker-direct grades
  ≤ default across rungs, or a medium/hard screen where the nudge lowers the
  grade because the worker needed to re-derive. Then drop it.
- **Falsifies the root-cause claim:** a grounded-edit remedy that removes the
  fabricated-anchor loop but leaves the grade unmoved — then the decomposition
  is not the binding constraint and the cause is elsewhere.
- **Risk:** the nudge is tuned on easy/01; a single prompt can flatter one arm.
  n=3 with two DEADLINE reps is thin — the two zeros in `default` could be
  variance as much as signal.
- **Risk:** the `exists` guard gap means the guard reads as "on" while missing
  the most common thrash command; fixing it changes what the guard measures, so
  any future guard screen must note the change.
