---
title: The Architect Split
tier: hard
number: H1
time: 8 min read · 60 min to run
track: lessons
position: 1
prerequisites: [lessons/medium/think-briefly]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# H1 · The Architect Split

The orchestration move everyone reaches for is to split the spec: an architect
plans the steps, a fresh worker builds each. With one fixed model that split is
overhead — one agent in a single pass is about five times cheaper at the same
score.

!!! abstract "Overview"

    **Questions**

    - When does delegating a build across an architect and fresh workers actually pay?
    - What does the `delegate` tool hand off, and how do I switch the loop on or off?

    **Objectives**

    - Read the two orchestration shapes side by side: the plan loop and one pass.
    - Run `--mode plan` against `--mode direct` and see the request count, not just the score.

![A small robot foreman handing numbered work-orders to a row of identical workers, each at its own bench](../../assets/illustrations/lessons.webp){ .illustration }

## Problem

**Badge:** `screen`

Delegation is the classic answer to a big task: one agent cannot hold the whole
spec, so an architect decomposes it into ordered steps, writes a brief and a
frozen test per step, and a fresh worker builds each one. It is real
orchestration — who drives, who implements, how a finished step hands to the
next. The question this lesson asks is not whether it works, but what it *costs*,
and whether a single fixed model needs it at all.

## Eval case

**Badge:** `screen`

**The condition:** easy (home page, oracle /4) and medium (four phases, oracle
/18). **Arm A:** one agent builds the whole section in a single pass —
`--mode direct`, no architect, no step docs, no delegation. **Arm B:** the shipped
plan-delegation loop — `--mode plan`, the architect splits the spec and a fresh
worker builds each step. The primary outcome is **total requests**; the score is a
guardrail
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

## Evidence of the problem

**Badge:** `screen`

| tier | one pass (Arm A) | plan loop (Arm B) |
|------|------------------|-------------------|
| easy (/4) | 4/4 at ~11.5 requests | 4/4 at ~52–64 requests |
| medium (/18) | 16/18 at ~70 requests | 300+ requests, pass-rate patchy |

One pass reached the same score for roughly a fifth of the requests. The
delegation the loop adds is pure overhead on these tiers: a page the architect
never needed to carve, and workers each paying to re-read a spec the one agent
already held in context. On the real ladder a one-pass arm with the exit-gate
later reproduced this — 3 of 3 on the hidden oracle at a mean of ~43 requests
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

## Solution

**Badge:** `screen`

The solution here is a judgement, not a switch: delegate only when it pays. The
split pays on a **model-tier price gap** — an expensive planner, a cheap builder,
which is exactly what JetBrains shipped as Junie "Eco Mode" (48–57% lower cost at
flat resolve). With one fixed model that gap is zero, so the split is overhead.
The other case it pays is a spec too large for one context — the case these tiers
do not test. The code below is how you drive each shape so you can measure the
gap yourself.

### The code

The loop is one primary-side tool and one nudge. The `delegate` tool hands one
bounded task to a fresh worker child; the nudge tells the primary to delegate the
implementation rather than write it
([`extensions/mellum-worker.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-worker.ts#L116-L168)):

```ts
const DELEGATE_NUDGE =
	"You are the primary. Explore, decide the layout, and pin the goal with a check or a failing " +
	"test yourself — but hand the implementation to the `delegate` tool, do not write it. … " +
	"Then read the worker's report and verify by running that command; delegate a fix if it is not done yet.";

// A PRIMARY-side tool. The spawned worker child sets MELLUM_WORKER_CHILD=1 and
// gets neither this tool nor the nudge, so a worker cannot delegate to itself.
pi.registerTool({
	name: "delegate",
	description: "Hand ONE bounded, test-driven implementation task to the local coding worker. …",
	parameters: { type: "object", properties: { brief: { type: "string" } }, required: ["brief"] },
	async execute(_id, { brief }) {
		return { content: [{ type: "text", text: await spawnWorker(brief) }] };
	},
});
```

You do not wire this by hand to compare the shapes — the ladder drives both. Pick
the orchestration with one flag:

```bash
# Arm A — one pass: one agent builds the whole section, no delegation
uv run python -m ladder.run_ladder --mode direct  --provider llamacpp --base-url http://127.0.0.1:8001/v1 ...

# Arm B — the architect loop: split the spec, delegate each step
uv run python -m ladder.run_ladder --mode plan    --provider llamacpp --base-url http://127.0.0.1:8001/v1 ...
```

One caveat the record is honest about: `--mode plan` does not yet run on the
course's llama.cpp backend — the delegate path's backend support is on an
unlanded branch, and in the verdict run the plan arm hung to the deadline with
zero requests. So Arm A is a measured ladder result and Arm B's cost stays the
screened baseline until that branch lands.

**Lesson check:** one pass ~5× cheaper than the plan loop at equal or better
score, easy and medium
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).

## Validation

**Badge:** `screen`

Both one-pass tiers reproduced within a tight band — easy 11 and 12 requests,
medium 62 and 78 — and finished clean, where the plan loop's medium runs swung
widely and sometimes failed to converge
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
The quality column (the oracle score) held while the budget column (requests)
dropped about fivefold — the split bought nothing here and cost four workers'
worth of re-reads. The one point the screen cannot settle is the size at which one
agent runs out of room; that is where the loop was always meant to earn its cost,
and this run never reached it.

## Interpretation

The weakest badge is `screen` — a scratch n=2 per tier, plus one real ladder arm;
a lead, not a rate, and the plan arm is still unmeasured on this backend. The
honest reading is not "delegation is never worth it" — it is "with a single fixed
model, the split is overhead at this size." The orchestration knowledge still
matters: you must know how the split works to know when it does not pay, and to
recognise the tier gap or the oversized spec where it does. The next lesson keeps
one piece of the loop that pays even in a single pass — the architect's frozen
acceptance test, used as an exit-gate.

### What to try next

A rung past four phases — a spec one agent cannot hold — is the test that would
flip the verdict; if one pass degrades there while the plan loop holds, the loop
earns its cost exactly where this screen could not see it. It needs the plan arm
running on llama.cpp first, which the unlanded delegate-backend branch provides.

### Run it yourself

The two orchestration shapes on the medium suite (the plan arm pending the
delegate-backend branch on llama.cpp):

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --grade --repeat 3 --deadline 1800
```

!!! success "Key points"

    - Delegation splits a spec across an architect and fresh workers — real orchestration, real cost.
    - With one fixed model the split is overhead: one pass was ~5× cheaper at equal or better score.
    - It pays on a model-tier price gap (Junie Eco) or a spec too large for one context — not here.
