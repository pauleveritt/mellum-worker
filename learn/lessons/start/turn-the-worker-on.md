---
title: Turn the Worker On
number: S1
time: 3 min read · 1 min to run
track: lessons
position: 1
prerequisites: [getting-started/extensions]
authors: [Andre van Zuydam]
backends: [none]
tryit: "`/mellum on` — switch the worker in | Ask it to do a task, e.g. `Do the task in TASK.md` | `/mellum off` — switch back and read the span summary"
---

# S1 · Turn the Worker On

The small model is cheap and local, but switching your session to it by hand —
model, tools, prompt — is fiddly. `/mellum on` does all of it in one word, and
`/mellum off` puts your session back.

!!! abstract "Overview"

    **Questions**

    - How do I hand my session to the small model, and take it back?
    - What does turning the worker on actually change?

    **Objectives**

    - Switch the worker on for a run of related tasks, then off again.
    - Name the four things the mode changes, and read the span summary.

![A small robot clicking a modular toolbox attachment onto its arm, with spare attachments laid out on a table](../../assets/illustrations/worker-extension.webp){ .illustration }

## Problem

You want the local Mellum model to do a bounded piece of work, not the big
model you usually drive. By hand that means `/model` to switch, re-pointing
your tools, pasting the worker prompt, and remembering to undo all three
afterwards. Miss a step and the small model runs with the wrong tools or the
wrong prompt, and every read and edit it makes lands in your own context.

## Eval case

`/mellum on` is the switch. In one command it: swaps the session's model to
Mellum, narrows the active tools to the worker set (`read`, `grep`, `find`,
`ls`, `bash`, `edit`, `write`), swaps in the worker prompt, and marks the
start of a **span** so the run can be summarised later. `/mellum off` restores
the model and tools you had before and prints a one-line summary of the span.

## Evidence of the problem

Start Pi on your usual big model and watch what a bare switch costs: `/model`
changes the model but leaves your full tool set and your conversation in play,
so the small model sees tools it uses badly and a context far larger than the
task. There is no marker, so nothing downstream can tell where the small
model's work began or ended.

## Solution

In Pi, turn it on, work, turn it off:

```text
/mellum on
Fix the failing test in test_export.py
/mellum off
```

The worker stays on across turns, so you can send several related tasks before
switching back. Auto-compaction is refused while the mode is on, so your
context is not rewritten under the small model — run `/mellum off` before a
long main-model turn. If Pi has no previous model to restore to, `/mellum off`
warns and stays on; pick one with `/model` first.

## Validation

After `/mellum on`, Pi's model indicator shows Mellum and the active tools are
the worker set. After `/mellum off`, you are back on your previous model and
tools, and the summary line reports the span: how many turns, files written,
commands run. That summary is your proof the switch and the restore both
happened.

## Interpretation

Reach for `/mellum on` when you have a run of small, bounded edits for the
local model and want to stay in one session. It is the manual twin of
[S2 · Run One Task](run-one-task.md), which does the same switch for a single
task and switches back on its own. The compaction refusal is deliberate: it
keeps the mode's own start marker intact, so a later `/mellum last` or
`/mellum learn` can still find the span.

### Run it yourself

Start Pi in your checkout; then type the commands above.

```bash
pi
```

!!! success "Key points"

    - `/mellum on` switches model, tools and prompt and marks the span start; `/mellum off` restores and summarises.
    - The worker stays on across turns — send several tasks, then switch back.
    - Auto-compaction is refused while on, so `/mellum off` before a long main-model turn.
    - No previous model to restore means `/mellum off` warns and stays on; set one with `/model` first.
