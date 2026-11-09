---
title: The Gate Is a Proxy
tier: hard
number: H3
time: 8 min read · 60 min to run
track: lessons
position: 3
prerequisites: [lessons/hard/dont-trust-the-self-exit]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# The Gate Is a Proxy

Build a multi-phase app in one go and a late change quietly breaks an early phase.
The flow builds it phase by phase, gates each one, and checkpoints every pass — but
its own gate is only a proxy for the real grade.

!!! abstract "Overview"

    **Questions**

    - How do you orchestrate a build across many phases without a later one breaking an earlier?
    - If every phase gate passes, why can the hidden grader still fail?

    **Objectives**

    - Follow the flow's phases — plan, examine, code, test — as tools the agent calls in order.
    - Read a hard run where every gate says PASS and the hidden grader says FAIL, and see why.

![A small robot foreman walking a line of finished rooms, stamping each door before it moves on, a ledger under its arm](../../assets/illustrations/lessons.webp){ .illustration }

## Problem

**Badge:** `screen`

A spec with seven phases is more than the model can hold in its head at once. Build
it in one go and the last phase elbows an early one — a change for phase 6 breaks
the route phase 2 passed, and nothing notices until the grade. So you split it into
phases and gate each one. But now the gate itself is the risk: the examiner writes
its own acceptance test, and that test is only a *proxy* for the suite's hidden
grade. A brittle gate false-fails correct code; a weak gate waves a wrong build
through. The examiner says done, and the oracle disagrees.

## Eval case

**Badge:** `screen`

**The condition:** a multi-phase suite — easy (1 phase), medium (4), hard (7) —
driven by the spec-driven flow, which registers the phases as tools the agent calls
in order and freezes a per-phase acceptance test as each gate. **Before:** a single
pass with no per-phase gate or checkpoint. **After:** the flow. The examiner's
frozen gates are the *proxy*; the suite's own hidden grader is the **oracle** that
settles whether a phase is really done
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md)).

## Evidence of the problem

**Badge:** `screen`

A single hard run carried all seven phases to green against their frozen gates — the
first time the flow had walked hard end to end — and then the oracle broke the news:
**`visible=PASS, hidden-grader=FAIL`**, 29 of 34 assertions passing and 5 failing,
all in the last two phases
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md)).
Every gate had said done. The gates for the late phases were simply too weak to
catch what the hidden grader checks — a passing proxy over a wrong build. Easy and
medium, where the gates were complete enough, came home 4/4 and 18/18 the same
day.

## Solution

**Badge:** `screen`

The flow answers the breakage, not the proxy gap — and you have to know which is
which. Three orchestration moves do the work. **Each phase runs as its own isolated
sub-agent** — planner, examiner, coder, reviewer — so one phase's context can't
bleed into the next. **Every passing phase is a git checkpoint**, so a later breaking
change reverts to the last good floor instead of poisoning the accumulated work.
**Every frozen gate re-runs cumulatively**, so a later phase can't pass by regressing
an earlier one. What none of that fixes is a gate that is itself too weak — for that,
the rule is the oracle: judge by the hidden grade, never the examiner's say-so.

### The code

Switch the workflow on and run it through its runner:

```text
/remedy on workflow/spec-driven-flow
```

```bash
uv run python learn/code/flow_run.py --suite hard --concurrency 1 --attempts 4
```

The phases are tools the agent calls in order — `plan → review_plan → code →
review_code → test` — each an isolated `pi` sub-agent sharing the workspace; only
the coder may write
([`extensions/mellum-flow.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-flow.ts)).
The orchestration that holds the build together is in the runner — a git checkpoint
per passing phase, and a revert when one breaks
([`learn/code/flow_run.py`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/learn/code/flow_run.py)):

```python
def git_checkpoint(workspace, msg):
    """Commit the workspace as a per-phase checkpoint (no-op safe if nothing changed)."""
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "--allow-empty", "-m", msg)

def git_revert_to_checkpoint(workspace):
    """Roll the workspace back to the last checkpoint (the last passing phase),
    discarding a broken phase so it never poisons the accumulated good work."""
    _git(workspace, "reset", "--hard", "-q", "HEAD")
```

And the gates re-materialise cumulatively before the authoritative run, so a coder
that edited or deleted an earlier gate gets it put back:

```python
def restore_gate(workspace):
    """Re-materialise EVERY frozen per-phase acceptance test into tests/ before scoring.
    A later phase cannot pass by regressing an earlier one; a deleted gate is restored."""
    for stale in (workspace / "tests").glob("test_gate_phase_*.py"):
        stale.unlink()
    for frozen in sorted((workspace / "plan" / "gate").glob("phase_*.py")):
        shutil.copy2(frozen, workspace / "tests" / f"test_gate_{frozen.stem}.py")
```

To load the flow as a graded remedy instead, name the unit:
`--remedy workflow/spec-driven-flow`.

**Lesson check:** flow runs 2026-10-29 — Easy 4/4, Medium 18/18, Hard 30/34 (n=1)
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md)).

## Validation

**Badge:** `screen`

The checkpoints and the cumulative gates do their job: the flow carried easy, medium
and all seven hard phases to green, where a single pass would have let a late change
break an early one unseen
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md)).
The oracle gap is the honest other half: on that hard run the gates passed and the
hidden grader failed 5 of 34, so the per-phase gate held the *build* together while
leaving a correctness hole its own tests never checked. Both readings are n=1 — a
mechanism settled, not a rate — and every number is llama.cpp's successor to the
oMLX host these first runs used.

## Interpretation

The weakest badge is `screen`. This is the orchestration H1 and H2 were building
toward: H1 split the work across agents, H2 gated a single pass, and here the gate
becomes a line of gates, one per phase, with git holding the last good floor beneath
them. The checkpoints make the *build* safe — a broken phase reverts instead of
poisoning the rest. The deeper lesson is the limit of any gate the model writes for
itself: it's a proxy, and a proxy can be too weak. The oracle is the hidden grade,
and a run isn't done because its own examiner says so — it's done when the grader
nobody can edit says so.

### What to try next

A stronger per-phase examiner — more exhaustive on the spec's negative and edge
cases — goes straight at the 5-of-34 gap, so the proxy tracks the oracle more
closely; the risk is the other failure, a brittle gate that false-fails correct
code, so it wants a run that scores the gate against the hidden grader at both ends.

### Run it yourself

The flow on the medium suite, its phases and checkpoints streamed in the terminal:

```bash
uv run python learn/code/flow_run.py --suite medium --concurrency 1 --attempts 4
```

!!! success "Key points"

    - A multi-phase build done in one go lets a late change break an early phase unseen.
    - The flow gates each phase, checkpoints every pass in git, and reverts a breaker to the last good floor.
    - The examiner's gate is a proxy for the hidden grade — all seven gates passed while the oracle failed 5 of 34.
