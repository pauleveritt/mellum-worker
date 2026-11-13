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

## What would falsify this / risks

- If the cross-check grade (2) disagrees often with our scorer, our past numbers carry
  a known bias. We'd publish the size of it with a dated correction, not swap graders.
- An n=3 screen is a lead. A unit that looks neutral at n=3 can still cost on a harder
  tier, so a preset change waits for a ladder run.
- Porting by hand into our `harness.py` risks dropping behaviour from either side. Each
  port carries its own tests from your branch.
