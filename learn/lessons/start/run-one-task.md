---
title: Run One Task
number: S2
time: 3 min read · 1 min to run
track: lessons
position: 2
prerequisites: [start/turn-the-worker-on]
authors: [Andre van Zuydam]
backends: [none]
tryit: "`/mellum Do the task in TASK.md` — one shot | Read the handoff block it leaves, then run the tests yourself"
---

# S2 · Run One Task

For a single piece of work you do not want to switch on, do the task, and
switch off by hand. `/mellum <task>` is the one-shot: it switches to the small
model, runs the task, and switches back when the work settles.

!!! abstract "Overview"

    **Questions**

    - How do I hand the small model one task without staying in its mode?
    - What does my main model see when the worker is done?

    **Objectives**

    - Delegate a single task with `/mellum <task>` and read the handoff.
    - Run the same one-shot headlessly from the terminal.

![Two robots joined by a growing pile of paper tape, beside a single small card passed hand to hand](../../assets/illustrations/the-handoff.webp){ .illustration }

## Problem

Most delegations are one task: fix this test, write this file, run this
command. Turning the worker on and off around each one is overhead, and if the
small model's every read, edit and command flows back into your context, one
task can bury the conversation you were having with the big model.

## Eval case

`/mellum <task>` is one-shot delegation. It switches to Mellum, runs the task
as its own span, and switches back to your model when the session settles —
no `/mellum off` needed. With the handoff collapse in place (the
`delegate/collapse-handoffs` remedy), your main model sees **one handoff block**
for the whole span — a summary line, the files written, the commands run, the
last output, and Mellum's reply — instead of every intermediate step.

## Evidence of the problem

Delegate a task by hand without the one-shot and watch two costs. First, you
own the switch-back: forget `/mellum off` and your next big-model prompt runs
on the small model. Second, without the handoff collapse the parent context
grows by every tool call the worker made — the paper tape in the picture — so
a three-file task can add dozens of messages you never needed to read.

## Solution

In Pi, give the task straight after the command:

```text
/mellum Fix the failing test in test_export.py and run the whole file
```

Mellum does the work and your session returns to its previous model on its
own. To run one task without an interactive session at all, use Pi's headless
flag:

```text
pi -p "/mellum Fix the failing test in test_export.py"
```

## Validation

When the span settles you are back on your own model, and the conversation
holds one handoff block for the task, not the worker's step-by-step trace.
Read the block's summary line and files-written list to see what changed, then
run the tests yourself — the handoff is the worker's account, not proof.

## Interpretation

Use `/mellum <task>` for a single bounded task and `/mellum on` (see
[S1](turn-the-worker-on.md)) when you have several in a row. The handoff block
is what makes delegation cheap: it is produced by the `delegate/collapse-handoffs`
remedy, so if your preset does not load it you will see the worker's full
trace instead. Trust the block to tell you *what* happened, and the tests to
tell you whether it is *right*.

### Run it yourself

Run one task headlessly against your local server:

```bash
pi -p "/mellum Fix the failing test in test_export.py"
```

!!! success "Key points"

    - `/mellum <task>` switches to Mellum, runs the one task, and switches back on its own.
    - With `delegate/collapse-handoffs` the parent sees one handoff block, not every step.
    - `pi -p "/mellum <task>"` runs the one-shot headlessly.
    - The handoff says what happened; the tests say whether it is right.
