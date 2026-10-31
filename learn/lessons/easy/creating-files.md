---
title: Creating Files
tier: easy
number: E5
time: 3 min read · 20 min to run
track: lessons
position: 5
prerequisites: [lessons/easy/searching]
authors: [Andre van Zuydam]
backends: [omlx]
---

# E5 · Creating Files

A small model asked to change a few lines sometimes calls the write tool, which replaces the whole file, and everything else in it is gone. One guard refuses write on a file that exists and points the model to edit instead.

!!! abstract "Overview"

    **Questions**

    - What is the difference between `write` and `edit`?
    - How do I stop a model replacing a whole file to change a fragment?

    **Objectives**

    - Tell `write` (the whole file) from `edit` (an exact old text and a new text).
    - Add `guard/refuse-whole-file-rewrite` and see `write` on an existing file refused.

![A small robot holding up a single sticky note beside a thick open book whose pages are blank](../../assets/illustrations/creating-files.webp){ .illustration }

## Problem

**Badge:** `screen`

The tools: `write` takes a path and the file's whole content; `edit` takes a path, the exact old text and the new text. Asked to change three lines, a small model sometimes calls `write` with just those lines, and everything else in the file is gone.

## Eval case

**Badge:** `conjecture`

**Before:** bare Pi with what the earlier Easy lessons added
(`guard/break-repeat-loops, guard/stay-in-workspace`). **After:** the same plus `guard/refuse-whole-file-rewrite`. The
lesson's own challenge, a task built to provoke this failure, is not built
yet, so for now both run on Bronze.

## Evidence of the problem

**Badge:** `screen`

Recorded once: a 942-line file became 2 lines under a write-only tool set. The guard has stayed dormant in the worker because the measured models anchor `edit` reliably; it is a cheap safety net, not a hot path.

## Solution

**Badge:** `screen`

**Remedy unit:** `guard/refuse-whole-file-rewrite`; apply it with `--remedy guard/refuse-whole-file-rewrite`.

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

The guard refuses a `write` to a path that already exists, and says why: `write` replaces the entire file, so use `edit` with the exact old text and the new text. A `write` to a new file passes.

```ts
if (call.toolName !== "write" || !exists(path)) return undefined;
return { block: true, reason: `${path} exists; write replaces the entire file. Use edit …` };
```

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. This page says FAIL → PASS only once its
challenge has shown it.

## Interpretation

The weakest badge is `conjecture`: the failure is recorded once and rare on current models. The guard also blocks a deliberate full rewrite, which a careful model may want; the model then has to delete and recreate, or edit. That trade is why it is a lesson to measure, not a default to assume.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy guard/break-repeat-loops,guard/stay-in-workspace --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy guard/break-repeat-loops,guard/stay-in-workspace,guard/refuse-whole-file-rewrite --repeat 3 --grade
```

!!! success "Key points"

    - `write` replaces a whole file; `edit` changes exactly the text you name.
    - `guard/refuse-whole-file-rewrite` refuses `write` on an existing file and points to `edit`.
    - The failure is rare on current models, so this lesson has to earn the guard.
