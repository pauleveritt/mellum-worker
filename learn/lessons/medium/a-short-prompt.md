---
title: A Short Prompt
tier: medium
number: M2
time: 4 min read · 35 min to run
track: lessons
position: 2
prerequisites: [lessons/medium/tell-it-how-to-test]
authors: [Paul Everitt]
backends: [llamacpp]
---

# M2 · A Short Prompt

Pi's own system prompt is long and general, and a small model can follow the
procedure it describes instead of the files in front of it. One unit swaps it
for the worker's 643-character task prompt, with no procedure in it.

!!! abstract "Overview"

    **Questions**

    - Does the worker's short prompt pass more sessions than Pi's own prompt?
    - What should earn a line in a small model's prompt?

    **Objectives**

    - Add `context/use-short-prompt` and read the prompt it installs.
    - Keep two samples apart rather than pooling them.
    - Recognise a null and say what it does and does not rule out.

![A small robot holding a short note beside a long unused scroll on the floor](../../assets/illustrations/a-short-prompt.webp){ .illustration }

## Problem

**Badge:** `screen`

A prompt that narrates a procedure gives a small model more to follow than the
project needs. It spends turns on the narration and drifts from the files, and
every line is paid for on every request.

## Eval case

**Badge:** `screen`

**Before:** `--remedy preset:easy,context/add-project-facts`. **After:** the
same plus `context/use-short-prompt`. The lesson's own challenge is not built
yet; the evidence below is Bronze, three sessions per arm on llama.cpp,
recorded with the older `worker` (prompt v5) and `no-prompt`
(`MELLUM_WORKER_PROMPT=pi`) arms, which differ only in the prompt.

## Evidence of the problem

**Badge:** `screen`

The argument is the narration; the measurement does not show it. Pi's prompt
passed as often as the short one in the 45-session record (**3/9 against
3/9**) and one session behind it in this run (**1/3 against 2/3**). Its one
passing session here peaked at 20,773 input tokens, against 1,639 and 3,404
for the short prompt's two passes.

## Solution

**Badge:** `screen`

**Remedy unit:** `context/use-short-prompt`; apply it with `--remedy context/use-short-prompt`.

**Lesson check:** not built yet. A small challenge of this lesson's own, failing without the remedy and passing with it, is planned; until then the evidence below is the suites'.

The unit drops every system message and puts `prompts/mellum-worker.md` in
their place: **643 characters**, the test-command facts and the missing-files
line, no procedure. The rule that built it: a line earns its place when a run
says so. Read the file as one page, not as steps.

## Validation

**Badge:** `screen`

**Lesson check, 2026-10-29** (vLLM host, n = 3 per arm; [lesson check](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lesson-check.md)): with the short prompt 3 of 3 passed on Bronze, with Pi's own prompt 1 of 3: direction only, the strongest separation in the check, but the arm without the remedy still passed once.

Not separated. Two samples, kept apart: 2/3 against 1/3 on Bronze in this run,
3/9 against 3/9 across Bronze, Silver and Gold in the 45-session record. The
context saving held in the record (7,834 against 15,167 peak on Bronze) but
not in this run, where the short prompt's losing session peaked at 33,443.

??? note "The full evidence"

    | Sample | With v5 | With Pi's prompt | Context |
    | --- | --- | --- | --- |
    | the 45-session record, Bronze/Silver/Gold, n=3 each | 3/9 | 3/9 | v5 7,834 vs 15,167 peak, Bronze |
    | this run, Bronze only, n=3 | **2/3** | **1/3** | v5 peaks 1,639–33,443; no-prompt 4,762–20,773 |

    | Arm | Session | Passed | Turns | Tool errors | Peak input | Wall |
    | --- | --- | --- | --- | --- | --- | --- |
    | `worker` | 1 | **yes** | 21 | 4 | 1,639 | 185 s |
    | `worker` | 2 | no | 22 | 2 | 33,443 | 275 s |
    | `worker` | 3 | **yes** | 52 | 17 | 3,404 | 405 s |
    | `no-prompt` | 1 | **yes** | 45 | 10 | 20,773 | 486 s |
    | `no-prompt` | 2 | no | 26 | 3 | 4,762 | 419 s |
    | `no-prompt` | 3 | no | 26 | 6 | 4,853 | 179 s |

    | Suite | Arm | Passes | Turns | Tool errors | Peak input | Wall |
    | --- | --- | --- | --- | --- | --- | --- |
    | Bronze | prompt v5 (`worker`) | 2/3 | 31.7 | 7.7 | 33,443 | 288 s |
    | Bronze | Pi's prompt (`no-prompt`) | 1/3 | 32.3 | 6.3 | 20,773 | 361 s |

## Interpretation

The weakest badge is `screen`, and this page is a **null**: the short prompt
did not beat Pi's own at n = 3, nor across three suites. An older claim, that
each removed line was paid for by a pass, rested on ladder ablations that are
no longer cited. What would upgrade this: a long, procedural prompt measured
against v5. A null against Pi's prompt is not a null against a bloated one,
and that comparison has not been run on this backend.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt --repeat 3 --grade
```

!!! success "Key points"

    - `context/use-short-prompt` replaces the system prompt with 643 characters and no procedure.
    - It did not change the pass count: 2/3 against 1/3 here, 3/9 against 3/9 in the record (a null).
    - The context saving held in the record but not in this run.
    - A line earns its place in the prompt when a run says so.
