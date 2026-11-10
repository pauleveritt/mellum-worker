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

### Rejoinder to your summary

Our reply to your summary, "Here's where the fork landed". Each point gets one verdict, **supports**,
**relates** or **refutes**, with the record behind it; numbers in brackets are proposals above.

**The short version.** We agree with your headline: for a fixed small model, a harness guarantee beats a
prose rule. Our counted runs are the strongest evidence for it that either of us has. Where we differ
is Easy. Your summary says Easy is won by guidance, not guards. Under a thirteen-check grade, the
guidance did not move Easy, and two deterministic units did.

#### The case for guards and deterministic checks

- **Matched and preregistered, n = 32 per arm** ([count](2026-11-09-easy-count-result.md)). Base is two
  units and no prompt text: Pi's bash timeout set on every call (`tool_call`) and an external test
  re-run at settle (`agent_before_settle`). Strict passes 25 against Vanilla's 2; full thirteen-check
  passes 30 against 2; stalls 0 against 7, all seven on a server start. Output per full pass was 36,633
  against 151,366 (Vanilla's figure rests on two passes). Base missed the count's preregistered cost
  clause (4.47× the median); we report that, and the presets stay empty.
- **The same test, as prose or as a gate** ([F.6](2026-11-08-f6-held-pod.md), n = 24 per arm, Easy).
  Showing the model the acceptance test: 6 full passes. Re-running it at settle and sending failures
  back: 16. Both: 11. Vanilla: 2. The enforcement half earns the gain; the persuasion half costs some.
- **Prompt units under the same grade.** `prompt/name-the-layout` at n = 12: mean 9.50 checks against
  Vanilla's 10.58, and no full pass ([R.1](2026-11-07-r1-easy-remedies.md)). `prompt/verify-the-spec`
  missed Easy's main failure, the title override, in 3 of 3 ([screen](2026-11-08-verify-the-spec-screen.md),
  a lead). In the count, Vanilla missed that check in 28 of 31 graded sessions; Base missed it once.
- **The bound**: 0 stalls in 122 bounded sessions, against 25 in 130 plain Vanilla sessions
  ([census](2026-11-09-phase-worker-review/stalls.md); descriptive totals, not a pooled rate).
- **Phase 2, from verified checkpoints** ([screen](2026-11-09-easy-base-spread.md)): Base accepted 9 of
  12, Vanilla 0 of 6. The first red verdict in all 12 Base runs named the model-contract test; Vanilla,
  with no gate, missed the matching hidden check in 6 of 6.
- **Only grading outside the session catches some failures.** Phase 2's three rejections all had a
  green settle gate: two failed lint, one had edited the supplied test. In the count, all five Base
  attempts that passed every hidden check but not strictly had edited the supplied test.

#### Point by point

**1. "A harness guarantee beats a prose rule, every time." Supports.** The section above is our
measured version of it.

**2. The shape: Vanilla floor, thin worker, explicit remedies, presets as results. Supports.** It is
your 2026-11-02 design, and we kept it. Two places where your `main` does not match it yet: the worker
registers the `delegate` tool by default (11), and the `easy` and `medium` presets list three prompts
and a guard that no counted run has credited (12). By your own rule, those presets are inputs.

**3. "Easy is won by guidance, not guards." Refutes, under a thirteen-check grade.** Your 6/6 was
graded by four hidden checks. In our matrix, that four-check grader rejects 1 of 6 Easy Phase 1 defect
builds, against 6 of 6 for ours ([F.7](2026-11-09-f7-qualify-acceptance.md); chosen builds, not a
defect rate). Under thirteen checks, the prompt lines did not beat Vanilla, and the two deterministic
units did. "The guards fired zero times" was true for your units in your runs. Ours had work to do:
Vanilla stalled 7 of 32 times on a server start, and Base none. We agree on reading `guard_blocks`
first. Our compile/import check and log-follow guard never acted in their screens, so we left them
unjudged rather than credited.

**4. "The worker's done can't be trusted"; a frozen test closes it. Supports, strongly.** Same
mechanism, and the core of Base. Two differences matter:
- **Visible or held out.** Your verdict run's gate is a visible test. On Easy, showing the test gave 6
  full passes in 24, against 16 when it was only re-run at settle (F.6).
- **A gate is only as complete as its test.** In our matrix, `test_medium.py` accepted three builds
  with id-sequence defects (`separate_route_counter`, `renumber_on_append`, `route_overwrites_with_max`),
  the same class as the Phase 4 miss it closed. Our Medium tests reject all 33 chosen defects (3, 16).
  The gate code also has no timeout, reads exit 0 as green, and replaces earlier gates' messages (17).

**5. One pass beats the architect loop. Relates.** We have not run the architect. Our Base is already
one agent. The 5× is still unpaired, since your verdict's plan arm hung with 0 requests. For a spec too
big for one context, we built a third option: one phase per session, starting only from a checkpoint
that trusted grading accepted (20). Phase 3 was accepted 12 of 12 that way, as a screen.

**6. The live-server spiral, and a guard that fixed it. Supports the case for guards.** Your strongest
Medium result is a guard. It relates to ours (15) in a specific way:
- **Our bound** sets Pi's own timeout and classifies no command. It ends every hang, but a model can
  still relaunch and poll.
- **Your guard** classifies commands and stops the loop. It needed three fixes in three days
  (`f0e31ea`, `d07921d`, `92169aa`), the same path our foreground guard took before we moved to a bound.
- We have not seen the spiral on Easy (R.1a: no server start in 90 tool calls, n = 1). The two belong
  in one paired run on Medium.

**7. "Thinking spends the turn", and the prompt is the only lever. Relates; refutes "only".** Thinking
is a harness switch: your verdict run used `--thinking low`, and Pi exposes `setThinkingLevel`
(llama.cpp has on and off, not a dial). The one-sentence prompt did not change thinking share (86–92%
against 88%) or cost per accepted phase on our Easy Phase 2 ([R.1b](2026-11-09-r1b-think-briefly.md)),
and your Easy n = 6 was negative too. Your Medium gain came with a turn cap. Base has none; the proxy
bounds each session instead (7). We agree that nothing transfers between tiers for free.

**8. The flow's gate is only a proxy; the hidden grader is the oracle. Supports, and goes further.**
The hidden grader can be wrong too. The suite's original Medium grader rejected valid captioned builds
and missed defects, so we qualify each grader against known builds and keep its versions (2, 3, 4).
Checkpoints advance only on trusted acceptance, never on an examiner's gate (20).

**9. Not the model's fault: the serving host, and Mac Q4 matching a rented A6000. Supports.** Pinning
the serving stack is our host card (8). A parity screen holds for one build, though: on the M5 Max,
llama.cpp b11669 returned NaN perplexity on Metal and b12110 agreed with the CPU within 0.57%
([F.5](2026-11-07-f5-run-trust.md)). So each counted run records its host card, rather than relying on
a parity check made once.

**10. Every number is a screen; the next rung is past four phases. Supports the first, relates to the
second.** Everything in your summary is a screen; our Easy count is one preregistered run. Before a
longer spec, we would qualify that rung's oracle (your rung-13 `check_agentclinic` is not in our matrix),
then pair three arms on it: one pass, the architect, and phase-at-a-time. Our Hard suite has seven
phases and four migrations, with a mediated test for each of its eleven prompts.

### What we do not claim

- No rate from a screen: the overnight Easy Phase 2–3 screen, R.1a and the F.6 settle-plus-bound
  screen are leads (16, 20).
- No acceptance rate or saving from the phase boundary's guarantees; they are unit and replay tested (17, 18, 20).
- `guard/supplied-tests` is unmeasured (19). Linux cleanup of leftover session processes is unexercised (8).
- The grader matrix counts describe the witness builds we chose, not defect rates; your `test_medium.py`
  is a visible test written for your stack (3).

## Ladder run

No run was made for this index. Each issue links the records behind it. The rejoinder asks for two
paired runs (Base with and without your live-server guard on Medium; three arms on a spec past four
phases); they are proposals, not results.

## Persuasion → enforcement

The proposals are enforcement: a Pi hook (`tool_call` in 15; `tool_call` and `tool_result` in 19;
`agent_before_settle` in 16 and 17) or the harness outside Pi (1–9, 18, 20). Proposal 13 changes how
prompt text is delivered (the `context` hook), not what it says. 10 and 12 are decisions. No prompt text
is offered; the one prompt-shaped change is failure feedback that reports facts (17). The rejoinder's
first part is the measured case for this section.

## What would falsify this / Risks

- A paired run on your stack that passes our thirteen-check Easy grade at lower cost would change the
  Architecture and Acceptance readings.
- A valid build that our grading rejects needs a dated correction. One is known: an exact
  `Complaints Board` heading on Easy Phase 2 (5).
- "Works alone" is a reading of imports, not a run on your `main`.
- A counted run where your three prompt lines beat Vanilla on thirteen checks would overturn the
  rejoinder's point 3. Base's Easy gain is one suite, one host and one model.
