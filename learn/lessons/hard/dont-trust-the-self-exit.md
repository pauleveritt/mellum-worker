---
title: Don't Trust the Self-Exit
tier: hard
number: H2
time: 8 min read · 60 min to run
track: lessons
position: 2
prerequisites: [lessons/hard/architect-split]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# H2 · Don't Trust the Self-Exit

The worker decides when it's done, and it'll call done over a quiet, self-authored
test that never touched the hard contract. The orchestration fix is a gate:
re-run an external, frozen test at settle, and hand the failure back until it's
green.

!!! abstract "Overview"

    **Questions**

    - How does a run exit confident on a build that fails the hidden grader?
    - What drives the worker back when its own "done" is wrong, and how do I wire it?

    **Objectives**

    - Read the Phase-4 contract a self-authored test passes and the oracle fails.
    - Switch on the verify gate with a frozen acceptance test, and watch one re-dispatch close the gap.

![A small robot proudly holding a paper checkmark at a finish line while a larger robot there holds up a clipboard to check it](../../assets/illustrations/dont-trust-the-self-exit.webp){ .illustration }

## Problem

**Badge:** `screen`

In a single pass the worker is its own gatekeeper. It decides when the work is
finished. On medium it leaks the same two points every time: Phase 4. The hidden
oracle builds the complaint object **directly** and asserts its id is an
automatic, unique default *on the type*. The worker takes the easy road. It
assigns the id in the one route the happy path walks. Which passes that route and
fails direct construction. Its own test only ever called the route, so its green
run says nothing about the contract it skipped. A better sentence won't fix this:
a stronger prose rule reached the full pass on only half the reps.

## Eval case

**Badge:** `screen`

**The condition:** the medium suite in a single pass (the H1 one-pass shape), with
the live-server guard from M1 keeping it in process. **Before:** no gate. The
worker settles on its own. **After:** the verify gate re-runs a complete, external,
frozen acceptance test at settle and re-dispatches the failing concept. The grader
is the hidden oracle, summed to 18
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

## Evidence of the problem

**Badge:** `screen`

Ungated, the one-pass medium run landed 16/18 on both converged reps and 18/18 on
only half of a five-rep screen. The Phase-4 id shape leaking exactly as above
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
The floor stayed at 15–16: when the first draft happened to get the invariant
right it finished clean, and when it didn't, no prose reliably rescued it. The miss
is invisible to the worker because the worker never wrote a test that builds the
object directly. The one check it needed is the one it left out.

## Solution

**Badge:** `screen`

The fix is a harness guarantee, not a prompt. The verify gate hooks
`agent_before_settle`: when the worker tries to finish, the gate re-runs a frozen
acceptance test and, while it's red, refuses the settle and hands back only the
failing test functions, the unmet concepts, for a short corrective turn, up to a
limit. The test is **external** (the worker didn't write it), **complete** (a
superset of the hidden oracle, with the direct-construction check in it), and
**held out** beside the workspace, where the worker can't read or weaken it.

### The code

The gate is one `agent_before_settle` hook
([`extensions/mellum-verify.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-verify.ts#L104-L123)):

```ts
export default function (pi) {
	let used = 0;
	pi.on("agent_before_settle", (_event, ctx) => {
		const { test, max, pytest } = gateConfig();          // VERIFY_TEST, VERIFY_MAX
		if (test === "" || !(used < max)) return undefined;
		const v = runTest(test, pytest, ctx.cwd);            // re-run the frozen test
		if (v.passed) return undefined;                      // every concept met, let it settle
		used += 1;
		return {                                             // refuse settle, name the unmet concepts
			entries: [{ type: "custom_message", customType: "mellum-verify", content: gateMessage(v), display: true }],
			continue: true,
		};
	});
}
```

The message it hands back names the failing tests and says the test is held out.
*don't go looking for it; each name is a behaviour to satisfy, checked with your
own tests in this directory*. The test itself pins the contract the worker
skipped, written from the spec, never from the grader
([`ladder/fixtures/acceptance/test_medium.py`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/ladder/fixtures/acceptance/test_medium.py)):

```python
def test_two_direct_constructions_get_distinct_ids():
    a = models.Complaint("agent-a", "first")   # constructed directly, not via the route
    b = models.Complaint("agent-b", "second")
    assert a.id != b.id                          # the id must default ON the type, not in the route
```

The ladder drives this natively. It copies the test into the workspace baseline,
freezes it, and re-dispatches the failure:

```bash
uv run python -m ladder.run_ladder --mode direct \
  --acceptance-test ladder/fixtures/acceptance/test_medium.py --redispatch 5 \
  --provider llamacpp --base-url http://127.0.0.1:8001/v1 ...
```

**Lesson check:** one re-dispatch carried a short-settling rep to a clean 18/18 at
61 requests
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

## Validation

**Badge:** `screen`

In the gated one-pass medium run, the rep that settled short had the gate re-run
the frozen test, name the unmet concept, and one small corrective turn carried it
to a clean 18/18. The deep Phase-4 contract closed by a harness guarantee, not a
sentence
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
On the real ladder, the one-pass arm with this native gate passed **3 of 3** on the
hidden oracle at a mean of ~43 requests. The gate only runs at settle, though, so
it leans on the live-server guard from M1 to keep the run alive long enough to
reach it. Guard and gate pull together: the guard gets the run to settle, the gate
closes the last contract.

## Interpretation

The weakest badge is `screen`. A mechanism proof on one converged rep, plus the
3-of-3 ladder arm; a lead, not a settled rate. This is the orchestration H1's split
was really for, kept even in a single pass: the architect's one durable
contribution is a complete, frozen test, and the gate uses it to define "done" so
the worker can't talk its way past. The honest caution: handing a confused small
model "these tests still fail" can nudge it toward live-server debugging itself,
which is why M1's guard rides along. The evidence is llama.cpp; a preregistered
`--mode one-pass` run against the plan loop at larger n is what turns this lead into
a rate.

### What to try next

A run where the gate fires *red* on a would-be stall is the integration proof the
clean-exit fixes still want. The re-dispatch path that hunts for a held-out file
and stalls, now exiting clean instead. It's variance-dependent, so it needs reps
until the gate bites
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

### Run it yourself

The one-pass medium run with the native frozen gate and re-dispatch:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy guard/no-live-server --grade --repeat 3 --deadline 1800
```

!!! success "Key points"

    - A single-pass worker is its own gatekeeper; its "done" can be wrong on the hard contract.
    - The verify gate re-runs an external, frozen, held-out test at settle and re-dispatches the failure.
    - One re-dispatch closed the Phase-4 miss a prose rule only coin-flipped. A harness guarantee, not a sentence.
