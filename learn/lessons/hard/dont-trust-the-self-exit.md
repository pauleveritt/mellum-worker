---
title: Don't Trust the Self-Exit
tier: hard
number: H3
time: 4 min read · about 1.5 h to run
track: lessons
position: 3
prerequisites: [lessons/hard/frozen-gates-and-checkpoints]
authors: [Andre van Zuydam]
backends: [vllm]
---

# H3 · Don't Trust the Self-Exit

The worker decides when it is done, and can stop confident on a self-written
test that covers less than the spec. Define done by a test it did not write and
cannot change, re-run after every stop, and hand back each failure.

!!! abstract "Overview"

    **Questions**

    - Why is a passing test the worker wrote not proof the task is done?
    - What makes an acceptance test safe to exit on?

    **Objectives**

    - Name the three properties of a safe exit: external, complete, unweakenable.
    - Run the flow's free mode, where the harness, not the agent, decides done.
    - Explain why an external test alone did not reach green, and what did.

![A small robot holding up its own small checkmark while a larger robot at the line checks a clipboard](../../assets/illustrations/dont-trust-the-self-exit.webp){ .illustration }

## Problem

**Badge:** `screen`

A worker that writes its own test from the spec writes the part it
understood. The test passes, so it stops. Nothing outside it checks the part
it dropped, and its final message reads exactly like a real finish.

## Eval case

**Badge:** `conjecture`

**Before:** `preset:medium` through `harness.py`: the worker writes and runs
its own tests and decides when it is finished. **After:**
`flow_run.py --flow-mode free`: an examiner pass freezes the phase's
acceptance test before any build, the coder works with ordinary tools, and the
harness re-runs the frozen test after each stop and re-dispatches its failure,
up to `--attempts` rounds.

## Evidence of the problem

**Badge:** `screen`

A single-shot probe (2026-10-18, n = 1, greedy, `mlx_lm.server`, not Pi) gave
the worker Phase 4's spec. It added a `status` field and `resolve` and
`reopen`, but **no `id` field**, and its own tests asserted only status
changes. The hidden oracle's `first.id != second.id` would raise. The
2026-10-29 flow run showed the same shape one level up: a re-frozen phase 4
gate checked only that the board loads and posting redirects, the phase
passed, and the hidden grader missed all five phase 4 checks.

## Solution

**Badge:** `screen`

**Remedy unit:** none: the verified exit is `--flow-mode free` in `learn/code/flow_run.py`, not a unit.

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

A self-exit is safe only when the test that defines done is:

- **External:** the worker did not write it (here, the examiner did, from the
  spec, before any code).
- **Complete:** it covers the whole spec, not the subset the worker chose.
- **Unweakenable:** the worker cannot edit or delete it (the harness restores
  the frozen copy before every run).

In free mode the harness enforces two invariants and nothing else: a frozen
test exists before any build, and the exit is verified by re-running it. On a
failure, the tail of the test output becomes the next round's message.

## Validation

**Badge:** `screen`

With an external, complete test but no freeze and no re-dispatch, the
hand-driven Phase 4 probe added the `id` field but did not reach green. Adding
only the freeze, the re-dispatch of each failure and a larger per-turn budget,
it converged at turn 25: the acceptance test and the hidden oracle, never
shown to the worker, both passed. n = 1, greedy, a hand-driver against
`mlx_lm.server`, not the suites. Free mode on Bronze, Silver or Gold is not
measured as a lesson yet.

## Interpretation

The weakest badge is `screen`, and it is a lead, not a rule. The external test
redirected the worker to the missed requirement; convergence came from not
trusting the stop. "Complete" is the load-bearing word: the flow's own weak
gate passed a wrong build, so the judgment moves up a level and does not
vanish. The hidden grade stays the oracle.

### Run it yourself

Before, then after, on Silver:

```bash
uv run python learn/code/harness.py run --suite medium --remedy preset:medium --repeat 3 --grade
uv run python learn/code/flow_run.py --suite medium --flow-mode free
```

!!! success "Key points"

    - A worker's own passing test proves only the part of the spec it chose to test.
    - Exit on a test that is external, complete and unweakenable, and re-run it after every stop.
    - In one probe the freeze and the re-dispatch, not the external test alone, reached green.
