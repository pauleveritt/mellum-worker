---
title: A Developer's Frame
tier: easy
number: E2
time: 4 min read · 10 min to run
track: lessons
position: 2
prerequisites: [lessons/easy/name-the-layout]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E2 · A Developer's Frame

The model that knows where the files go can still ship a careless one. A short
role, a meticulous developer working to a spec, steadies the hand.

!!! abstract "Overview"

    **Questions**

    - Why does a model that gets the layout right still fail on small mistakes?
    - What does a role prompt put in front of the model, and where?

    **Objectives**

    - Run Easy with the layout line and watch a run trip on an unchecked typo.
    - Switch on `prompt/python-developer`, read the role it prepends, and see the
      careful version of the same run.

![A small robot in overalls reading a spec sheet with a careful, measured eye](../../assets/illustrations/a-short-prompt.webp){ .illustration }

## Problem

**Badge:** `screen`

With the layout named, the model builds in the right place. And still finishes on
a mistake it never checked. A stray `if __name__ == "main__":` with the
underscores wrong, a done declared without a single run. The work has the right
shape and a careless flaw tucked inside it. Nothing frames the model as the kind
of developer who reads twice and runs the thing before it says done.

## Eval case

**Badge:** `screen`

**The condition:** Easy Phase 1, the same home page. **Before:** Vanilla Pi plus
`prompt/name-the-layout`. **After:** the same plus one more unit,
`prompt/python-developer`. The grader is the Easy suite's hidden tests.

## Evidence of the problem

**Badge:** `screen`

With the layout line alone the ladder sat at 2 of 3: the layout's right, the
finish isn't. The failing runs aren't in the wrong place, they're the right place
built carelessly. A typo shipped unchecked, a done declared without a run. The
gap isn't where the file goes. It's how the work is done.

## Solution

**Badge:** `screen`

One remedy unit, `prompt/python-developer`, prepends a single role to the system
prompt. Where `name-the-layout` appends a line to each turn, this one reaches the
front of the whole session. The model works as a careful developer from the first
token. It names no suite, file or route; a role changes how the model works, never
what the task is.

### The code

In a live Pi session you switch it on with one command, on top of the layout line
from E1:

```text
/remedy on prompt/python-developer
```

The unit is one sentence and the hook that puts it at the head of the system
prompt, quoted from the file frozen at a commit
([`remedies/prompt/python-developer.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/remedies/prompt/python-developer.ts#L6-L31)):

```ts
const ROLE =
	"You are an experienced, meticulous python developer working in a spec driven paradigm.";

// Prepend ROLE to the system message (or add one if there is none).
pi.on("before_provider_request", (event) => {
	const payload = event.payload;
	const messages = [...payload.messages];
	const i = messages.findIndex((m) => m.role === "system");
	if (i >= 0) messages[i] = { ...messages[i], content: `${ROLE}\n\n${messages[i].content}` };
	else messages.unshift({ role: "system", content: ROLE });
	return { ...payload, messages };
});
```

The role rides in front of Pi's own system prompt. The model reads it first,
before the task, so every turn is coloured by the frame instead of reminded of it.
To pass it to a graded run instead, name both units:
`--remedy prompt/name-the-layout,prompt/python-developer`.

**Lesson check:** 2/3 rose to 3/3 at n=3 on the local host, a screen
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

## Validation

**Badge:** `reference-run`

Adding the role took `name-the-layout` from **2/3** to **3/3** at n=3, at 14 to
20 turns. At n=6 the same stack read **4/6**. The screen at n=3 flattered it, as
screens do
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
The role helps; it doesn't finish the job on its own. A screen is a lead, never a
rate, and a strong lead at small n is still a lead.

## Interpretation

The weakest badge is `screen`. A role prompt makes the model *attempt* care, but
care comes out as reading files or launching a server, not always as running the
real check. That's the limit of a frame: it points the model at diligence without
saying what diligence does. The code shows why. One sentence at the head of the
prompt, nothing that enforces a thing. The next lesson names the act. Verify every
requirement, and run the test. Which is what carries the stack the rest of the
way. The role is the posture; verification is the act.

### Run it yourself

With the layout line, then with the role added:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout --grade --repeat 3 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout,prompt/python-developer --grade --repeat 3 --deadline 600
```

!!! success "Key points"

    - The right layout can still ship a careless, unchecked mistake.
    - `/remedy on prompt/python-developer` prepends one role sentence to the
      system prompt. A posture, not an enforcement.
    - It lifted the screen 2/3 → 3/3, but n=6 read 4/6. A lead, not a settled rate.
