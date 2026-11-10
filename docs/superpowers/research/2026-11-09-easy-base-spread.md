# Easy Phases 2 and 3: Base's own per-phase spread, a screen

## For Andre

**Date:** 2026-11-09, 20:57–23:03 EST. Cut from `integration` at `302ac419` (F.7, F.8, R.1a), rebased
onto `be0afbd1` (R.1b) before the write-up.
**What is measured:** 30 local sessions, all in [the evals record](../../../evals/2026-11-09-easy-base-spread/table.md):
12 Base on Easy Phase 2, 12 Base on Phase 3, 6 plain Vanilla on Phase 2. A spread and a lead, not a rate.
**What is conjecture:** any rate; any ratio to the pod's Phase-1 count; Phase 3 from any Phase-2 build
other than R.1a's; Phase 4; why a given session runs long.

**Why.** Paul is retiring the bar "3× Vanilla's median charged output over all sessions" for an absolute
ceiling on all-attempt cost per accepted phase, plus a reliability floor. Setting that ceiling needs
Base's own spread per phase. Before this there were three Phase-2 Base draws, R.1a's and the two in
[R.1b's note](2026-11-09-r1b-think-briefly.md), and Phase 3 had never been run from model work.

**Result.** Base was accepted on 9 of 12 Phase-2 attempts and 12 of 12 Phase-3 attempts. Plain Vanilla
was accepted on none of 6. Each Base attempt cost 7,689–64,472 charged output; the medians were 14,770
(Phase 2) and 17,772.5 (Phase 3). Cost per accepted phase, every attempt included, was:

| Arm | Accepted | Charged output per accepted phase | Trace output per accepted phase | Median charged, all attempts | Max charged |
| --- | --- | --- | --- | --- | --- |
| Phase 2, Base | 9/12 | 25,761 | 24,372 | 14,770 | 48,985 |
| Phase 3, Base | 12/12 | 27,071 | 21,667 | 17,772.5 | 64,472 (ceiling) |
| Phase 2, Vanilla | 0/6 | none accepted | none accepted | 8,935.5 | 10,476 |

*Charged output* is the budget proxy's count, the one the ceiling is charged in. *Trace output* is the
recorder's count of the worker's own replies. The record gives both per session.

### What the runs show

- **Acceptance holds up.** In all 21 accepted runs, the boundary verdict in `run.json` matches the
  checkpoint's own record. Every one passed every mediated test (22/22 on Phase 2, 27/27 on Phase 3) and
  the hidden phases up to its own. All 24 Base builds passed the hidden checks, including the three
  rejected ones.
- **Phase 2's three rejections are not behaviour.** Two failed the lint gate on an unused import (ruff
  F401, auto-fixable). One changed the supplied `tests/test_home.py`. All three had a green settle gate:
  the settle re-run checks the mediated tests, not lint or the supplied tests.
- **Every Phase-2 Base run was sent back at least once,** 19 send-backs in all. The first red verdict
  in all 12 named `test_complaint_constructs_positionally_with_its_own_aware_timestamp`. Plain Vanilla, which has
  no gate, missed the matching hidden check (`test_complaint_model_contract_is_preserved`) in 6 of 6.
  On this phase, the gate's feedback is the difference between the arms. Vanilla is cheaper per
  attempt (median 8,935.5) and buys nothing.
- **Phase 3 mostly passes first time.** 10 of 12 were green on their first settle, one needed a single
  send-back, and one (r12) hit the token ceiling before its first settle. r12 was still accepted, because F.8 grades
  the stopped snapshot whatever the ending. It was charged 64,472, which is over the 64,000 ceiling by
  its last request. A ceiling set below that would have rejected an accepted build.
- **The Phase-3 tail is long.** Five of 12 runs cost 41,065–64,472 charged and took 405–676 s of Pi time.
  All five compacted; none of the other seven did, and they cost 7,689–20,356.
- **The two counts differ in 7 of 30 runs, and the gap reconciles exactly.** Charged output equals the
  proxy's per-request sum in every session. Charged minus trace is compaction output (requests the trace
  omits) plus a flat charge: a request whose usage the proxy could not read is charged 16,384, which is
  about 7,500–8,600 more than that reply's real output. Four such requests appeared, all in Base runs. As a
  share of all charged output, compaction was 2.2% on Phase 2 and 12.4% on Phase 3; the flat-charge
  excess was 3.2% and 7.6%. [R.1b](2026-11-09-r1b-think-briefly.md) read its gap as
  compaction; here part of it is the flat charge.
- **R.1a was a high draw.** Its 47,860 would rank second among these ten accepted Phase-2 Base builds
  (R.1a's plus this batch's nine); this batch's median accepted cost is 15,120. R.1b's Base draws are in its
  [note](2026-11-09-r1b-think-briefly.md).
- **The Phase-3 grading check applied.** Every Phase-3 build wrote `action="/complaints"` literally, so
  `f7-roadmap`'s exact form-action check ran and passed. The `url_for` false failure did not arise. This
  does not clear the grader: a build that renders a `url_for` action still fails it.
- **Strays.** Two Phase-2 Base runs edited the supplied `AGENTS.md` (r01, rejected for lint; r07,
  accepted). No run created a note file. Every Phase-3 run started from R.1a's checkpoint, which
  already holds its `PHASE2_COMPLETED` and `PHASE2_FINISHED`. These are listed, not scored.
- **Time.** The 30 sessions took 2 h 06 min wall time. Median session: 161 s on Phase 2, 220 s on Phase 3.

This changes no preset, default or ROADMAP status, and it sets no ceiling: the numbers are Paul's input.

## Reading, fixed before the runs

- **Arms** (all Easy, `--grader f7-roadmap`, current Easy budget 128 requests / 64,000 charged output /
  1,200 s, `--grade --stall 180`, counted against a fresh host card, `--pi-binary ~/.local/bin/pi`):
  - `p2-base`: R.1a's arm exactly, `--arm vanilla --remedy
    tool/bounded-commands,check/mediated-test-settle --phase 2`, from the `base-r02` Phase-1
    checkpoint (`ffced376`). **n = 12.**
  - `p3-base`: the same arm, `--phase 3`, from R.1a's accepted Phase-2 checkpoint (`cc908686`).
    **n = 12.**
  - `p2-vanilla`: `--arm vanilla --phase 2` with no remedy, from `ffced376`. **n = 6**, a floor.
- **Order:** `scripts/r1_batch.py`, round-robin. Rounds 1–6 run all three arms; rounds 7–12 the two
  Base arms. 30 sessions; expected 5–6 h, at most about 10 h if many reach the wall.
- **Recorded per session:** accepted / strict and the boundary's reasons; hidden and mediated counts;
  gate verdicts and send-backs; ending (`completion`); requests; **charged output** (the budget proxy's
  count, `budget.spent.output_tokens`, the number the ceiling is charged in); **trace output** (the
  recorder's `output_tokens`); Pi seconds and wall time; strays (`out_of_layout`).
- **Per arm:** accepted k/n; min, median and max of both token counts over all attempts and over
  accepted ones; **all-attempt cost per accepted phase** (sum of every attempt's charged output over
  the accepted count), in both counts; endings; strays.
- **No bar and no rule.** This is a screen: it reports a spread, not a rate, and changes no preset,
  default or ROADMAP status.

### Known confounds, stated before the runs

- **Phase-3 hidden grading has a known false failure:** `_post_forms` compares a form action exactly,
  so a `url_for` action rendering `http://testserver/...` fails `f7-roadmap` while the mediated tests
  accept it (BACKLOG "Two hidden checks can still fail a valid build"). Paul's call: grade as is, keep
  every workspace, regrade under a corrected, versioned grader. A Phase-3 rejection whose only hidden
  miss is that check is reported as *rejected, regrade owed*, never as a model failure.
- **Phase 3 starts with strays.** R.1a's Phase-2 checkpoint carries its `PHASE2_COMPLETED` and
  `PHASE2_FINISHED` note files. Whether strays count against acceptance is Paul's open decision; they
  are listed, not scored.
- **Host:** the Mac, not the A40 pod; Phase 1's count is on the pod. No cross-host ratio is drawn.

## Ladder run

The batch ran as fixed above: 30 sessions, none skipped or re-run, finished in about 2 h rather than the
5–6 h expected. The record is [`evals/2026-11-09-easy-base-spread/`](../../../evals/2026-11-09-easy-base-spread/table.md).
Each session's `run.json`, gate log, mediated result, layout report and, when accepted, checkpoint record
are there, with the raw trace stripped. Traces, workspaces and checkpoints are kept under
`~/mellum-runs/base-spread/`, so every Phase-3 build can be regraded under a corrected grader. A research
release is owed when the branch is pushed.

## Persuasion → enforcement

Nothing here relies on the model's word. Acceptance comes from the harness's trusted grading of each
stopped snapshot (hidden checks, the supplied tests unchanged, lint, every mediated test), and a
checkpoint comes only from that verdict. The settle gate is what moves Base past the Phase-2 timestamp
contract that Vanilla misses. What it does not enforce, lint and the supplied tests, is where Base's
three Phase-2 rejections came from. That is a lead for an agnostic check, not a measured remedy.

## What would falsify this / Risks

- n = 12 per Base arm gives a spread, not a rate or a tail estimate. The one budget ending (Phase 3,
  r12) is a real tail and is counted, not dropped.
- Phase 3 started from a single Phase-2 build, R.1a's, with its own tests and strays. Phase 3 from
  another accepted Phase-2 build could cost differently.
- The Phase-2 rejections depend on lint and integrity rules, not behaviour. A different lint policy
  would change the 9/12 without changing any build.
- The flat 16,384 charge on a request with no usage report added 3.2% (Phase 2) and 7.6% (Phase 3) to
  charged output here. A ceiling in charged output carries that charge as long as the proxy applies it.
- The Mac, not the pod. Phase 1's count is on the A40, so no cross-host ratio is drawn.
- Drift through the night hit the arms alike through the round-robin, except Vanilla in rounds 7–12.
