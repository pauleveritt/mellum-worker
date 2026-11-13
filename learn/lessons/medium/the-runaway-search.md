---
title: The Runaway Search
tier: medium
number: M4
time: 5 min read · 20 min to run
track: lessons
position: 4
prerequisites: [lessons/medium/the-loop]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# The Runaway Search

Told to find a file it can't see, the model searches the whole machine. `find /`,
`grep -r /Users`. And the crawl hangs the run. A guard pins the search inside the
workspace, where the file actually lives.

!!! abstract "Overview"

    **Questions**

    - Why does a confused model reach for `find /` and crawl the entire disk?
    - How does the guard tell a workspace search from a whole-machine one?

    **Objectives**

    - Read a run that stalls on `find / -name test_medium.py` eating the clock.
    - Switch on `guard/outside-workspace`, read how it measures "outside", and watch the crawl refused.

![A small robot with a torch peering into an enormous dark warehouse of shelves, a tidy room with one open drawer right behind it](../../assets/illustrations/searching.webp){ .illustration }

## Problem

**Badge:** `screen`

The model is handed a name and can't find it in the workspace, so it widens the
net the only way it knows. It points `find` at the root of the disk and sets off.
The whole machine is a lot of floor to cover. The crawl doesn't error; it just
walks, directory after directory, until the stall guard pulls the plug. One gated
run showed it plainly: the gate named a held-out test, the worker went looking for
it with `find / -name test_medium.py`, and that one crawl ate the time to the
stall.

## Eval case

**Badge:** `screen`

**The condition:** a session where the model runs a tree walk (`find`, recursive
`grep`, `ls -R`) against a path outside its working folder. **Before:** no confine
guard. The crawl runs against whatever path the model names. **After:**
`guard/outside-workspace`, which refuses a tree walk whose target sits outside the
workspace. It is the guard this session widened to catch a bare `/` as well as
`/Users` and `/var`.

## Evidence of the problem

**Badge:** `screen`

The crawl showed up in the wild on the exit-gate run: a correct build settled
short, the gate re-dispatched naming a held-out test, and the worker. The test
living beside the workspace, not in it. Hunted the whole machine for the file and
stalled there
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
The matcher had a gap, too: it refused `grep -rl x /Users /var` but let a lone `/`
through, so `find /` ran unguarded until one character fixed it.

## Solution

**Badge:** `screen`

One remedy unit, `guard/outside-workspace`, refuses a tree walk that reaches past
the working folder. It only fires on a command that actually walks a tree. A
`find`, a recursive `grep`, an `ls -R`. And only when the path it walks sits
outside the workspace. A search with relative paths, or paths under the working
folder, passes untouched; the guard is after the crawl that escapes, not the honest
local search.

### The code

Switch it on live:

```text
/remedy on guard/outside-workspace
```

The guard resolves every absolute path the command names and blocks the walk if one
of them escapes the working folder
([`extensions/mellum-guards.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-guards.ts#L336-L356)):

```ts
export function confineSearch(root) {
	const base = resolve(root);
	const isUnder = (p) => { const r = resolve(base, p); return r === base || r.startsWith(`${base}/`); };
	return (call) => {
		if (call.toolName !== "bash") return undefined;
		const command = commandOf(call.input);
		if (!command || !isTreeWalk(command)) return undefined;              // not a crawl, let it be
		const outside = absolutePathArgs(command).filter((p) => !isUnder(p));
		if (outside.length === 0) return undefined;                          // every path is inside
		return { block: true, reason:
			`That searches outside your workspace (${outside.slice(0, 3).join(", ")}). It scans the whole ` +
			`machine and hangs the run. Search only within your working folder: use relative paths (e.g. ` +
			"`grep -rl pattern .`) or paths under " + `${base}.` };
	};
}
```

`isTreeWalk` is what keeps it narrow. A `cat` or a single-file `grep` is not a
crawl, so it passes. `absolutePathArgs` reads the paths the command names, and the
bare `/` that once slipped through now resolves to the root and is caught. To screen
it on a graded run, name it: `--remedy guard/outside-workspace`.

**Lesson check:** `grep -rl x /Users /var` and `find /` are refused; `grep -rl x .`
passes. Proven at the unit grain
([test](https://github.com/andrevanzuydam/mellum-worker/blob/main/tests/remedy-units.test.mjs)).

## Validation

**Badge:** `screen`

The unit test pins both sides: a walk across `/Users /var` is blocked, a walk of
`.` passes, and after this session's fix a bare `/` is blocked too. The crawl it
targets was seen live, stalling a run that had already built correctly. A presence
claim at n=1, the clearest kind of evidence a guard can carry. What stays open is
whether a run that *now* gets refused the crawl goes on to exit clean instead of
stalling; that wants a run where the gate fires red, which is variance-dependent
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

## Interpretation

The weakest badge is `screen`. A live sighting plus the unit test, not a rate. The
guard pairs with the exit-gate from H2: the gate is what sends the worker looking
for a held-out test, so the gate needs this guard beside it to keep the search from
running off the bench. It's a context error dressed as a search. The model is
looking in the wrong place because the thing it wants isn't where it expects. And
the cheapest fix is a fence around the floor it's allowed to walk.

### Run it yourself

Load the guard on a medium run and read its block count in the record:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy guard/outside-workspace --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - A model that can't find a file crawls the whole disk with `find /`, and the crawl hangs the run.
    - `guard/outside-workspace` refuses a tree walk whose path escapes the working folder.
    - The bare-root case slipped through until a one-character fix this session; proven at the unit grain.
