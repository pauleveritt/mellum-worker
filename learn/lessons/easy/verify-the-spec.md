---
title: Verify the Whole Spec
tier: easy
number: E3
time: 5 min read · 12 min to run
track: lessons
position: 3
prerequisites: [lessons/easy/developer-frame]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E3 · Verify the Whole Spec

A model declares itself done and quietly leaves a requirement behind. The fix
isn't a better test — it's telling the model to account for every requirement, and
to run the tests, before it finishes.

!!! abstract "Overview"

    **Questions**

    - How does a run pass most checks and still drop one requirement?
    - What line makes a model verify the whole spec instead of the test it wrote?

    **Objectives**

    - Run the three-unit stack and find the rep that shipped without its navbar links.
    - Switch on `prompt/verify-the-spec`, read the line it adds, and watch the
      dropped requirement close, 5/6 → 6/6.

![A small robot ticking off every item on a checklist before closing the lid on its work](../../assets/illustrations/check-before-finishing.webp){ .illustration }

## Problem

**Badge:** `screen`

The model builds the home page, the tagline's there, the page returns 200 — and
the navbar links the spec asked for are gone. Not a faked check and not the wrong
place: a *dropped requirement*. The model verified the one thing it thought to
test and finished on the rest. A requirement it never implemented is a requirement
it never tested, so its own green run says nothing about it.

## Eval case

**Badge:** `screen`

**The condition:** Easy Phase 1, the home page with its required navbar links.
**Before:** `prompt/name-the-layout` + `prompt/python-developer` +
`guard/foreground-server`. **After:** the same plus one unit,
`prompt/verify-the-spec`. The grader is the Easy suite's hidden tests, which check
each requirement the spec names.

## Evidence of the problem

**Badge:** `screen`

At n=6 the three-unit stack read 5 of 6. The one loss, rep `c05e80`, passed the
tagline check and failed `test_home_still_has_navigation_links` — one check, Phase
1. No guard fired, nothing landed outside the layout. The model built a working
route and simply left out a piece the spec named, then declared done. Reading
files isn't verification; starting a server isn't verification; the model did one
of those and called it checked.

## Solution

**Badge:** `screen`

One remedy unit, `prompt/verify-the-spec`, appends a line to every turn that names
the act the role in E2 only gestured at: account for every requirement, and run the
project's own tests, before finishing. It names no requirement, route or value;
the model reads them from the spec. It catches the dropped requirement by making
the model clear the whole list, not just the test it chose to write.

### The code

In a live Pi session you switch it on alongside the earlier units:

```text
/remedy on prompt/verify-the-spec
```

The line and the hook that appends it to each turn, quoted from the file frozen at
a commit
([`remedies/prompt/verify-the-spec.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/remedies/prompt/verify-the-spec.ts#L8-L35)):

```ts
const LINE =
	"Before you finish, check that every requirement the spec lists is present in your code, and " +
	"run the project's own tests to confirm — do not finish while a requirement is unimplemented " +
	"or a test you can run is failing. Reading the files is not verification; run them.";

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

It's the same append mechanism as E1 — a `before_provider_request` hook on each
user message — carrying a different instruction. Stack the three prompt units and
the guard with the course preset: `--remedy preset:easy`.

**Lesson check:** 5/6 rose to **6/6** at n=6 on the local host, every rep with 0
failed checks
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

## Validation

**Badge:** `reference-run`

Adding the line took the stack from **5/6 to 6/6** at n=6, every rep green with 0
failed checks, median 25 turns — a touch more deliberate than before, which is the
verification step doing its work. The result replicated: a second n=6 run of the
same stack with an enforcement gate stacked on top also passed its prompt share,
and the gate fired 0 times because the prompts already met its contract
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
n=6 at 6/6 is a strong, replicated lead, not a one-host certainty.

## Interpretation

The weakest badge is `screen`. The reliability lever on Easy is verification — run
the real route or test before finishing, and account for every requirement the
spec names. The code is a single appended line; that it closes the dropped
requirement on this tier, where enforcement doesn't, is the lesson. The deeper rule
carries to any tier — a model's own "done" is a claim, not a check, and the spec is
the list it has to clear in full. On a harder tier the same claim needs a gate
behind it, which the Hard lessons build.

### Run it yourself

The three-unit stack, then with verification added:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout,prompt/python-developer,guard/foreground-server --grade --repeat 6 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy preset:easy --grade --repeat 6 --deadline 600
```

!!! success "Key points"

    - A run can pass most checks and still ship a requirement it never implemented.
    - A model's own "done" is a claim; the spec is the list it must clear in full.
    - `/remedy on prompt/verify-the-spec` appends one check-everything line — 5/6 → 6/6.
