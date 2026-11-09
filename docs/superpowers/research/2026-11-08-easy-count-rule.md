# Easy, Vanilla against Base: the rule, fixed before the count

## For Andre

- **What this is:** the one short rule for a single counted Easy run, written before its first
  session, so the result cannot be re-read afterwards. Paul asked for it on 2026-11-08 after four
  days in which the effects held but the bar kept moving.
- **The bar moves from 20% to 3 times.** Paul's call: up to 3 times Vanilla's cost for a session
  that finishes the spec. This replaces R.1's 20% budget limit for this run.
- **Base is two units,** `tool/bounded-commands` and `check/mediated-test-settle`.
- **What to look at:** whether a mediated test written without seeing the grader still lifts the
  hidden grade. Easy's earlier test mirrored it.

**What is measured.** Nothing yet: this note fixes what will be.

**What is conjecture.** That Base beats Vanilla here. F.6's gain used the grader-mirroring test.

## Ladder run

Pod A40 under its host card, one session at a time, `scripts/r1_batch.py`, round-robin, each
session as `mellum-session` and graded as `mellum-grade`. Arms in
[`easy-final-arms.json`](../../../scripts/pod/easy-final-arms.json): `vanilla` and `base`, both on
`--arm vanilla`. n = 32 per arm, Easy only, budget 128 requests and 64,000 output tokens, stall
180 s, `bounded` at 30 s, up to 5 re-dispatches. The configuration is frozen at the tag
`checkpoint-2026-11-08-easy-final`; a change after it voids the count.

**Go or no-go first.** The same two arms at n = 6. The count starts only if Base has more strict
passes than Vanilla and at least 3 of 6, and every session was graded. Otherwise it stops there and
Paul decides.

## The rule

A **strict pass** is all 13 hidden checks, the project's own tests, and the lint gate. The
report gives 13-check full passes beside it.

Cost is the median requests and the median output tokens over **all** 32 sessions of an arm,
stalled ones included. Base passes if all three hold:

1. Base has at least 8 more strict passes than Vanilla (R.1's 6 of 24, at n = 32).
2. Base's median requests are at most 3 times Vanilla's.
3. Base's median output tokens are at most 3 times Vanilla's.

**Correction, 2026-11-09:** this rule did not say which output-token count it meant. The count used
the budget proxy's charge, `budget.spent.output_tokens`, which includes compaction summaries.

If Base passes, `preset:base` and `preset:easy` become those two units. If not, both stay `[]`.
Either way the result goes in `evals/` with the per-check table. No other arm is added.

## Persuasion → enforcement

Both of Base's units are enforcement: a timeout on every bash call (`tool_call`) and a re-run of an
external test before the session may end (`agent_before_settle`). Vanilla adds neither. The only
persuasion in the run is the suite's own notes, the same for both arms.

## What would falsify this / Risks

- Base missing the 8-pass margin falsifies "the re-run earns its place" on this suite.
- The go or no-go screen is n = 6 and can stop a real effect or admit a weak one.
- One suite says nothing about Medium or Hard.
- The mediated test was written from the roadmap by an agent barred from the grader, then proved on
  fixtures. A roadmap gap is a gap in the test too.
