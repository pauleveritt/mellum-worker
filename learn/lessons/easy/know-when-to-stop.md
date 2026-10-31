---
title: Know When to Stop
tier: easy
number: E7
time: 4 min read · check owed
track: lessons
position: 7
prerequisites: [lessons/easy/too-many-tools]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# E7 · Know When to Stop

Pi has no turn cap, so a model that cannot finish works until its deadline. A blunt cap looks like the fix, but it fights the gate that re-checks the work; what stops cleanly is surviving the server, then settling when the tests pass.

!!! abstract "Overview"

    **Questions**

    - What actually makes a session run all the way to its deadline?
    - Why does a hard turn cap stop badly next to a gate that refuses a premature "done"?

    **Objectives**

    - See the two measured ways a session burns its deadline: a foreground server it waits on, and a stop-cap deadlocked against a verify gate.
    - See what stopped cleanly on the easy suite — survive the server, then gate the settle — and why a shorter run is the better pass.

![Know When to Stop: a placeholder picture until this lesson has its own](../../assets/illustrations/know-when-to-stop.webp){ .illustration }

## Problem

**Badge:** `screen`

Pi gives the model no turn budget, so a session can run until the deadline ends it. Two causes were measured on the easy suite (AgentClinic phase 1, local Q4), and neither is simply "the model needs a cap":

- **A server it waits on.** The worker starts `python main.py` in the foreground to check its work; the call never returns, and the harness ends the session at the 120 s stall — before it ever tries to finish ([pathology #8](../../pathologies.md)).
- **A cap fighting a gate.** Add a hard turn cap *and* a gate that refuses a premature "done", and they give opposite orders — the cap says stop, the gate says keep going — so the worker can neither act nor settle and churns to the deadline ([pathology #11](../../pathologies.md)).

## Eval case

**Badge:** `screen`

The easy task is AgentClinic phase 1. With `guard/cap-turns(120)` stacked on the verify gate, one rep ran **296 turns to the 1800 s wall**, its tool calls pinned at the 120 cap and `agent_settled` never firing — 349 "budget reached — stop" blocks against 193 "not done — keep going" refusals. Two sibling reps that instead stalled on a foreground `python main.py` were killed at the 120 s stall, 18–21 turns in, before the gate could act. (A built before/after lesson check is still owed; these are the campaign screens.)

## Evidence of the problem

**Badge:** `screen`

Recorded 2026-10-31 on local M3 Q4: the cap×gate deadlock ([note](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-31-cap-ncm-deadlock.md)) and the stall-before-settle screen in the [easy-remedy campaign](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-31-easy-remedy-campaign.md). Both are leads at n = 3, not rates.

## Solution

**Badge:** `screen`

**Remedy unit:** `guard/cap-turns`; apply it with `--remedy guard/cap-turns`.

A turn cap does bound a runaway session — but on its own it stops badly:

- It cannot help a run that **stalls before it ever tries to finish**: a foreground server never returns, so no budget is ever spent. That needs `tool/background-long-commands`, which backgrounds the command and hands back its startup output so the worker keeps moving.
- Next to a **refuse-to-settle verify gate it deadlocks**: reconcile the two — the gate stands down once the budget is exhausted, so the run settles on its real (incomplete) state instead of timing out — or do not run both.

What stopped cleanly on the easy suite, measured, was not a cap at all. Background the server so the worker survives to settle (`tool/background-long-commands`), then gate the settle with an external contract that re-runs and redispatches until it is green (`mellum-acceptance` + `mellum-ncm`). That stack took easy from 1/3 to **6/6** ([campaign](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-31-easy-remedy-campaign.md)). "Know when to stop" became "know the work is done" — and a shorter run is the better pass: 5 of the 6 settled in 17–20 turns, one needed 99.

**Lesson check:** not built yet.

## Validation

**Badge:** `conjecture`

No before/after lesson check has run on the 6-bit reference model. The claims here rest on the 2026-10-31 easy screens (local Q4) in the linked notes; building `learn/challenges/know-when-to-stop/` and its check is owed, and only then does a number belong in this section.

## Interpretation

The strongest step here is `screen`: the two deadline-burning shapes and the cap×gate deadlock are measured, but at small n and without a built lesson check. A hard cap is the obvious answer and the wrong one to reach for first — read this as the current lead, not a settled rule.

### Run it yourself

The before line, until the challenge and its after line exist:

```bash
uv run python learn/code/harness.py run --suites-dir learn/challenges --suite know-when-to-stop --remedy guard/break-repeat-loops,guard/stay-in-workspace,guard/refuse-whole-file-rewrite,guard/block-foreground-server,context/narrow-tools --repeat 1
```

!!! success "Key points"

    - Pi has no turn cap; a session that cannot finish runs to its deadline.
    - Two measured causes: a foreground server the worker waits on, and a stop-cap deadlocked against a verify gate — not a missing cap.
    - `guard/cap-turns` bounds a runaway, but deadlocks with a settle gate and cannot help a pre-settle stall; reconcile them, or prefer the verify-and-settle gate.
    - Measured on easy: background the server + gate the settle took 1/3 → 6/6, and a shorter run is the better pass.
