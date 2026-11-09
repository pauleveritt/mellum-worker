---
title: The Loop
tier: medium
number: M3
time: 5 min read · 20 min to run
track: lessons
position: 3
prerequisites: [lessons/medium/think-briefly]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# The Loop

The model reads the same file, gets the same answer, and reads it again — and
again, learning nothing each time. A guard that counts the repeats stops the sixth
and tells it to act on what it already knows.

!!! abstract "Overview"

    **Questions**

    - Why does a small model re-run a call whose answer can't have changed?
    - What counts a repeat, and what tells the guard the result might be different now?

    **Objectives**

    - Spot the loop in a trace: the same `ls` or `read`, five times over, nothing between.
    - Switch on `guard/repeat-loops`, read how it counts, and watch the sixth call refused.

![A small robot walking a tight circle that has worn a groove into the floor tiles, passing the same signpost again and again](../../assets/illustrations/the-loop.webp){ .illustration }

## Problem

**Badge:** `conjecture`

A small model loses the thread and reaches for the thing it knows how to do: it
reads a file. The file hasn't changed, so the answer is the same, so it reads it
again — the call becomes a nervous tic. One run shelled the same `ls -R` 245 times,
every one of them a success and none of them new. The budget drains into a groove
the model wears into the floor, and nothing gets built while it paces.

## Eval case

**Badge:** `conjecture`

**The condition:** any session where the model repeats an identical tool call with
nothing changed in between. **Before:** no loop guard — the repeat runs as often as
the model asks. **After:** `guard/repeat-loops`, which watches the recent calls and
refuses the sixth identical one. It is part of the shipped guard set behind a
phase-2b 15/15, and tested on its own at the unit grain.

## Evidence of the problem

**Badge:** `conjecture`

The tic is easy to read once you know its shape: the same `read`, `ls` or `grep`,
back to back, each returning what the last one did. It is not a wrong answer and
not a crash — it is a request spent to learn nothing, and on a bounded budget a
handful of them is a phase the model never gets to. The pathology is logged in the
[pathologies page](../../pathologies.md) as *a loop*.

## Solution

**Badge:** `conjecture`

One remedy unit, `guard/repeat-loops`, keeps a short memory of recent calls and
refuses a call it has already seen five times unchanged. The memory is the trick:
an edit, a write or a bash command may change what the next read returns, so any of
those forgets the repeats. Only an *unbroken* run of the same call trips the
breaker — an edit-then-re-read is never mistaken for a loop.

### The code

Switch it on live:

```text
/remedy on guard/repeat-loops
```

The guard is a closure with a little memory, quoted from the file frozen at a
commit
([`extensions/mellum-guards.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-guards.ts#L361-L385)):

```ts
export function createLoopBreaker(window = 20, threshold = 5) {
	let recent = [];
	return (call) => {
		if (MUTATING_TOOLS.has(call.toolName)) { recent = []; return undefined; }  // edit/write/bash: forget
		const key = callKey(call.toolName, call.input);
		const seen = recent.filter((entry) => entry === key).length;
		if (seen >= threshold) {
			return { block: true, reason:
				`You have already run this exact ${call.toolName} call ${seen} times with nothing changed ` +
				`in between, and the result will not change. Use what you already know and take the next action.` };
		}
		recent.push(key);
		if (recent.length > window) recent.shift();
		return undefined;
	};
}
```

`MUTATING_TOOLS` is the set that clears the memory — `edit`, `write`, `bash` —
because after any of those the same read can honestly return something new. To
screen it on a graded run, name it: `--remedy guard/repeat-loops`.

**Lesson check:** the sixth identical call is refused and the memory clears after a
write — proven at the unit grain
([test](https://github.com/andrevanzuydam/mellum-worker/blob/main/tests/remedy-units.test.mjs)).

## Validation

**Badge:** `conjecture`

The unit test pins the behaviour: five identical `ls` calls pass, the sixth is
blocked, and a `write` in between clears the count so the next `ls` passes again.
That is a presence claim settled at n=1 — the guard fires when it should and steps
aside when a mutation could have changed the answer. What it is not yet is a rate:
the guard ships in the set behind a phase-2b 15/15, so its standalone effect on the
score is owed a preregistered run, not read off a bundled pass.

## Interpretation

The weakest badge is `conjecture` — this rests on the unit test and the logged
pathology, not a run that isolates the guard. The lesson is the method as much as
the guard: a loop is one of the clearest things to read in a trace, and a cheap
guard that counts repeats buys the budget back that the tic would drain. It is a
guard that earns its place only where the pathology appears; on a tier that never
loops it would sit silent, which is E4's warning, read the other way round.

### Run it yourself

Load the guard on a medium run and read its block count in the record:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy guard/repeat-loops --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - A small model re-runs an unchanged call as a nervous tic, draining the budget.
    - `guard/repeat-loops` refuses the sixth identical call and forgets after any edit, write or bash.
    - Proven at the unit grain; the standalone score effect is still owed a run.
