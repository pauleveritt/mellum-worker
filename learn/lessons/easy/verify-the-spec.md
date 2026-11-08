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

A model declares itself done and quietly leaves a requirement behind. The fix is
not a better test — it is telling the model to account for every requirement, and
to run the tests, before it finishes.

!!! abstract "Overview"

    **Questions**

    - How does a run pass most checks and still drop one requirement?
    - What makes a model verify the whole spec instead of the test it wrote?

    **Objectives**

    - Run the three-unit stack and find the rep that shipped without its navbar links.
    - Add `prompt/verify-the-spec` and watch the dropped requirement close, 5/6 → 6/6.

![A small robot ticking off every item on a checklist before closing the lid on its work](../../assets/illustrations/check-before-finishing.webp){ .illustration }

## Problem

**Badge:** `screen`

The model builds the home page, the tagline is there, the page returns 200 — and
the navbar links the spec asked for are missing. Not a faked check and not the
wrong place: a *dropped requirement*. The model verified the one thing it thought
to test and finished on the rest. A requirement it never implemented is a
requirement it never tested, so its own green run says nothing about it.

## Eval case

**Badge:** `screen`

**The condition:** Easy Phase 1, the home page with its required navbar links.
**Before:** `prompt/name-the-layout` + `prompt/python-developer` +
`guard/foreground-server`. **After:** the same plus one unit,
`prompt/verify-the-spec`. The grader is the Easy suite's hidden tests, which
check each requirement the spec names.

## Evidence of the problem

**Badge:** `screen`

At n=6 the three-unit stack read 5 of 6. The one loss, rep `c05e80`, passed the
tagline check and failed `test_home_still_has_navigation_links` — one check,
Phase 1. No guard fired, nothing landed outside the layout. The model built a
working route and simply left out a piece the spec named, then declared done.
Reading files is not verification; starting a server is not verification; the
model did one of those and called it checked.

## Solution

**Badge:** `screen`

**Remedy unit:** `prompt/verify-the-spec`; switch it on live in Pi with `/remedy on prompt/verify-the-spec`, or pass `--remedy prompt/verify-the-spec` to a graded run.

**Remedy code:** [`remedies/prompt/verify-the-spec.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/main/remedies/prompt/verify-the-spec.ts) — the few lines that make the fix. In Pi the `/lesson` panel shows the file inline under this step.

**Lesson check:** 5/6 rose to **6/6** at n=6 on the local host, every rep with 0
failed checks
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

The unit appends one agnostic line to each turn: before you finish, check that
every requirement the spec lists is present in your code, and run the project's
own tests to confirm — do not finish while a requirement is unimplemented or a
test you can run is failing, and reading the files is not verification. It names
no requirement, route or value; the model reads them from the spec. It catches
the dropped requirement by making the model account for each one, not only the
test it chose to write.

## Validation

**Badge:** `reference-run`

Adding the line took the stack from **5/6 to 6/6** at n=6, every rep green with 0
failed checks, median 25 turns — a touch more deliberate than before, which is
the verification step doing its work. The result replicated: a second n=6 run of
the same stack with an enforcement gate stacked on top also passed its prompt
share, and the gate fired 0 times because the prompts already met its contract
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
n=6 at 6/6 is a strong, replicated lead, not a one-host certainty.

## Interpretation

The weakest badge is `screen`. The reliability lever on Easy is verification —
run the real route or test before finishing, and account for every requirement
the spec names. A prompt line is the cheap way to get it, and on Easy it is
enough: it closes the dropped requirement that the layout and the role left
behind. The deeper rule carries to any tier — a model's own "done" is a claim,
not a check, and the spec is the list it has to clear in full.

### Run it yourself

The three-unit stack, then with verification added:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout,prompt/python-developer,guard/foreground-server --grade --repeat 6 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy prompt/name-the-layout,prompt/python-developer,guard/foreground-server,prompt/verify-the-spec --grade --repeat 6 --deadline 600
```

!!! success "Key points"

    - A run can pass most checks and still ship a requirement it never implemented.
    - A model's own "done" is a claim; the spec is the list it must clear in full.
    - `prompt/verify-the-spec` makes it check every requirement and run the tests — 5/6 → 6/6.
