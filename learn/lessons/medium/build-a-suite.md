---
title: Build a Suite
tier: medium
number: M8
time: 3 min read · not built yet
track: lessons
position: 8
prerequisites: [lessons/medium/keep-a-plan]
authors: [Andre van Zuydam]
backends: [vllm]
---

# M8 · Build a Suite

A suite proves nothing until its grader fails a build it should fail. You build one in Pi and watch a weak grader pass a broken build, then yours catch it.

!!! abstract "Overview"

    **Questions**

    - What makes a hidden grader trustworthy?
    - How do known-good and known-broken builds test the grader itself?

    **Objectives**

    - Run `qualify` on a weak grader and see it pass the known-broken build.
    - Write a grader that fails known-broken and passes known-good, and see `qualify` pass.

![Build a Suite: a placeholder picture until this lesson has its own](../../assets/illustrations/build-a-suite.webp){ .illustration }

## Problem

**Badge:** `conjecture`

A weak grader passes a wrong build, and every score built on it is wrong in the same direction. Nothing about a green run says whether the grader could have gone red.

## Eval case

**Badge:** `conjecture`

Not built yet. This lesson's own challenge, `learn/challenges/build-a-suite/`, is
planned under the uniform-lessons plan; its before and after lines arrive
with it.

## Evidence of the problem

**Badge:** `conjecture`

None yet: no arm has run on this lesson's challenge, so there is no n to
report.

## Solution

**Badge:** `conjecture`

**Remedy unit:** your grader; the reference is committed with the challenge, and `qualify --grader` swaps yours in.

**Lesson check:** not built yet.

## Validation

**Badge:** `conjecture`

Not run. The lesson check will run the before and after lines on the 6-bit
reference model and record the result here.

## Interpretation

The weakest badge is `conjecture`: this page names a failure and its remedy,
and nothing has been measured yet. Read it as the plan for a lesson, not as a
lesson.

### Run it yourself

The before line, until the challenge and its after line exist:

```bash
uv run python learn/code/harness.py qualify --suites-dir learn/challenges --suite build-a-suite
```

!!! success "Key points"

    - A grader is only as good as the broken build it fails.
    - `qualify` runs known-good and known-broken through the grader; both must come out right.
    - This lesson's challenge, its `--grader` option and its check are not built yet.
