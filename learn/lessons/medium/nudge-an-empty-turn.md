---
title: Nudge an Empty Turn
tier: medium
number: M3
time: 4 min read · 60 min to run
track: lessons
position: 3
prerequisites: [lessons/medium/a-short-prompt]
authors: [Paul Everitt]
backends: [llamacpp]
---

# M3 · Nudge an Empty Turn

A small model can end a turn having said nothing and called no tool, part-way
through the task, and the session stops there. One unit answers that empty
turn with a short nudge, at most three times.

!!! abstract "Overview"

    **Questions**

    - What happens when the model ends a turn having said nothing?
    - Does the nudge actually fire on the suites?

    **Objectives**

    - Add `nudge/nudge-empty-turn` and read how it is bounded.
    - Tell the empty turn it answers (`stop`) from the ones it does not (`error`, `length`).
    - Read the `Nudges` fire count before the pass count.

![A small robot with an empty speech bubble being tapped on the shoulder by a guard](../../assets/illustrations/nudge-an-empty-turn.webp){ .illustration }

## Problem

**Badge:** `screen`

Sometimes the model ends a turn with no text and no tool call. Nothing is wrong
with the request; the model is simply not finished, and without help the
session ends there with the work half done.

## Eval case

**Badge:** `screen`

**Before:** `--remedy preset:easy,context/add-project-facts,context/use-short-prompt`.
**After:** the same plus `nudge/nudge-empty-turn`. The lesson's own challenge
is not built yet; the evidence below is Bronze, five sessions per arm on
llama.cpp, recorded with the older `worker` (nudge on) and `no-nudge` arms.
An arm is only an arm if the thing it removes fires, so the reading is the
`Nudges` count, not the passes.

## Evidence of the problem

**Badge:** `screen`

**The nudge never fired.** In ten Bronze sessions the count was zero in both
arms. Every empty final had a reason the unit is not built to answer: `error`,
a 51,697-token request against a 50,176-token window, or `length`, the output
cap spent. None ended by `stop` with nothing said, the one case it answers.
A later Bronze pairing recorded zero fires across nine sessions in three arms.

## Solution

**Badge:** `screen`

**Remedy unit:** `nudge/nudge-empty-turn`; apply it with `--remedy nudge/nudge-empty-turn`.

**Lesson check:** not built yet. A small challenge of this lesson's own, failing without the remedy and passing with it, is planned; until then the evidence below is the suites'.

When a turn ends by `stop` with no text and no tool call, the unit restates
the completion fact and asks for one more turn. The whole bound is one
counter, and it stops asking after the third:

```ts
export function createEmptyFinalNudge(max: number): (message: MessageLike) => Continuation | undefined {
	let used = 0;
	return (message) => {
		if (!isEmptyAssistantTurn(message) || used >= max) return undefined;
		used += 1;
		return {
			entries: [{ type: "custom_message", customType: "mellum-guard", content: NUDGE_TEXT, display: true }],
			continue: true,
		};
	};
}
```

An aborted turn (`error`) is deliberately not continued, and a capped turn
(`length`) never matches. The code is in
[`extensions/mellum-guards.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/176922f/extensions/mellum-guards.ts#L83-L93).

## Validation

**Badge:** `screen`

**Lesson check, 2026-10-29** (vLLM host, n = 3 per arm, 5 for this page; [lesson check](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lesson-check.md)): with the nudge 4 of 5 passed on Bronze, without it 5 of 5: it does not hold, and the arm without the remedy did slightly better.

### Evidence of the solution

The arms are **void for its question**. Two arms whose guard never fires do
not differ in behaviour, so the 2/5 against 3/5 below is one policy scoring
differently in two samples, not a null. One apparent fire on Silver turned out to be a
counting bug (four prompts, four Pi processes, one empty final counted as
continued by the next prompt), and one test now pins each side.

??? note "The full evidence"

    | Run | Arm | Passes | Turns, mean | Tool errors, mean | Nudge fires |
    | --- | --- | --- | --- | --- | --- |
    | guard screen, Bronze, n=5 | `worker` | 2/5 | 32.6 | 4.2 | **0** |
    | guard screen, Bronze, n=5 | `no-nudge` | 3/5 | 34.6 | 4.6 | **0** |

    | Sessions | Empty final ended by | Guard's condition |
    | --- | --- | --- |
    | most | `error`: a 51,697-token request against a 50,176-token window | `stop` only |
    | most | `length`: the output cap spent | `stop` only |
    | none | `stop` with nothing said | the case it answers |

## Interpretation

The weakest badge is `screen`, and this page has no evidence that the nudge
lifts a pass on this backend. An older number, 13/15 to 15/15, came from oMLX
rungs and is retired. What holds is the mechanism and its bound, and a sharper
problem: an empty turn has several causes and the nudge answers one. What would
upgrade this is a task whose empty finals carry `stop`, read on the `Nudges`
column.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt --repeat 3 --grade
uv run python learn/code/harness.py run --suite easy --remedy preset:easy,context/add-project-facts,context/use-short-prompt,nudge/nudge-empty-turn --repeat 3 --grade
```

!!! success "Key points"

    - `nudge/nudge-empty-turn` asks for one more turn when the model stops with nothing said, at most three times.
    - It answers only a `stop` final; an `error` (context overflow) or `length` (output cap) is a budget, not a lapse.
    - On Bronze it never fired, so its arm is void, not a null.
    - Read the fire count before the pass count when judging any guard.
