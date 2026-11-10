# Handover to Andre: an index of proposals, to take or refuse one at a time

## For Andre

**Date:** 2026-11-10. **From:** Paul. **What this is:** the index of everything since the 2026-11-07
re-boot, split into proposals. Each proposal is one issue in your repo, titled `(Group) Proposal title`.
Take or refuse each one on its own; nothing is meant to merge in one go.
**What is measured:** the run records, deterministic tests and saved-build replays each issue links.
**What is conjecture:** savings, later phases, Medium reliability and Hard.

**Where the code is.** Branch `andre-integration` on
[pauleveritt/mellum-worker](https://github.com/pauleveritt/mellum-worker/tree/andre-integration). Paul has
read-only access to your repo, so the PR from that branch is a **reference copy**, where you can read
everything together and CI can run. It is not a request to merge.

**What each issue holds.** A short opening: the problem as you have seen it in your runs, your side of
it (your commit, unit or note), and ours, with the Pi hook it uses and what that hook guarantees. Below
that: evidence, what refusing costs, and an agent section. The agent section lets an agent try the
proposal for you: branch from your `main`, bring over only that issue's files from `andre-integration`
at a pinned commit, run the tests that prove it, report conflicts with your code, and stop.

*Rewritten 2026-11-10 as this index. The earlier version, a table of ten offers with dated updates, is
at commit `aa885f66`; its content now lives in the issues.*

### Where we agree

We reached the same core from two directions: re-run a test the model did not write before it may stop,
keep that test out of its sight, stop a server start from hanging the session, count requests as cost,
and expect a prose rule to land unreliably on a fixed small model. Your preregistered rung-13 run passed
one pass 3 of 3 at 72, 34 and 24 requests. Its plan arm did not run (it hung on llama.cpp), it has no
Vanilla arm, and its oracle is not one our grader matrix tested. Both sides found `think-briefly` no help
on Easy. Where our results differ, a paired run on one stack decides.

### What is trusted, and what is advice

The decision about a build is made outside the session: hidden grading on a disposable copy, with the
suite's own dependencies, which nothing the session writes can change. Everything inside the session,
including the settle gate, its log and its environment, is advice: it steers the model, and a determined
session could get around it. This is why Measurement is the first group.

### Proposals

Issue links are added here once filed. "Works alone" is our reading of whether the issue's files run on
your `main` without the others; each issue's agent section checks it.

**(Measurement): the evals and graders themselves**

| # | Proposal | Problem | Depends on | Works alone? |
| --- | --- | --- | --- | --- |
| 1 | Single-source suites | Prompts and specs said a phase twice and disagreed; one prompt cued an import | none | partly: needs `--specs` in `harness.py` |
| 2 | Hidden grading on a disposable copy | A build can pass on its own pytest config or an edited supplied test | none | partly: `grading.py` and its call in `harness.py` |
| 3 | Graders qualified against witness builds, with versions | A grader can pass a known defect or fail a valid build | 2 | no |
| 4 | Medium grader corrections | A captioned status fails, and direct and route ids are never checked together | 2, 3 | yes: grader files |
| 5 | Easy at thirteen checks, and in four phases | Four checks leave most of Phase 1 ungraded | 2, 3 | no |
| 6 | Honest budget fields in `run.json` | Wall time came from the trace, and turns equalled requests | none | partly: `harness.py` |

**(Run trust): runs we can count**

| # | Proposal | Problem | Depends on | Works alone? |
| --- | --- | --- | --- | --- |
| 7 | Budgets enforced at a proxy | Cost is reported after the fact, not bounded | 6 | partly: `budget-proxy.mjs` and harness flags |
| 8 | Host cards and clean runs | A run on a drifted server, a shared venv or a leftover port-8000 server still counts | none | partly: `conformance.py` and harness |
| 9 | Counted runs on a rented pod | Long batches tie up one Mac | 7, 8 | no |
| 10 | The cost rule for phase work | A multiple of Vanilla's cost moves with an arm that rarely finishes | 7, 20 | yes: a decision |

**(Architecture)**

| # | Proposal | Problem | Depends on | Works alone? |
| --- | --- | --- | --- | --- |
| 11 | The floor: no default `delegate` tool or nudge | A unit's effect cannot be credited when the worker bundles behaviour | none | yes, but check `--mode plan` |
| 12 | Presets are results | Presets list units no counted run has credited | 11 | yes, but empties your presets |
| 13 | Prompt fragments once per task | A fragment appended to every user message repeats with each prompt and never shows in the session history | none | partly: `mellum-task.ts`, `task-prompt.ts` |
| 14 | Remove the dead extensions | Extensions outside the floor that nothing loads still carry code and tests | none | yes, after checking nothing of yours loads them |

**(Stalls)**

| # | Proposal | Problem | Depends on | Works alone? |
| --- | --- | --- | --- | --- |
| 15 | Bound every bash call with Pi's own timeout | A server started in the foreground hangs the session to its cutoff | none | yes: one file |

Your side of 15 is `guard/foreground-server` and `guard/no-live-server`, and the issue sets them side by side.

**(Acceptance tests): what decides "done"**

| # | Proposal | Problem | Depends on | Works alone? |
| --- | --- | --- | --- | --- |
| 16 | Re-run a held-out test at settle | The model stops on its own word, with a test it wrote | 1, 2, 8 | no |
| 17 | Gate-runner fixes, for your `mellum-verify` too | A hung test stalls settle, a later gate's message replaces an earlier one, exit 0 reads green | 15 (`bounded.ts`) | yes, with `bounded.ts` |
| 18 | Keep the held-out test hidden | Feedback named the test's path, and sessions went looking for it | 16 | no |
| 19 | `guard/supplied-tests` (a lead) | A session edits the supplied test until it passes | none | partly: restore per prompt needs harness |

**(Phase work)**

| # | Proposal | Problem | Depends on | Works alone? |
| --- | --- | --- | --- | --- |
| 20 | One phase at a time, from verified checkpoints | Phases advance on the model's word or an exhausted send-back cap | 2, 5, 16 | no |

### What we do not claim

- No rate from a screen: the overnight Easy Phase 2–3 screen, R.1a and the F.6 settle-plus-bound
  screen are leads (16, 20).
- No acceptance rate or saving from the phase boundary's guarantees; they are unit and replay tested (17, 18, 20).
- `guard/supplied-tests` is unmeasured (19). Linux cleanup of leftover session processes is unexercised (8).
- The grader matrix counts describe the witness builds we chose, not defect rates; your `test_medium.py`
  is a visible test written for your stack (3).

## Ladder run

No run was made for this index. Each issue links the records behind it.

## Persuasion → enforcement

The proposals are enforcement: a Pi hook (`tool_call` in 15; `tool_call` and `tool_result` in 19;
`agent_before_settle` in 16 and 17) or the harness outside Pi (1–9, 18, 20). Proposal 13 changes how
prompt text is delivered (the `context` hook), not what it says. 10 and 12 are decisions. No prompt text
is offered; the one prompt-shaped change is failure feedback that reports facts (17).

## What would falsify this / Risks

- A paired run on your stack that passes our thirteen-check Easy grade at lower cost would change the
  Architecture and Acceptance readings.
- A valid build that our grading rejects needs a dated correction. One is known: an exact
  `Complaints Board` heading on Easy Phase 2 (5).
- "Works alone" is a reading of imports, not a run on your `main`.
