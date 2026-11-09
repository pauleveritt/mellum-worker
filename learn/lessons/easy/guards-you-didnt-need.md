---
title: Guards You Didn't Need
tier: easy
number: E4
time: 5 min read · 15 min to run
track: lessons
position: 4
prerequisites: [lessons/easy/verify-the-spec]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E4 · Guards You Didn't Need

The temptation on a hard problem is to add machinery. A guard, an enforcement
gate. The scientific move is to measure whether it fires. On Easy, the machinery
sat silent and the prompts did the work.

!!! abstract "Overview"

    **Questions**

    - How do I tell a guard is earning its place and not just riding along?
    - Where in the run record do I read whether a guard fired at all?

    **Objectives**

    - Switch on `guard/foreground-server`, then read `guard_blocks` in `run.json`
      and find the guard that fired 0 times.
    - Stack the verify gate on the 6/6 set and watch it add nothing. And cost a rep.

![A small robot watching a row of alarm bells that never ring while it works](../../assets/illustrations/evidence.webp){ .illustration }

## Problem

**Badge:** `screen`

A tier looks hard, so you reach for a guard, then a gate that re-runs a test and
sends the model back. It feels safer. But a unit that never fires buys nothing, and
a gate that only acts when the worker finishes can't help a worker that never does.
The danger is a stack that passes *with* the machinery, so the machinery takes the
credit the prompts earned.

## Eval case

**Badge:** `screen`

**The condition:** the Easy set that passes 6/6. `preset:easy`. **The guard:**
`guard/foreground-server`, in the set, refusing a foreground server start. **The
gate:** the mediated acceptance gate (`mellum-acceptance` derives a structural test
from the spec; `mellum-verify` re-runs it at settle and re-dispatches a red one),
loaded on top with `--extension`. The grader is the Easy hidden tests; `run.json`
records `guard_blocks` and each gate firing.

## Evidence of the problem

**Badge:** `screen`

Across every n=6 run, `guard/foreground-server` fired **0 times**. The model never
tried the foreground server the guard refuses, so the guard sat silent while the
prompts carried the pass. Stacking the verify gate on the 6/6 set gave **5/6**, not
better: the gate fired **0 times** too, because the prompts already met its
contract before it checked. The one loss spun **66 turns to the deadline with no
settle attempt**, so the gate, which acts only at finish, never got a turn, and
the run shipped without the HTML5 doctype its own contract checks for.

## Solution

**Badge:** `screen`

The move isn't to trust a guard but to read whether it bit. The guard itself is a
short function: it looks at a bash command, decides whether it starts a foreground
server, and either hands back a block with a reason or steps aside. The run record
counts every block it returns, and that count is the evidence.

### The code

Switch the guard on live:

```text
/remedy on guard/foreground-server
```

The guard is one function. It returns a block only when the command would hang the
run, and the reason points the model back in process
([`extensions/mellum-guards.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-guards.ts#L229-L243)):

```ts
export const serverGuard = (call) => {
	if (call.toolName !== "bash") return undefined;
	const command = commandOf(call.input);
	if (!isForegroundServer(command)) return undefined; // not a server start, step aside
	return {
		block: true,
		reason:
			"That starts a server in the foreground; it blocks forever and burns your whole time budget. " +
			"Exercise an endpoint in process the way the tests do: TestClient(app).get('/...').",
	};
};
```

Every block it returns is counted in the run record. After a run, read it. A guard
that reads `0` did nothing this run:

```bash
# how many times each guard blocked a call, this run
cat runs/<run-id>/run.json | python -m json.tool | grep -A6 guard_blocks
```

The gate is loaded the same way, as two extensions on top of the preset, and the
record logs each time it fires. Both numbers come from the same place: the run
record, never a hunch.

**Lesson check:** guard 0× across six reps; the verify gate 5/6, firing 0×
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).

## Validation

**Badge:** `reference-run`

Two independent n=6 runs agree: the prompt lines pass Easy, and the enforcement
around them is inert. `guard/foreground-server` blocked nothing in either; the
verify gate re-dispatched nothing and read 5/6, its one loss a run it structurally
couldn't touch
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
The verify gate is a finish-time gate, not a watchdog. Blind to the failure mode
that never settles. Its payoff is a harder tier, where the prompts don't already
pass and a settled "done" hides a real miss.

## Interpretation

The weakest badge is `screen`. The cheapest thing that passes is the right thing.
On Easy that's three prompt lines; the guard and the gate add nothing you can
measure, and a gate can even trap a struggling rep in a loop it can't finish. The
habit the code teaches is to read `guard_blocks` before you believe a guard helped.
This is the method, not a verdict against guards. A guard earns its place on the
tier where its pathology actually appears. The Medium and Hard lessons are exactly
that: a guard and a gate read on the tier where they finally bite.

### Run it yourself

The 6/6 set, then the same with the verify gate stacked on:

```bash
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy preset:easy --grade --repeat 6 --deadline 600
uv run python learn/code/harness.py run --suite easy --arm vanilla --remedy preset:easy --extension extensions/mellum-acceptance.ts --extension extensions/mellum-verify.ts --grade --repeat 6 --deadline 600
```

!!! success "Key points"

    - A unit that never fires earns nothing; read `guard_blocks` to see it.
    - The verify gate acts only at finish, so it can't save a worker that never settles.
    - On Easy the prompts pass; reach for enforcement only where guidance stops being enough.
