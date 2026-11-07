# Worker prompt: spec-led re-gear (v11 → v12) — a lead

Date: 2026-11-01. Lifecycle: open lead (not promoted).

## What is measured / What is conjecture

**Measured** (recorded, n=3 per arm, local llama.cpp Q4_K_M on :8002, the
`--prompt` ablation): on the hidden oracle, a spec-led prompt (v12) is never
worse than the shipped v11 and clearly better on the discriminating rung.

**Conjecture**: that this holds at higher n, on the full `mode` product (facts
block + installed template, not the `--prompt` ablation), and that it does not
regress the test-present case. Not yet run.

## The question

v11 opens "You make one failing test pass." The agentclinic rungs (and the
shipped `/mellum` worker) often present a task as a spec with NO visible test,
graded by a hidden oracle. Does a prompt re-geared to "implement the spec; a
test is optional" work better on those spec-only tasks?

## Two findings about the measurement itself

1. **The standard screen rig cannot see prompt-vs-spec framing.** `scripts/
   screen.sh` / `--acceptance-test` rewrites the task sentence to "Make
   tests/<X>.py pass. Test command: pytest tests/<X>.py" and copies the test
   into the workspace (`run_ladder.py:433,:577`). So the rig always hands the
   model a visible test — it measures test-following, not spec-implementation.
   This is why prompt wording measured null before (LC.11): the task sentence
   carries the instruction. The question is only testable WITHOUT
   `--acceptance-test`.

2. **`facts_cmd_pass` is meaningless on spec-only tasks.** `check_agentclinic`
   scores `passed = facts_cmd_pass AND hidden_pass AND …`; `facts_cmd_pass` is
   `pytest tests -q`. On a rung whose `tests/` ships empty and whose prompt does
   not ask the worker to write tests, pytest collects nothing and "fails" every
   run, so overall `passed` is 0/N for all arms, uninformatively. Judge by
   `hidden_pass` (AGENTS.md: "judge on the hidden grade"). Observed: rung 6
   `facts_cmd_pass=False` for all; rung 9 `=True` for all — so on rung 6 the
   hidden oracle is the only valid signal, and on rung 9 it is the separator.

## Arms

- A = v11, the shipped `prompts/mellum-worker.md`.
- B = v12, a candidate: spec-led opening, explicit that a task may have no test
  ("do not write one to grade yourself and do not go hunting for one that is
  not there — check against the spec clause by clause"), every v11 guard kept
  (no-server, in-process TestClient, don't weaken a given test, no network) and
  the Phase-4 auto-id clause kept. Passed via `run_ladder --prompt`; the shipped
  file was never edited.

Fixed: `--mode direct --profile tuned --repeat 3 --effort-ramp --thinking off
--guards`, no `--acceptance-test`, no redispatch (faithful to the one-shot
`mode` product). Scored by `check_agentclinic`'s `hidden_pass`.

## Result (hidden oracle)

| rung | task | v11 | v12 |
|------|------|-----|-----|
| 6 | phase-1-home (easy spec) | 2/3 | 3/3 |
| 9 | phase-4 resolve/reopen (auto-id) | 0/3 | 2/3 |

Per-rep turns/wall and stops: `runs/2026-11-01-promptscreen-{v11,v12}-rung{6,9}`
(git-ignored). The shape:

- v11's misses are the predicted thrash — rung 9 r2/r3 error-stopped at 174 and
  84 turns; rung 6 r1 error-stopped at 123 turns and wrote outside the
  allow-list. v12's passes are clean stops at roughly half the turns and wall.
- v12's one rung-9 miss was a length-stop at 18 turns (ran out of the
  effort-ramp's initial token budget), a budget artifact v11 also hit once —
  not a prompt failure.

## Decision

A **lead**, not a decision. No promotion. `prompts/mellum-worker.md` stays v11.
The signal is consistent (v12 never worse, clearly better on the auto-id rung)
and the v11 failure mode matches the hypothesis, which is enough to keep the
candidate but not to ship it.

## What would falsify this / Risks

- Falsify: at higher n the rung-9 gap closes to within noise, or v12 regresses
  the test-present case (the `--acceptance-test` rig, where a visible test
  exists), or the gain vanishes under the full `mode` product (facts block +
  installed template) rather than the `--prompt` ablation.
- Risk: n=3 single-dispatch on local Q4 is thin; two of v11's five misses were
  length/error stops, which add variance. The `--prompt` ablation is direct
  mode, one step removed from the shipped `mode` path.

## Reopen condition

A preregistered deciding run: higher n on rungs 6 and 9, plus a no-regression
check on the `--acceptance-test` rig. If v12 holds, promote via the product
path (edit `prompts/mellum-worker.md`, `node build.mjs`, the template-drift
test), as its own change with its own ladder record in `evals/`.

## The v12 diff from v11 (load-bearing lines)

- Opening: "You make one failing test pass. You work in this repository,
  offline." → "You implement a spec in this repository, offline. Sometimes a
  failing test points the way; often only the spec does."
- Added to "how to check": "If there is NO test, do not write one to grade
  yourself and do not go hunting for one that is not there — check your code
  against the spec directly, clause by clause."
- Softened "the named test" → "a test you were given" (there may be none).
