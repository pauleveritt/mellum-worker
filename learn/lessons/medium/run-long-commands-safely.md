---
title: Run Long Commands Safely
tier: medium
number: M4
time: 3 min read · 20 min to run
track: lessons
position: 4
prerequisites: [lessons/medium/nudge-an-empty-turn]
authors: [Andre van Zuydam]
backends: [omlx]
---

# M4 · Run Long Commands Safely

Some commands never return on their own (a server, a watcher, a dev reload),
and run in the foreground one holds the session until its deadline. One unit
lets the command run in the background and hands back what it printed.

!!! abstract "Overview"

    **Questions**

    - Why does a small model's "let me check it runs" hang the whole session?
    - How can a long command run without the session waiting on it?

    **Objectives**

    - Recognise a hung command in a trace: a call with no result, then silence.
    - Add `tool/background-long-commands` and read the output it returns instead.

![A small robot with a clipboard walking away from a machine that keeps running on its own](../../assets/illustrations/run-long-commands-safely.webp){ .illustration }

## Problem

**Badge:** `screen`

A generated web app often ends with `uvicorn.run(...)`, so a model that checks
its work with `python app.py`, `uvicorn` or `flask run` starts a process that
never exits. `bash` waits for it, the model waits for `bash`, and the session
burns its time on silence.

## Eval case

**Badge:** `conjecture`

**Before:** `--remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn`.
**After:** the same plus `tool/background-long-commands`. The lesson's own
challenge, a task that invites starting a server or watcher, is not built yet,
so for now both run on Bronze.

## Evidence of the problem

**Badge:** `screen`

The hang is recorded. In the nine bare sessions of 2026-10-29 on the vLLM
host, four named a foreground server in `stalled` (see
[S0](../start-here.md#reading-a-real-failure)), and all three facts-off sessions in
[M1](tell-it-how-to-test.md) ended in one. It reproduced on a second host and
quantization: in the 2026-10-29 local 6-bit MLX lessons smoke
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-10-29-local-lessons-smoke/README.md)),
two of the three bare `build-a-harness` sessions hit the 120-second cutoff on
`uvicorn main:app …`, one cycling ports 8000, 8001 and 8002. The Easy tier's
guard, `guard/block-foreground-server`, refuses the start; this unit lets the
command run instead.

## Solution

**Badge:** `conjecture`

**Remedy unit:** `tool/background-long-commands`; apply it with `--remedy tool/background-long-commands`.

**Lesson check:** not built yet. A small challenge of this lesson's own, failing without the remedy and passing with it, is planned; until then the evidence below is the suites'.

On each `bash` call the unit matches the command against known launchers
(`uvicorn`, `gunicorn`, `flask run`, `http.server`, `--reload`, `npm run dev`,
`python app.py` and others) and rewrites a match in place: run it in a
subshell in the background, wait four seconds, print what it produced, and
return. The model sees the startup output and a note to verify behaviour in
process with a test client rather than wait on the server.

```ts
const launcher = blockingLauncher(command);
if (!launcher) return undefined;
(input as Record<string, unknown>).command = wrap(command);
```

It never blocks a call; a short command passes through untouched.

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. The unit is unit-tested but has no
before-and-after record on the suites, and how it combines with the Easy
tier's server guard, which also acts on these calls, is not measured either.
This page says FAIL → PASS only once its challenge has shown it.

## Interpretation

The weakest badge is `conjecture`: the pathology is recorded, the fix is not
measured. Backgrounding keeps what the model wanted (the startup output, a
running app) where a refusal only says no; whether that helps it finish is the
question this lesson's challenge has to answer.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn,tool/background-long-commands --repeat 3 --grade
```

!!! success "Key points"

    - A server or watcher run in the foreground holds the session until its deadline.
    - `tool/background-long-commands` runs it in the background and returns its startup output.
    - It rewrites only known launchers and never blocks a call.
    - Not measured as a lesson yet: the hang is recorded, the fix is `conjecture`.
