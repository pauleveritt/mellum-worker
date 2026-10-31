---
title: Start Here
number: S0
time: 3 min read · 1 min to run
track: lessons
position: 0
prerequisites: [getting-started/suite]
authors: [Andre van Zuydam]
backends: [none]
---

# S0 · Start Here

This lesson teaches how every other lesson works, by being one: a before run
that fails, a change, and an after run that passes. It needs no model and no
GPU, because a stand-in plays the model, so both runs finish in seconds.

!!! abstract "Overview"

    **Questions**

    - What do a lesson's before and after mean, and how do I run them?
    - How do I read whether a run passed, and why it failed?

    **Objectives**

    - Run a before line and an after line, and read FAIL then PASS.
    - Find the reason for a failure in the result, then in `run.json`.
    - Switch a remedy on by hand with `/remedy`.

![A small robot reading an open map beside a row of stepping stones leading away](../assets/illustrations/start-here.webp){ .illustration }

!!! tip "Take this lesson in Pi"

    Open a terminal in your checkout of this repository and start Pi, the one
    you installed in [Getting Started](../getting-started/base-pi-on-llamacpp.md):

    ```bash
    cd mellum-worker
    pi
    ```

    The first time, type `/trust`, then quit Pi (`Ctrl+D`) and start it
    again, so it loads this project's extensions. Then type:

    ```text
    /lesson S0
    ```

    Pi shows this lesson one step at a time. Press `→` or `Enter` for the
    next step and `←` to go back; on the Eval case and Solution steps press
    `r` to run. `Esc` leaves, and `/lesson` brings you back to the next one.

## Problem

**Badge:** `conjecture`

Every lesson names one thing a small model gets wrong and shows one change
that fixes it. To trust the fix you have to see both states, with and without
it, and read the result yourself. Here the "model" writes `add(a, b)` as
`a - b`, so the hidden test fails.

## Eval case

**Badge:** `conjecture`

**Before:** a stand-in for the model that writes the wrong answer
(`fake-pi-wrong.sh`). **After:** a stand-in that writes the right one
(`fake-pi.sh`). Both run the same small task through the real harness and
its hidden grader. In every other lesson, before and after differ by one
`--remedy` unit and the model is real; nothing else changes.

## Evidence of the problem

**Badge:** `conjecture`

Run the before line (in `/lesson`, press `r` on this step's Eval case). The
result reads `FAIL`, one line per session, with the reason: here, "the
hidden tests failed". Each session also leaves a `run.json`: `passed`,
`checks_ran`, `stalled` and `missing_checks` say what happened, in that
order of importance. Reading a failed session is the first skill: every
later lesson adds one remedy for one named failure. No arm of this lesson has
run, so there is no n to report.

## Solution

**Badge:** `conjecture`

**Remedy unit:** none: in this lesson the change is the stand-in itself; every
other lesson names a unit from the remedies list.

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

Real lessons apply their remedy in one of two ways, and you can use both:

1. **On the command line:** the after line adds `--remedy <unit>`, as every
   lesson's Run it yourself shows.
2. **By hand, in Pi:** type `/remedy` to pick a unit, or
   `/remedy on guard/break-repeat-loops`, and the next tool call in your
   session is covered by it. `/remedy off …` takes it away again.

## Validation

**Badge:** `conjecture`

Run the after line (`r` on the Solution step). The result reads `PASS`. One
session is a demonstration; a lesson's real test, its lesson check, runs each
line at a preregistered n and must fail every session before and pass after.
No arm has run, so there is no n to report.

## Interpretation

### Reading a real failure

Read a failed session in this order:

1. `run.json`: `passed`, then `checks_ran` (did the checks even run?), then
   `stalled` (which command hung?), `empty_finals` and `tool_errors`.
2. `trace.jsonl`: the last few tool calls before the end. The failure is
   almost always there.
3. The [remedies list](index.md#pathologies-and-their-remedies): find the row
   whose pathology matches, and go to its lesson.

Nine bare sessions on the vLLM host (Bronze, Silver and Gold, n = 3 each,
2026-10-29) show why the order matters. Three passed. The six failures, by
what the record shows:

| What the record shows | Sessions | The failure |
| --- | --- | --- |
| `stalled` names `python app.py` or `uvicorn …` | 4 (3 of them failed) | a server started in the foreground hung the session |
| `checks_ran: false` without a stall (one wrote `main.py`) | 2 | the hidden checks import a module that was never created |
| `empty_finals: 1` and 21 `tool_errors` | 1 | it kept retrying failing calls, then ended a turn with nothing |

A session can show more than one. That table is a `screen`, nine sessions on
one host, though the foreground-server stall also showed on a second, the
local 6-bit lessons smoke ([note](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-local-lessons-smoke.md)). Read
`checks_ran` and `stalled` before `failed_checks`: a session whose checks
never ran reports every check missing for a reason that has nothing to do
with the checks.

### The loop

That is the whole loop every lesson repeats: name the failure, run before,
add one change, run after, and read the record rather than the model's own
claim of success. The only differences later are a real model, a real task,
and a real remedy, so the runs take minutes instead of seconds.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suites-dir learn/code/tests/fixtures/suites --suite add --pi-binary learn/code/tests/fixtures/fake-pi-wrong.sh --repeat 1 --grade
uv run python learn/code/harness.py run --suites-dir learn/code/tests/fixtures/suites --suite add --pi-binary learn/code/tests/fixtures/fake-pi.sh --repeat 1 --grade
```

!!! success "Key points"

    - Every lesson shows two states of one command: before, and after one change.
    - Read the result line first, then `run.json`: `passed`, `checks_ran`, `stalled`, `missing_checks`.
    - Apply a remedy with `--remedy` on the command line, or `/remedy on` by hand in Pi.
    - Name a real failure before fixing it: `checks_ran` and `stalled` first, then the trace's last calls.
