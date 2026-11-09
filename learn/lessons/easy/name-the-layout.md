---
title: Name the Layout
tier: easy
number: E1
time: 4 min read · 10 min to run
track: lessons
position: 1
prerequisites: [getting-started]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E1 · Name the Layout

Give a small model a task and no floor plan, and it builds a house of its own.
One line that points it at the spec's own layout turns a flailing run into a
fast pass.

!!! abstract "Overview"

    **Questions**

    - Why does a small model put files where the grader never looks?
    - What exactly do I switch on in Pi to make it read the layout instead?

    **Objectives**

    - Run Easy Phase 1 from the bare floor and watch the model invent `main.py`.
    - Switch on `prompt/name-the-layout` in Pi, read the one line it adds, and
      see the model build `app.py` where the spec says.

![A small robot laying out floor tiles by following a blueprint pinned to the wall](../../assets/illustrations/creating-files.webp){ .illustration }

## Problem

**Badge:** `screen`

The spec names where each file belongs — `app.py` at the root, templates under
`templates/`. The model does not read it for that. Left to itself it reaches for
`find` and `ls`, wanders the empty workspace, and settles on a layout it made up,
`main.py` with the home page inside it. Every hidden check then imports the
project the spec described and finds nothing there. The work is done; it is just
done in the wrong house.

## Eval case

**Badge:** `screen`

**The condition:** Easy Phase 1 — the home page of a small FastAPI app, whose
file layout the spec states in the open. **Before:** the bare floor, Vanilla Pi
with only the recorder (`--arm vanilla`). **After:** the same floor plus one
unit, `prompt/name-the-layout`. The grader is the Easy suite's own hidden tests,
which import the project at the paths the spec names.

## Evidence of the problem

**Badge:** `screen`

From the floor the model flailed about fifteen turns shelling `find` and `ls`
through bash — there is no search tool on Easy — then invented the layout and
shipped `main.py` with no templates. The plain worker, the old bundle of six
guards with no prompt, did the same thing and scored 0 of 3. The guards stop bad
actions; they do not tell the model where a file goes.

## Solution

**Badge:** `screen`

One remedy unit, `prompt/name-the-layout`, appends a single agnostic line to
every message the model receives: read the project's own spec for where each
file belongs, and build there. It names no path, file or route of any suite, so
the model reads the layout from the spec itself — the line between a remedy and
coding to the eval.

### The code

In a live Pi session you switch it on with one command. Nothing else changes —
the floor is still Vanilla Pi plus the recorder:

```text
/remedy on prompt/name-the-layout
```

That loads one small file. The part that does the work is the line it adds and
the hook that attaches it to each turn — quoted here from the unit, frozen at a
commit so the page cannot drift
([`remedies/prompt/name-the-layout.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/remedies/prompt/name-the-layout.ts#L6-L33)):

```ts
const LINE =
	"Read the project's own spec or notes for where each file and route belongs, and create " +
	"files at exactly those paths — do not invent your own layout.";

// On every request to the model, append LINE to each user message.
pi.on("before_provider_request", (event) => {
	const payload = event.payload;
	return {
		...payload,
		messages: payload.messages.map((m) =>
			m.role === "user" ? { ...m, content: `${m.content}\n\n${LINE}` } : m),
	};
});
```

A `before_provider_request` hook sees the request on its way out and rewrites it.
The model never knows the line was added later; it reads the task and the layout
instruction as one message. The worker's own task now ends like this:

```text
Build the home page described in specs/phase1.md.

Read the project's own spec or notes for where each file and route belongs, and
create files at exactly those paths — do not invent your own layout.
```

To pass it to a graded run instead of a live session, name the same unit:
`--remedy prompt/name-the-layout`.

**Lesson check:** 2 of 3 on the local host, the fastest pass at 15 turns
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

## Validation

**Badge:** `reference-run`

On the Easy ladder, built one unit at a time from the floor: Vanilla Pi alone
failed; the plain worker scored **0/3**; Vanilla Pi plus this one line scored
**2/3**, and did it in 15 turns against the worker's 53
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
One agnostic line matched the whole worker's pass and beat it on speed. This
shows guidance works on this tier on this host, not that two of three is the
settled rate.

## Interpretation

The weakest badge is `screen`. The lever on Easy is guidance, not guards. Six
guards and a facts block earned nothing; one line that points the model at the
spec earned the pass. The change is small enough to read in full — a constant
and a hook — and that is the point of showing it: you can see exactly what
reached the model, and that it carries no answer to the exam. A real codebase
has the same shape as this task — a convention for where things live, written
down somewhere the model has to be told to read. The habit the unit teaches is
the one to keep: take the layout from the spec, never from the model's
imagination.

### Run it yourself

The floor, then the floor plus the unit:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --grade --repeat 1 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout --grade --repeat 1 --deadline 600
```

!!! success "Key points"

    - A small model invents a file layout unless the task points it at the spec's.
    - `/remedy on prompt/name-the-layout` adds one line through a
      `before_provider_request` hook — the whole change is a constant and that hook.
    - One agnostic line took Easy from 0/3 to 2/3, and beat the six-guard worker on speed.
