# Reply to the handover: take or refuse, proposal by proposal

**Date:** 2026-11-13. **From:** Andre. **To:** Paul.
**In reply to:** [Handover to Andre](2026-11-09-handover-to-andre.md)
(`andre-integration` at `4efa421e`).

## What is measured / what is conjecture

**Measured:** every claim about our `main` cites a file and line read on 2026-11-13. The
three `mellum-verify` bugs were confirmed by reading the code and Pi 1.4.0's runner.
**Conjecture:** nothing we take has run on our stack yet. Every "take" below is a
proposal we'll screen, not a result.

## Two rules we apply to every proposal

1. **Our metrics stand.** Our graders stay as they are, and cost stays counted in
   requests and turns. A proposal that changes how a build is scored or how cost is
   counted can run beside our numbers, never replace them. Every number we've
   published stays comparable with every new one.
2. **Everything we take is screened at n=3 when it lands.** It runs on our harness
   with our grader, against our current baseline, and we report pass, requests, turns
   and wall for each rep. Nothing goes into a preset on the strength of a screen alone.

We bring files over one proposal at a time. We don't merge the branch.

## The short version

| # | Proposal | Verdict |
| --- | --- | --- |
| 1 | Single-source suites | **Refuse** |
| 2 | Hidden grading on a disposable copy | **Take, as a cross-check** |
| 3 | Graders qualified against witness builds, with versions | **Take** |
| 4 | Medium grader corrections | **Refuse as a default** |
| 5 | Easy at thirteen checks, in four phases | **Refuse as a default** |
| 6 | Budget fields in `run.json` | **Take, additive** |
| 7 | Budgets enforced at a proxy | **Refuse** |
| 8 | Host cards and clean runs | **Take, as a record** |
| 9 | Counted runs on a rented pod | **Refuse** |
| 10 | The cost rule for phase work | **Refuse** |
| 11 | The floor: no default `delegate` tool or nudge | **Take, after n=3** |
| 12 | Presets are results (empty them) | **Refuse** |
| 13 | Prompt fragments once per task | **Take, after n=3** |
| 14 | Remove the dead extensions | **Take, with changes** |
| 15 | Bound every bash call with Pi's own timeout | **Take, opt-in** |
| 16 | Re-run a held-out test at settle | **Later** |
| 17 | Gate-runner fixes for `mellum-verify` | **Take** |
| 18 | Keep the held-out test hidden | **Take, with changes** |
| 19 | `guard/supplied-tests` | **Take, opt-in** |
| 20 | One phase at a time, from verified checkpoints | **Later** |

Take: 11 (counting the two after n=3). Refuse: 7. Later: 2.

## Measurement and run trust (1-10)

- **1 Single-source suites. Refuse.** It rewrites the suite prompts and the roadmap
  (`easy/prompts/01.md` included), so runs after it would face a different task, and
  our numbers would stop comparing. The duplicated text is a real smell, and we'll fix
  any prompt that cues an import as a dated, separate change.
- **2 Hidden grading on a disposable copy. Take, as a cross-check.** The hole is real.
  Our `score_workspace_details` (`learn/code/harness.py:1043`) grades inside the
  workspace with its own `pyproject` and environment (`:1051-1058`), so a build can pass
  on its own pytest config. We'll port `grading.py` alone (your `harness.py` lacks our
  mediated arm, `5441b864`) and run it next to our scorer. Where they disagree, we
  report both.
- **3 Grader versions and witness builds. Take.** Pinned grader versions are what keep
  our numbers comparable, so this supports rule 1. Your matrix also found a gap in our
  `ladder/fixtures/acceptance/test_medium.py`, covered under 16-18 below.
- **4 Medium grader corrections. Refuse as a default.** Under rule 1, our 18-check
  Medium grader stays the reported number. We'd like the corrected grader as a named,
  versioned second grader (through 3), and we'll re-grade saved Medium builds under
  both.
- **5 Easy at thirteen checks. Refuse as a default.** Same reason. Your matrix says our
  four-check grader rejects 1 of 6 defect builds, and we accept that it's lenient. Our
  published Easy results (including 5/6 on 2026-11-12) are four-check numbers, and they
  stay that way. A thirteen-check grade can be reported beside them, labelled.
- **6 Budget fields. Take, additive.** Correct: our `turns` equals `requests`
  (`harness.py:996-997`), and `wall` comes from the trace span (`:1004`).
  `requests` stays as it is, as our cost metric. We'll add an accurate turn count and a
  clock wall as new fields, with a dated correction saying our past "turns" were
  requests. Your scoreboard rewrite stays out.
- **7 Budget proxy. Refuse.** We measure cost and don't enforce it. Our runs carry only
  a loose hang guard and censor reps that don't converge. Our own cap work found the
  right cap depends on the tier (a cap that bounds Easy starves Medium), so a fixed
  budget would be measuring the cap.
- **8 Host cards. Take, as a record.** We'll pin our llama.cpp :8001 serve flags and
  write the host card into each run as provenance. It won't be a hard gate.
- **9 Rented pod. Refuse.** Q4_K_M on our M3 Max matched a rented A6000 on Q4, so local
  runs are free and comparable.
- **10 Cost rule. Refuse.** It anchors on output tokens and a multiple of Vanilla.
  Ours is requests and turns per pass (rule 1).

## Architecture, stalls, acceptance, phase work (11-20)

- **11 No default `delegate`. Take, after n=3.** It's our own rule (the worker bundles
  nothing), and `mellum-worker.ts:1882-1884` breaks it. `--mode plan` doesn't use the
  tool (`ladder/run_ladder.py:752-757`). It changes default behaviour, so it lands only
  after an n=3 screen shows no loss.
- **12 Empty presets. Refuse.** Presets are measured settings here. We'll re-derive
  them with a ladder run rather than empty them by decision.
- **13 Prompt fragments once per task. Take, after n=3.** Today each prompt unit appends
  its line to every user message (`remedies/prompt/name-the-layout.ts:25-31`). Once per
  task is cleaner and better for the prompt cache, but it changes what the model sees,
  so n=3 first.
- **14 Remove dead extensions. Take, with changes.** We remove the unloaded ones but
  keep feed, control and rethink, which `dashboard/serve.py` reads, and
  content-tool-call-assist, which is credited in `learn/credits.md`.
- **15 Bounded bash. Take, opt-in.** It comes in as a remedy unit, outside any preset,
  and gets a paired n=3 screen against our `guard/no-live-server` on Medium. That's the
  paired run your rejoinder asks for.
- **16 Held-out test at settle. Later.** We already run our own (`mellum-acceptance.ts`
  plus `mellum-verify.ts`). Yours depends on 1, 2 and 8. We'll look again once 2 and 8
  are in.
- **17 Gate-runner fixes. Take.** All three bugs are real in our
  `extensions/mellum-verify.ts`:
  - No timeout on `execSync` (`:78-83`), so a hung test holds settle.
  - The gate returns only its own entries (`:120`), and Pi keeps the last handler's
    result, so an earlier gate's message is dropped.
  - `passed = code === 0` (`:40`), so a conftest that skips or deselects reads green.
  The branch patch fixes the first two. We'll port the exit-0 check from
  `remedies/gate-run.ts` ourselves. These are bug fixes, test-first, then an n=3
  screen.
- **18 Keep the test hidden. Take, with changes.** Our gate message quotes 1,200
  characters of pytest output (`mellum-verify.ts:46`), which includes the test's path.
  We'll strip the path now. The rest waits for 16.
- **19 `guard/supplied-tests`. Take, opt-in.** The ladder copies the acceptance test
  into the workspace and re-runs that editable copy (`run_ladder.py:532-534`,
  `:821-826`). The guard comes in as an unmeasured opt-in unit with an n=3 screen.
- **20 One phase at a time. Later.** It depends on 2, 5 and 16, and we refuse 5 as a
  default. Our flow harness already checkpoints each passing phase.

## On the rejoinder

- **Agreed:** harness guarantees beat prose rules, the worker is a floor plus explicit
  units, and the hidden grader can be wrong too.
- **Point 3 (Easy is won by guidance).** We accept that our four-check grade can't
  separate guidance from guards. Our claim stays scoped to that grade, and rule 1 keeps
  that grade in place. A thirteen-check number reported beside it would answer the
  question without rewriting our history.
- **Point 4 (`test_medium.py`).** You're right, and the gap is wider than the three
  id-sequence builds. Your matrix has it passing about 20 defect builds (`no_nav`,
  `disabled_input`, `html4_doctype` and others) and rejecting four valid caption and
  date builds. It checks only that two directly built complaints get distinct ids
  (`test_medium.py:70-78`), never route-assigned ids against direct ones. We'll extend
  it against your witness builds before the next gated Medium run.

## Order of work

1. 17 and 18: bug fixes, test-first, then an n=3 screen.
2. 6: the additive fields, plus a dated correction on past "turns".
3. 3 and 2: grader versions and the cross-check grade; re-grade saved Easy and Medium
   builds under both.
4. 15 and 19: opt-in units, each with its paired n=3 screen.
5. 11 and 13: n=3 each, landing only if they show no loss.
6. 14 and 8: cleanup and provenance.

## Updates

Findings and changes as the order of work lands. New verdicts, rejections and
adjustments are added here, newest last.

### 17 and 18 landed, and their n=3 screen (2026-11-13)

- **Landed (`62665777`).** `bounded.ts` is yours, copied as is. The gate now stops
  a hung test at 150 s, keeps earlier settle handlers' entries, reads green only
  when every acceptance function shows a PASSED line, strips `PYTEST_ADDOPTS`, and
  never names where the held-out test lives. Six new tests, each shown red first.
- **The screen (Medium n=3, same rig as our last gated run):**

  | rep | score | requests | wall | stop |
  |---|---|---|---|---|
  | 1 | 17/18 | 168 | 2,272 s | clean |
  | 2 | 18/18 | 22 | 260 s | clean |
  | 3 | 17/18 | 247 | 2,405 s | deadline |

  The previous gate scored 18/18 on 3 of 3 at 76, 56 and 100 requests.
- **The fixes didn't cause the drop.** We re-ran the acceptance test through the
  gate and through plain pytest on all three final builds, and the verdicts
  matched each time. The fixes act only at settle, so they can't change a first
  pass. This time reps 1 and 3 settled short, and the redispatch path, which our
  last run never reached, cost 2 to 3 times the requests without reliably
  closing. That loop is the next thing to work on.
- Details: [the one-pass note](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md).

### `test_medium.py` extended against your witness builds (2026-11-13)

- **Before:** 16 of your 43 Medium witnesses were classified as expected (17 by
  your labels; see `newest_first` below).
- **After:** 43 of 43. The test now reads each page as a document tree, so:
  - a hidden label, a brand inside a comment, a control outside its form, and a
    disabled or non-submitting button no longer count as shown;
  - ids must form one increasing sequence across direct and route creation;
  - the model keeps its field order and a UTC timestamp;
  - resolving or reopening changes only that complaint and moves nothing, in the
    list or on the board.
- **The four valid builds pass now:** the three caption variants and
  `textual_date`. A date is accepted in any common written form that shows the
  year, month and day.
- **Still green** on `agentclinic-done` alongside the phase 1-4 hidden oracle (15
  of 15).
- **One rejection beyond your labels: `newest_first`.** You label it valid, but our
  18-check hidden grader rejects it, and the acceptance test has to be a superset
  of the grader the run is scored on. So the board must show complaints in list
  order.
- **Stricter than our grader, by design.** The test now catches spec misses the
  grader doesn't check:
  - `id` placed before `timestamp`;
  - a missing favicon;
  - every complaint rendered twice.

  One of our earlier 18/18 builds has two of these, so the gate would now send it
  back. That's spec-correct, but it adds gate turns.
- **Reproducible:**
  [`2026-11-13-test-medium-qualified/qualify.py`](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-13-test-medium-qualified/qualify.py)
  reads your witness tables from the `andre-integration` git ref (no merge) and
  writes [`matrix.md`](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-13-test-medium-qualified/matrix.md).

### The gated screen with the extended test (2026-11-13)

- **Same rig as the 17+18 screen**, with only `VERIFY_TEST` pointing at the new
  `test_medium.py`. Medium, n=3:

  | rep | score | requests | wall | stop | acceptance test at exit |
  |---|---|---|---|---|---|
  | 1 | 16/18 | 153 | 1,592 s | clean | 4 of 9 red |
  | 2 | 18/18 | 39 | 626 s | clean | 9 of 9 green |
  | 3 | 17/18 | 234 | 2,201 s | clean | 6 of 9 red |

  Mean 17.0/18 at 142 requests. The 17+18 screen gave 17.3/18 at 146 requests,
  and the earlier gate gave 18/18 on 3 of 3 at 77 requests.
- **The gate's verdicts agree with the grader.** It is green only on the 18/18
  build and red on both short builds. Every grader miss is in phase 4
  (`test_complaint_identity_is_stable_and_keyword_only` on reps 1 and 3, plus
  `test_resolve_route_marks_complaint_resolved_and_redirects` on rep 1). The
  acceptance test flags those misses, plus spec misses the grader doesn't check:
  6 red on rep 3 against 1 grader failure.
- **The gate fired but didn't close.** In reps 1 and 3 the worker's reasoning
  quotes the failing test names the gate handed back. Both builds settled red
  with no guard or deadline stop, so the gate ran out of its five redispatches.
  Our rig's round counter read 0 because it matched a string the console log
  never prints. We can't recover the exact number of rounds, so it isn't
  reported.
- **What this settles.** A stricter test doesn't buy a better score on its own.
  The gate is detecting correctly, and the cost sits in a redispatch loop that
  spends 100 to 200 requests and still doesn't converge. That loop is the lever.
  Why it doesn't converge (context compaction mid-loop, too many concepts per
  round, the worker searching for the held-out file) is a theory until we run
  it.

### Why the loop didn't close, and the fix's screen (2026-11-13)

- **The cause.** The gate handed back the last 1,200 characters of pytest output.
  With nine tests and `-rA`, that tail was only PASSED and FAILED lines, so the
  worker got test names and never a reason. In the rep 1 log, each round it
  reran its own tests, saw them green and settled. Five rounds left the same four
  tests red.
- **The fix (`fcefc2bb`).** The gate now hands back each failing test's
  assertion lines, capped per test. On that rep 1 build the message is 1,710
  characters, with a reason for every failing test. It also stops naming the
  held-out module in object reprs. Four new tests, each shown red first.
- **The screen (Medium n=3, same rig).** Each gate round is counted from the
  gate's own pytest runs this time:

  | rep | score | requests | wall | stop | gate rounds | acceptance test at exit |
  |---|---|---|---|---|---|---|
  | 1 | 18/18 | 150 | 1,591 s | clean | 1, then green | 9 of 9 green |
  | 2 | 14/18 | 172 | 1,473 s | stall | 4 | 5 of 9 red |
  | 3 | 13/18 | 79 | 1,264 s | stall | 0 | collection error |

- **What it shows.**
  - Rep 1 is the first redispatch on record that closed: one round with reasons,
    then green and 18/18.
  - Reps 2 and 3 stalled with no output for 240 s. Both were mid-way through
    debugging a POST that "returns 200, not 303": the routes return 303, but the
    worker's own TestClient follows the redirect.
  - Rep 3 never reached the gate, so this fix can't have touched it. Rep 2 had
    the gate's reasons for four rounds and still stalled in the same debug.
  - The gate's verdict agreed with the grader on all three builds.
- **Where that leaves the loop.** Reasons let a round close, which names alone
  never did. That is a lead at n=3, not a rate. Today's lower mean comes from two
  first-pass stalls on the redirect confusion, and that spiral, not the gate, is
  the next lever. Whether a redirect-aware hint or guard closes it is a theory
  until it's screened.

### The redirect spiral, and a nudge for it (2026-11-13)

- **The trigger, confirmed.** Rep 3 above wrote its own test as `TestClient(app)`
  and asserted 303. That client follows the redirect, so pytest printed
  `assert 200 == 303`. The worker then rewrote a route that already returned 303,
  spending 23 of its 78 turns on it. Rep 2 spent 17.
- **The unit (`42e6ef1b`): `nudge/redirect-followed`.** When a command's output
  shows 200 against an expected 3xx, it appends a note: the client followed the
  redirect, the 3xx is in `response.history`, so check it with
  `follow_redirects=False` and fix the test, not the route. It is opt-in, adds at
  most three notes a session, and carries no suite values. Three new tests, two
  shown red first.
- **The screen (Medium n=3, the failure-reasons rig plus this one unit):**

  | rep | score | requests | wall | stop | gate rounds | acceptance test at exit |
  |---|---|---|---|---|---|---|
  | 1 | 18/18 | 143 | 1,645 s | clean | 2, then green | 9 of 9 green |
  | 2 | 18/18 | 200 | 1,833 s | clean | 5, ran out | 2 of 9 red |
  | 3 | 18/18 | 46 | 510 s | clean | 0, green at once | 9 of 9 green |

  18/18 on 3 of 3 at a mean of 130 requests, with no stalls. Across the last
  three screens, at n=3 each:

  | gate | scores | requests |
  |---|---|---|
  | names only | 16, 18, 17 | 153, 39, 234 |
  | with reasons | 18, 14, 13 | 150, 172, 79 |
  | with reasons and the nudge | 18, 18, 18 | 143, 200, 46 |

- **Attribution is a lead.** We don't log each note the nudge adds. Reps 1 and 3
  ended with `follow_redirects=False` in their own tests, and rep 1's reasoning
  records the switch ("now it shows status 303"). Rep 2 never hit the redirect.
  No rep stalled, against 2 of 3 last time. At n=3 that is a lead, not a rate.
- **Rep 2's five rounds were a real miss with a thin reason.** The favicon
  `<link>` left its `href` quote open, which swallows the Bootstrap stylesheet
  link that follows. A browser parses it the same way, so the acceptance test's
  red is correct. Our grader doesn't check the stylesheet, so the build still
  scores 18/18. The reason the gate handed back was only "Bootstrap 5 CSS" and
  `any(<generator>)`, so the worker couldn't see what the parse found and added
  HTML comments instead.
- **Next lever (a theory).** Make our own acceptance test's messages say what it
  found, for example the stylesheet links it parsed, so a round can close on a
  structural miss too. That needs its own screen.

## What would falsify this / risks

- If the cross-check grade (2) disagrees often with our scorer, our past numbers carry
  a known bias. We'd publish the size of it with a dated correction, not swap graders.
- An n=3 screen is a lead. A unit that looks neutral at n=3 can still cost on a harder
  tier, so a preset change waits for a ladder run.
- Porting by hand into our `harness.py` risks dropping behaviour from either side. Each
  port carries its own tests from your branch.
