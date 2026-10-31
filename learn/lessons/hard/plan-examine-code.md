---
title: Plan, Examine, Code
tier: hard
number: H1
time: 4 min read · about 1.5 h to run
track: lessons
position: 1
prerequisites: [lessons/medium/check-before-finishing]
authors: [Andre van Zuydam]
backends: [vllm]
---

# H1 · Plan, Examine, Code

One agent that plans, writes the test and builds the code in the same breath
does all three badly. The flow splits them into roles the model calls as
tools, one phase at a time, so each call has one small job.

!!! abstract "Overview"

    **Questions**

    - What goes wrong when one session builds a multi-phase app at once?
    - What does it change to make plan, examine and code separate tools?

    **Objectives**

    - Name the flow's six tools and the order the driver calls them in.
    - Run the same suite in one session and through `flow_run.py`, and compare.
    - Read a flow result in hidden checks passed, not sessions passed.

![Three robots at three desks in a row: one drawing a plan, one holding up a sheet, one at work](../../assets/illustrations/plan-examine-code.webp){ .illustration }

## Problem

**Badge:** `screen`

Silver has four phases and Gold seven. Handed the whole task, one session has
to hold every phase in its context, decide its own test and judge its own
work. A small model can narrow the task to what it can hold and write a test
that matches what it built ([H3](dont-trust-the-self-exit.md) shows one), and nothing stops
a later phase breaking an earlier one.

## Eval case

**Badge:** `screen`

**Before:** `preset:medium`, one session for the whole task, through
`harness.py`. **After:** the same model driven by `learn/code/flow_run.py` in
its default `--flow-mode forced`: the task is split into phases, and each
phase runs the roles as tools. Silver is the level to watch; Bronze has one
phase, so the split has less to do there.

## Evidence of the problem

**Badge:** `screen`

On the pinned vLLM baseline host (RTX A6000, Mellum 2.1 BF16, vLLM 0.32.0, Pi
1.3.0) the baseline's `bare` arm passed Bronze 1/3, Silver 1/3 and Gold 0/3
sessions. That is bare Pi, not `preset:medium`; the tier's own before has not
been run on this host.

## Solution

**Badge:** `screen`

**Remedy unit:** `workflow/spec-driven-flow`; it runs through `learn/code/flow_run.py`, which loads it for you.

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

The driver gets only the phase tools and `read`, and every tool takes no
arguments: the task lives in `plan/TASK.md`, so the model never writes a long
tool argument.

1. `plan()` writes `TODO.md`, a north star and a checklist; `review_plan()`
   answers PASS or REDO.
2. `examine()` writes this phase's acceptance test from the spec, before any
   code. It is frozen as the gate ([H2](frozen-gates-and-checkpoints.md)).
3. `code()` builds to pass that test; `review_code()` answers PASS or REDO.
4. `test()` runs the gate. It is the only exit.

## Validation

**Badge:** `screen`

One forced flow run per level on the same host, 2026-10-28/29, n = 1: Bronze
4/4 hidden checks (a full pass), Silver 13/18, Gold 30/34. Gold reached phase
7 of 7, further than any setup recorded so far. A rerun with three gate fixes
([H2](frozen-gates-and-checkpoints.md)) gave Bronze 4/4, Silver 18/18 and Gold 30/34.

The units differ (checks passed here, sessions passed in the baseline), and
each level ran once, so this is not a rate. Gold's four misses in the first
run were the model's: its migration was invalid SQL for six rounds.

## Interpretation

The weakest badge is `screen`: n = 1 per level, one host. The flow got further
than one session did, and Silver's 13/18 became 18/18 only after harness
fixes, which is the next lesson's subject. The roles help because each call
has a smaller job, not because the model got better. The flow is opt-in and
unmeasured as a remedy against `preset:medium`.

### Run it yourself

Before, then after, on Silver. Point `flow_run.py` at your server with
`--base-url` and `--model` if it differs from the defaults.

```bash
uv run python learn/code/harness.py run --suite medium --remedy preset:medium --repeat 3 --grade
uv run python learn/code/flow_run.py --suite medium
```

!!! success "Key points"

    - The flow makes plan, examine, code and test separate tools, called one phase at a time.
    - The acceptance test is written from the spec before any code, and running it is the only exit.
    - One forced run per level reached Bronze 4/4, Silver 13/18 and Gold 30/34 hidden checks; not a rate.
