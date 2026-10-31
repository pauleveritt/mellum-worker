---
title: Tell It How to Test
tier: medium
number: M1
time: 4 min read · 45 min to run
track: lessons
position: 1
prerequisites: [lessons/easy/too-many-tools]
authors: [Paul Everitt]
backends: [llamacpp]
---

# M1 · Tell It How to Test

A small model dropped into a workspace has to guess how the project is tested,
and a plausible guess survives several turns. One unit appends the project's
own facts, the test command first, to every request so it does not have to.

!!! abstract "Overview"

    **Questions**

    - What does a small model do when nobody tells it how the project is tested?
    - How do I know the facts actually reached the model?

    **Objectives**

    - Add `context/add-project-facts` and read the block it appends.
    - Count injected requests before counting passes.
    - Recognise a null result, and a lead that is not yet a finding.

![A small robot at a workbench reading an index card pinned above it](../../assets/illustrations/tell-it-how-to-test.webp){ .illustration }

## Problem

**Badge:** `screen`

The model has to infer which command runs the tests, which interpreter to use
and what it may not touch. It usually guesses, and the guess is plausible
enough to survive several turns before anything proves it wrong.

## Eval case

**Badge:** `screen`

**Before:** `--remedy preset:easy`, everything the Easy tier built. **After:**
the same plus `context/add-project-facts`. The lesson's own challenge, a task
whose test command is genuinely unknown, is not built yet; the evidence below
is Bronze, three sessions per arm on llama.cpp, recorded with the older
`worker` (facts on) and `no-facts` (`MELLUM_MODE_FACTS=0`) arms, which differ
only in the block.

## Evidence of the problem

**Badge:** `screen`

All three `no-facts` sessions failed, and all three ended the same way: a
foreground server command with no result after it, then silence until the
harness killed the child at 600 s. The bullet they did not receive is
`- Do not: start servers`. That is a lead, not a finding: n = 3 on one machine,
and the same pathology is what `guard/block-foreground-server` answers with a
guard.

## Solution

**Badge:** `screen`

**Remedy unit:** `context/add-project-facts`; apply it with `--remedy context/add-project-facts`.

**Lesson check:** not built yet. A small challenge of this lesson's own, failing without the remedy and passing with it, is planned; until then the evidence below is the suites'.

The unit reads the first `## Mellum` section of `AGENTS.md`, adds a detected
test command when the section names none, caps the result at 600 characters
and appends it to every user message. What the worker forwarded in those
sessions:

```
Project facts:
- Test command: uv run --frozen python -m pytest tests
- Run Python commands with uv run --frozen.
- Use existing dependencies and test configuration.
- Keep changes scoped to the task; do not weaken existing tests.
- Before reporting completion, run the test command and report its result.
- Do not: start servers
```

## Validation

**Badge:** `screen`

**Lesson check, 2026-10-29** (vLLM host, n = 3 per arm; [lesson check](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lesson-check.md)): with the facts 3 of 3 passed on Bronze, without them 2 of 3: direction only, not a FAIL → PASS, because the arm without the remedy still passes.

The block reached the model on every facts-on request (26/26, 22/22, 11/11)
and on no facts-off request (0/17, 0/48, 0/51), so the arm is real. Passes did
not separate: **1 of 2 valid sessions against 0/3**, a null. One facts-on
session is excluded because the grader was touched during the run.

??? note "The full evidence"

    | Arm | Session | Passed | Requests | Injected | Peak input | Tool errors |
    | --- | --- | --- | --- | --- | --- | --- |
    | `worker` | `9d5483` | **yes** | 26 | 26/26 | 857 | 5 |
    | `worker` | `6e3209` | no | 22 | 22/22 | 13,813 | 2 |
    | `worker` | `7009b6` | **invalid** | 11 | 11/11 | 19,721 | 1 |
    | `no-facts` | `0f2dc0` | no | 17 | **0/17** | 857 | 2 |
    | `no-facts` | `e3136d` | no | 48 | **0/48** | 880 | 17 |
    | `no-facts` | `64c6ec` | no | 51 | **0/51** | 758 | 11 |

    | Suite | Arm | Passes | Turns | Tool errors | Peak input | Wall |
    | --- | --- | --- | --- | --- | --- | --- |
    | Bronze | facts on (`worker`) | 1/2 | 24 | 3.5 | 13,813 | 316 s, 199 s |
    | Bronze | facts off (`no-facts`) | 0/3 | 38.7 | 10.0 | 880 | 139–457 s |

    How the three `no-facts` sessions ended:

    | Session | Last command | Silence before the kill |
    | --- | --- | --- |
    | `0f2dc0` | `uv run uvicorn app:app --reload --port 8001` | 460 s |
    | `e3136d` | `uvicorn app:app --reload --port 8001` | 200 s |
    | `64c6ec` | `uv run --offline python app.py` | 143 s |

    The same day's `worker` sessions reached for servers too, and none of them
    ended a run; the one that started the app backgrounded it. Backend
    `llama-server` 0.7.0 (build 11669), Mellum 2.1 `Q4_K_M`, `-c 50000`
    (`n_ctx` 50,176), `temperature 1`, `top_p 0.95`, `top_k 20`,
    `max_tokens 16384`.

## Interpretation

The weakest badge is `screen`: one suite, three sessions, one machine, and a
null on passes. The facts-on arm spent more peak context, not less. An older
claim, a four-phase build going from 1/12 to 9/12, came from a different
instrument on a different backend and is retired. What holds is narrower: the
block provably reaches the model on every request. What would upgrade this is
the lesson's own challenge, where the test command cannot be guessed.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy preset:easy --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts --repeat 3 --grade
```

!!! success "Key points"

    - `context/add-project-facts` appends the test command and the project's rules to every request.
    - Count injected requests first: the block reached every facts-on request and no facts-off one.
    - Passes did not separate, 1/2 valid against 0/3: a null at n = 3 on one suite.
    - Every facts-off session ended in a foreground server; that is a lead, not a finding.
