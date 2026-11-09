---
title: Think Briefly
tier: medium
number: M2
time: 7 min read · 45 min to run
track: lessons
position: 2
prerequisites: [lessons/medium/live-server-spiral]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# M2 · Think Briefly

A turn cap that tames the easy tier starves the medium one — the bigger steps get
cut off mid-route. The fix is not a bigger cap; it is a shorter think, so each
step costs fewer, denser turns and the cap fits.

!!! abstract "Overview"

    **Questions**

    - Why does the same turn cap help easy and hurt medium?
    - How do I cut a model's thinking when it has no reasoning-effort dial?

    **Objectives**

    - Read a medium run where a per-step turn cap fires and leaves `POST /complaints` returning 405.
    - Switch on `prompt/think-briefly`, read the one line it adds, and watch the median climb 10 → 16.

![A small robot writing one short note per step instead of a long essay before each move](../../assets/illustrations/a-short-prompt.webp){ .illustration }

## Problem

**Badge:** `screen`

A per-step turn cap is how you stop a worker thrashing — on easy it bounded the
thrash and held 4/4. On medium the same cap *starves* the work: the steps are
bigger, the worker spends its turns thinking, and the cap fires before the route
is written. A capped run leaves `POST /complaints` returning 405 — the handler
never finished — and the median score falls below the uncapped baseline. The cap
is not wrong; it is tuned for a tier where each step is small.

## Eval case

**Badge:** `screen`

**The condition:** the medium suite (phases 1–4), the shipped plan loop, scored on
the hidden oracle summed to 18. **Before:** the full medium stack with a per-step
turn cap of 25. **After:** the same plus `prompt/think-briefly`. Three reps each,
a scratch screen of the shipped loop — a lead, not a recorded rate
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md)).

## Evidence of the problem

**Badge:** `screen`

With the cap at 25 and nothing else, the medium reps read 10 / 18 / 8, median
**10** — below the uncapped baseline's median of 15. The cap fired repeatedly and
cut workers off before they finished the phase-3 and phase-4 routes. The lost
points are not careless mistakes; they are *unfinished behaviour* — a route that
returns 405 because the worker ran out of turns while still thinking about it.

## Solution

**Badge:** `screen`

Mellum has no reasoning-effort dial — `supportsReasoningEffort` is false, and
turning thinking off pollutes the content channel. The only lever that works is
the prompt. One remedy unit, `prompt/think-briefly`, tells the worker to reason in
one short sentence per action. A denser turn carries more work, so the same cap of
25 now covers the step instead of cutting it off.

### The code

Switch it on live, alongside the turn cap:

```text
/remedy on prompt/think-briefly
/remedy on guard/turn-cap
```

The line and the hook that appends it to each turn, from the unit
([`remedies/prompt/think-briefly.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/main/remedies/prompt/think-briefly.ts)):

```ts
const LINE =
	"Think briefly — reason in one short sentence before each action, then act; do not debate " +
	"back and forth or restate your plan. A concise turn is the goal, not a long one.";

// Append LINE to each user message on its way to the model.
pi.on("before_provider_request", (event) => {
	const payload = event.payload;
	return {
		...payload,
		messages: payload.messages.map((m) =>
			m.role === "user" ? { ...m, content: `${m.content}\n\n${LINE}` } : m),
	};
});
```

It is the same append mechanism as the easy prompt units — one line onto each
user turn. The companion is the turn cap itself (`guard/turn-cap`, or the
`MELLUM_TURN_CAP` the shipped loop reads); the two are measured together, because
neither pays alone: the cap without the shorter think starves the step, and the
shorter think without the cap just runs longer.

**Lesson check:** median 10 → 16, floor 8 → 15 at n=3
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md)).

## Validation

**Badge:** `screen`

| arm | rep1 | rep2 | rep3 | median | floor |
|-----|------|------|------|--------|-------|
| cap 25 | 10 | 18 | 8 | **10** | 8 |
| cap 25 + think briefly | 18 | 15 | 16 | **16** | **15** |

Adding the shorter think lifted the median from 10 to 16 and the floor from 8 to
15 — the low-variance collapse that hit both the baseline and the capped stack
disappeared
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md)).
The quality column that moved is the score; the budget it cost is a touch more
deadline pressure — one rep still ran to the 30-minute wall, though it scored 18
anyway. This is a scratch screen of five bundled changes, so the attribution to
the cap-and-think pair is inference; a clean ablation is owed before any default
change.

## Interpretation

The weakest badge is `screen`. The medium lesson is that a setting measured on one
tier does not carry to the next — the easy stack is not the medium stack, it is
the floor the medium remedies are built on. The turn cap is the clearest case: a
win on easy, a loss on medium, a win again once the thinking is cut to fit it.
The code is one appended line, and it works because it changes *how the model
spends a turn*, not what the task is — the whole Medium theme. The evidence is
llama.cpp (Mellum Q4 on the local server), a lead to be settled by a preregistered
`run_ladder`, not a rate.

### What to try next

A finer step-plan — fewer requirements per step so a worker needs fewer turns —
targets the same budget without touching the think; the measured risk is
over-splitting a many-bullet spec into contentless micro-steps, which backfired
at a tight budget, so it wants its own screen
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md)).

### Run it yourself

Load the pair on a medium run; the full plan-loop rig that produced the table is
the scratch driver in the research note:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy prompt/think-briefly,guard/turn-cap --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - A turn cap that bounds easy starves medium — bigger steps get cut off mid-route.
    - Mellum has no effort dial, so `prompt/think-briefly` cuts the thinking with one line.
    - Cap plus shorter think lifted the median 10 → 16; a scratch screen, not a settled rate.
