---
title: Look It Up
tier: medium
number: M5
time: 3 min read · 20 min to run
track: lessons
position: 5
prerequisites: [lessons/medium/run-long-commands-safely]
authors: [Andre van Zuydam]
backends: [omlx]
---

# M5 · Look It Up

A small model writes the API it remembers, and some APIs it never saw: a
library newer than its training, a default it has wrong. One unit adds a
lookup tool that answers from the packages actually installed.

!!! abstract "Overview"

    **Questions**

    - What does a model do with an API it was never trained on?
    - Where can it find the truth without being handed the answer?

    **Objectives**

    - Recognise an API-shaped failure: a wrong default, a missing name, a redirect loop.
    - Add `tool/lookup-library-docs` and see what a `lookup` call returns.

![A small robot on a library ladder pulling down a thick reference book](../../assets/illustrations/look-it-up.webp){ .illustration }

## Problem

**Badge:** `conjecture`

The model fills in an API from memory. When the library is newer than its
training, or the default is not what it remembers, the guess is wrong in a
way that looks right: the code runs, and the behaviour is off.

## Eval case

**Badge:** `conjecture`

**Before:** `--remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands`.
**After:** the same plus `tool/lookup-library-docs`. The lesson's own
challenge, a task that needs an API the model cannot know, is not built yet,
so for now both run on Bronze.

## Evidence of the problem

**Badge:** `conjecture`

The case the extension was written for: FastAPI's `RedirectResponse` defaults
to 307, so a POST that redirects loops back to a POST, where the spec needs
303. The ladder also runs on Python 3.15, which the model was never trained
on. Neither failure has a before-and-after count on the suites.

## Solution

**Badge:** `conjecture`

**Remedy unit:** `tool/lookup-library-docs`; apply it with `--remedy tool/lookup-library-docs`.

**Lesson check:** not built yet. A small challenge of this lesson's own, failing without the remedy and passing with it, is planned; until then the evidence below is the suites'.

The unit registers a `lookup` tool. A query runs a BM25 search over the
installed packages in the workspace's environment (every class and function
with its signature and docstring) and returns the top matches. The index is
warmed when the session starts and rebuilt when the packages change.

```json
{ "query": "RedirectResponse status code default 303", "k": 4 }
```

It grounds on the library docs a developer would have, never on the task's
solution or the hidden grader.

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. The unit is unit-tested but has no
before-and-after record on the suites, and nothing yet shows how often the
model calls `lookup` unprompted. This page says FAIL → PASS only once its
challenge has shown it.

## Interpretation

The weakest badge is `conjecture`: neither the pathology's rate nor the fix is
measured here. A tool only helps if the model calls it at the right moment, so
the lesson's challenge has to read `lookup` calls in the trace as well as the
grade.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands,tool/lookup-library-docs --repeat 3 --grade
```

!!! success "Key points"

    - A model writes the API it remembers, and a newer library or a wrong default makes that guess quietly wrong.
    - `tool/lookup-library-docs` answers from the installed packages, not from memory.
    - It grounds on library docs only, never the task's solution or the grader.
    - Not measured as a lesson yet: read the trace for `lookup` calls as well as the grade.
