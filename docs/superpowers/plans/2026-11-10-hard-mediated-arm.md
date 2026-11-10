---
phase: mediated-test
feature_cycle: backlog/the-mediated-test
cycle: 1
lifecycle: active
---

# Hard suite: a mediated acceptance-test arm — plan

Answers upstream [pauleveritt/mellum-worker#5](https://github.com/pauleveritt/mellum-worker/issues/5).
Reopens the parked backlog lead "The mediated test" for the hard suite: give the
worker an external, complete, frozen acceptance test per phase, run it after each
phase prompt, and re-dispatch its failure, with the hidden grader still the final
oracle. The medium version of this loop is already built and measured on the fork
(the verify gate plus `ladder/fixtures/acceptance/test_medium.py`); this carries
it to the hard suite and wires it as an arm in `learn/code/harness.py`.

## What is measured / what is conjecture

- **Measured here.** The phase-1 acceptance test is complete: it passes the done
  reference and goes red on a real phase-1 miss (see Workstream 1, done).
- **Conjecture, to be measured by the arm.** That mediation turns the hard
  0/3 into separation at a cost well under the architect loop. Hard is 0/3 for
  both Baseline Pi and the Baseline Worker today (issue #5's table); the worker
  spends about 108 turns and 541 s per hard session and still misses 21 hidden
  checks. No claim of a rate until the n=1 screen, then a preregistered run.

## What already exists — reuse, do not rebuild

- `extensions/mellum-verify.ts` — the `agent_before_settle` gate. Runs
  `VERIFY_TEST` with `PYTHONPATH=cwd`, and while red returns `{continue:true}`
  naming the failing test functions, up to `VERIFY_MAX` (default 5). Loads with
  `-e`, so it fires on the one-shot child's settle in any session.
- `ladder/fixtures/acceptance/test_medium.py` — the authoring convention: written
  from the spec, a superset of the hidden oracle, plain-substring and delta-based
  so it is complete without being brittle. The new hard tests mirror it.
- `learn/code/suites/hard/grader/` — the hidden oracle, per phase
  (`test_phase1_home.py` … `test_phase4_resolve_reopen.py`, plus `_contract.py`
  and `_seed.py`). The harness copies it in only after the worker exits.
- `ladder/fixtures/agentclinic-done` — the complete reference build. The green
  leg of the completeness proof runs against it.
- `learn/code/harness.py` — already sets `ACCEPTANCE_PROMPT` per phase; the arm
  extends this, it does not start from nothing.

## The design decisions

- **Author the acceptance tests by hand, from the spec.** Not a per-run examiner
  model (keeps the one-pass cost, no extra model), not the grader (that is coding
  to the eval). Each test is a superset of that phase's hidden oracle: every check
  the oracle makes, plus the spec items it leaves thin.
- **Frozen, and visible, per Paul's model.** The test sits in the workspace so the
  worker can read and run it, and is restored from a read-only copy before every
  attempt, so the worker cannot weaken it. It lives outside the worker write
  scope. This is the one point to confirm with Paul; the reply on #5 states it.
- **Re-dispatch policy.** After a phase prompt settles, run the acceptance test;
  on red feed back only the failing test function names and re-dispatch the same
  phase on the same workspace, cap 5; on green send the next phase. The effort
  ramp stays out of the arm, so mediation is the only variable against the
  Baseline Worker controls (same model, prompt, tools, facts, guards).
- **The hidden grader stays the oracle.** Copied in once, after exit. A passing
  acceptance test with a failing hidden grader is reported a fail, not a pass.

## The loop

```text
phase prompt -> worker edits -> frozen acceptance test
  red:  feed back the failing test names, same workspace, re-dispatch (cap 5)
  green: next phase prompt
after all phases: hidden grader, once
```

## Workstreams

### 1. Author the phase-1 acceptance test — DONE

`ladder/fixtures/acceptance/test_hard_phase1.py`, written from `prompts/01.md` as
a superset of `grader/test_phase1_home.py`. Completeness proven before any model
run:

- **Green:** all six pass on `ladder/fixtures/agentclinic-done`.
- **Red:** removing `lang="en"`, the Complaints nav link, and the python.org
  favicon each turns its check red (three fail, three still pass), and the
  template restores clean. A test that could not go red would not be complete.

The green-on-done leg also owes a run of the hidden phase-1 oracle itself against
the done reference, to confirm both pass together; that is inherent to the suite
(the grader is authored against `agentclinic-done`) and is re-confirmed when the
arm runs.

### 2. Author the phase-4 acceptance test — DONE

`ladder/fixtures/acceptance/test_hard_phase4.py`, from `prompts/04.md`, a superset
of `grader/test_phase4_resolve_reopen.py`, reusing the Phase-4 assertions proven
in `test_medium.py`. This is where the hard misses concentrate: the complaint id
must be an automatic default on the dataclass, so two direct constructions get
distinct ids; an id assigned only in the add route passes the happy path and
fails here. Completeness proven:

- **Green:** all seven pass on `ladder/fixtures/agentclinic-done`.
- **Red:** replacing the id's auto `default_factory` with a fixed `id: int = 0`
  (the id-not-auto-on-dataclass miss) turns the two deep-invariant checks red
  (distinct direct-construction ids, distinct seed ids) while the happy-path
  route checks still pass - the exact shape the invariant guards. `models.py`
  restores clean.

### 3. Wire the mediated arm into `learn/code/harness.py` — DONE

`--mediate` with `--acceptance PHASE:PATH` (repeatable) and `--verify-max N`
(default 5), layered on `--arm worker` so mediation is the only change from the
Baseline Worker. Per gated phase the harness runs the frozen acceptance test
(`run_acceptance`) from its canonical path outside the workspace, and while red
re-dispatches the same phase on the same workspace with the failing test names
(`corrective_prompt`), up to the cap. The test is also dropped into the
workspace under `acceptance/` before the pristine snapshot, so the worker can
read and run it (and `grade()` excludes that dir); the gate always runs the
canonical copy, so editing the visible one cannot weaken it. The hidden grader
is untouched. Each phase's attempts, pass and remaining failures land in
`run/acceptance.json`, and `run.json` carries `mediated` and `acceptance`.
`--repeat`, `--deadline`, `--arm` and scoring keep working.

Test-first (`learn/code/tests/test_harness.py`, shown red first): `parse_failing`
reads both pytest summary formats; `corrective_prompt` names the checks and
protects the test; `parse_acceptance_map` pairs phase and path; `run_acceptance`
reports green and red against a real workspace; and a fake-pi that fails then
passes drives the full re-dispatch loop, asserting `acceptance.json` records two
attempts, a pass, and the visible copy. 155 learn/code tests pass, 717 node.

Open recording refinement for the measure step: fold per-phase turns and wall
into `acceptance.json` (the whole-run turns and wall are already in `run.json`).

### 4. Measure — the real check

Hard sanity at **n=1** first (issue #5's acceptance criterion). Only if the n=1
screen shows a signal, a preregistered n=3 against the Baseline Worker: same
model, prompt, tools, facts; mediation the only change. Stream it in a Terminal
tab with `watch_ladder.py` (skill §9). Report full-pass rate, attempts, turns,
total requests, wall, and the hidden-grader passes, against the 0/3 baseline and
the architect loop's cost.

### 5. Record and decide

A dated research note under `docs/superpowers/research/` with arms, n, the rule
and the result (screens first, preregistered runs to decide). If mediation moves
hard at a cost well under the architect loop, note whether it should become a
ladder mode (one-pass + `--acceptance-test`, like `--mode plan`). The win or
learning lands as its own PR to upstream, carrying the record (skill §10, §11).

## Out of scope (now)

- A per-run examiner model (Tier-2 dynamic); easy-tier or medium-tier gating.
- A preregistered `run_ladder` verdict — a follow-up once the n=1 screen shows
  the arm works.
- Any shipped worker change: this is eval-harness infrastructure. The measured
  settings freeze does not apply (no prompt, template, sampling, guard or remedy
  change); the committed artifacts are the acceptance-test fixtures, the harness
  arm, and the research note.

## Verification

- Workstream 1 and 2 dry-runs (green on done, red on the miss) gate the work
  before any model run.
- `node --test tests/docs-caps.test.mjs` and `npm test` stay green (the fixtures
  are not a package code path).
- The n=1 hard screen, tally streamed in a Terminal tab, gates the n=3.
