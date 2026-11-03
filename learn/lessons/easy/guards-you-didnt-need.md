---
title: Guards You Didn't Need
tier: easy
number: E4
time: 5 min read · 15 min to run
track: lessons
position: 4
prerequisites: [lessons/easy/verify-the-spec]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E4 · Guards You Didn't Need

The temptation on a hard problem is to add machinery — a guard, an enforcement
gate. The scientific move is to measure whether it fires. On Easy, the machinery
sat silent and the prompts did the work.

!!! abstract "Overview"

    **Questions**

    - How do I tell a guard is earning its place and not just riding along?
    - Why did an enforcement gate make a passing stack worse, not better?

    **Objectives**

    - Read `guard_blocks` in `run.json` and find the guard that fired 0 times.
    - Stack the NCM gate on the 6/6 set and watch it add nothing — and cost a rep.

![A small robot watching a row of alarm bells that never ring while it works](../../assets/illustrations/evidence.webp){ .illustration }

## Problem

**Badge:** `screen`

A tier looks hard, so you reach for a guard, then a gate that re-runs a test and
sends the model back. It feels safer. But a unit that never fires buys nothing,
and a gate that only acts when the worker finishes cannot help a worker that
never does. The danger is a stack that passes *with* the machinery, so the
machinery takes the credit the prompts earned.

## Eval case

**Badge:** `screen`

**The condition:** the Easy set that passes 6/6 — `preset:easy`. **The guard:**
`guard/foreground-server`, in the set, refusing a foreground server start. **The
gate:** the mediated acceptance gate (`mellum-acceptance` derives a structural
test from the spec; `mellum-verify` re-runs it at settle and re-dispatches a red
one), loaded on top with `--extension`. The grader is the Easy hidden tests;
`run.json` records `guard_blocks` and each gate firing.

## Evidence of the problem

**Badge:** `screen`

Across every n=6 run, `guard/foreground-server` fired **0 times** — the model
never tried the foreground server the guard refuses, so the guard sat silent
while the prompts carried the pass. Stacking the NCM gate on the 6/6 set gave
**5/6**, not better: the gate fired **0 times** too, because the prompts already
met its contract before it checked. The one loss spun **66 turns to the deadline
with no settle attempt**, so the gate — which acts only at finish — never got a
turn, and the run shipped without the HTML5 doctype its own contract checks for.

## Solution

**Badge:** `screen`

**Remedy unit:** `guard/foreground-server`; switch it on live in Pi with `/remedy on guard/foreground-server`, then read its firing in the run record — `--remedy preset:easy` versus the same with the gate's two extensions.

**Lesson check:** guard 0× across six reps; NCM 5/6 with the gate at 0×
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

The move is not to add machinery and hope. It is to add one unit, measure
whether it fires and whether it moves the rate, and keep only what earns its
place. A guard that never speaks and a gate that never bites are not safety —
they are weight, and on the spinning rep the gate was weight that could not even
reach the failure.

## Validation

**Badge:** `reference-run`

Two independent n=6 runs agree: the prompt lines pass Easy, and the enforcement
around them is inert. `guard/foreground-server` blocked nothing in either; the
NCM gate re-dispatched nothing and read 5/6, its one loss a run it structurally
could not touch
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
NCM is a finish-time gate, not a watchdog — blind to the failure mode that never
settles. Its payoff is a harder tier, where the prompts do not already pass and a
settled "done" hides a real miss.

## Interpretation

The weakest badge is `screen`. The cheapest thing that passes is the right thing.
On Easy that is three prompt lines; the guard and the gate add nothing you can
measure, and a gate can even trap a struggling rep in a loop it cannot finish.
This is the method, not a verdict against guards — a guard earns its place on the
tier where its pathology actually appears. Measure the firing, read the rate, and
reach for enforcement only where guidance stops being enough.

### Run it yourself

The 6/6 set, then the same with the NCM gate stacked on:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy preset:easy --grade --repeat 6 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy preset:easy --extension extensions/mellum-acceptance.ts --extension extensions/mellum-verify.ts --grade --repeat 6 --deadline 600
```

!!! success "Key points"

    - A unit that never fires earns nothing; read `guard_blocks` to see it.
    - The NCM gate acts only at finish, so it cannot save a worker that never settles.
    - On Easy the prompts pass; reach for enforcement only where guidance stops being enough.
