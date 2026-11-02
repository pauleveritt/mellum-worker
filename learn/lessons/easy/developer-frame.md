---
title: A Developer's Frame
tier: easy
number: E2
time: 4 min read · 10 min to run
track: lessons
position: 2
prerequisites: [lessons/easy/name-the-layout]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E2 · A Developer's Frame

The model that knows where the files go can still ship a careless one. A short
role — a meticulous developer working to a spec — steadies the hand.

!!! abstract "Overview"

    **Questions**

    - Why does a model that gets the layout right still fail on small mistakes?
    - Can a role prompt cut careless failures without changing the task?

    **Objectives**

    - Run Easy with the layout line and watch a run trip on an unchecked typo.
    - Add `prompt/python-developer` and see the careful version of the same run.

![A small robot in overalls reading a spec sheet with a careful, measured eye](../../assets/illustrations/a-short-prompt.webp){ .illustration }

## Problem

**Badge:** `screen`

With the layout named, the model builds in the right place — and still finishes
on a mistake it never checked. A stray `if __name__ == "main__":` with the
underscores wrong, a declared-done it never ran. The work has the right shape
and a careless flaw inside it. Nothing frames the model as the kind of developer
who reads twice and runs before it says done.

## Eval case

**Badge:** `screen`

**The condition:** Easy Phase 1, the same home page. **Before:** Vanilla Pi plus
`prompt/name-the-layout`. **After:** the same plus one more unit,
`prompt/python-developer`. The grader is the Easy suite's hidden tests.

## Evidence of the problem

**Badge:** `screen`

With the layout line alone the ladder sat at 2 of 3: the layout is right, the
finish is not. The failing runs are not in the wrong place, they are the right
place built carelessly — a typo shipped unchecked, a finish declared without a
run. The gap is not where the file goes, it is how the work is done.

## Solution

**Badge:** `screen`

**Remedy unit:** `prompt/python-developer`; switch it on live in Pi with `/remedy on prompt/python-developer`, or pass `--remedy prompt/python-developer` to a graded run.

**Lesson check:** 2/3 rose to 3/3 at n=3 on the local host, a screen
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

The unit prepends one line to the system prompt: you are an experienced,
meticulous python developer working in a spec driven paradigm. It names no
suite, file or route. A role is cheap and it is agnostic — it changes how the
model works, never what the task is.

## Validation

**Badge:** `reference-run`

Adding the role took `name-the-layout` from **2/3** to **3/3** at n=3, at 14 to
20 turns. At n=6 the same stack read **4/6** — the screen at n=3 flattered it, as
screens do
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
The role helps; it does not finish the job on its own. A screen is a lead, never
a rate, and a strong lead at small n is still a lead.

## Interpretation

The weakest badge is `screen`. A role prompt makes the model *attempt* care, but
care comes out as reading files or launching a server, not always as running the
real check. That is the limit of a frame: it points the model at diligence
without defining what diligence does. The next lesson names that — verify every
requirement, and run the test — which is what carries the stack the rest of the
way. The role is the posture; verification is the act.

### Run it yourself

With the layout line, then with the role added:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout --grade --repeat 3 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout,prompt/python-developer --grade --repeat 3 --deadline 600
```

!!! success "Key points"

    - The right layout can still ship a careless, unchecked mistake.
    - `prompt/python-developer` frames the model as a meticulous, spec-driven developer.
    - It lifted the screen 2/3 → 3/3, but n=6 read 4/6 — a lead, not a settled rate.
