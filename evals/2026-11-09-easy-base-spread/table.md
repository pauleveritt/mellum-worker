# Easy Phases 2 and 3: Base's per-phase spread, with a Vanilla floor on Phase 2

A screen, not a rate: 30 local sessions, 2026-11-09 20:57–23:03 EST. Easy, `--grader f7-roadmap`, `--grade --stall 180`, budget 128 requests / 64,000 charged output / 1,200 s. Apple M5 Max, pinned Q4 (`b12110-cd959bae9`), Pi 1.4.0, host card passed 7/7. Arms in `arms-r01-06.json` and `arms-r07-12.json`, run round-robin by `scripts/r1_batch.py`. Phase 2 starts from the `base-r02` Phase-1 checkpoint (`ffced376`), Phase 3 from R.1a's accepted Phase-2 checkpoint (`cc908686`). See the [note](../../docs/superpowers/research/2026-11-09-easy-base-spread.md).

**Two token counts.** *Charged output* is the budget proxy's count (`budget.spent.output_tokens`), the number the ceiling is charged in; it equals the sum of the proxy's per-request charges in every session. *Trace output* is the recorder's count of the worker's own replies (`output_tokens`). Charged minus trace is exactly compaction output (requests absent from the trace) plus, for each request whose usage the proxy could not read, the flat 16,384 charge less the reply's real output.

## Per arm

| Arm | n | Accepted | Charged output, all attempts: min / median / max | Trace output, all attempts: min / median / max | Charged per accepted phase | Trace per accepted phase | Median requests | Median Pi s | Endings | Send-backs | Runs compacted | Compaction / flat-charge share of charged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p2-base | 12 | 9 | 10,578 / 14,770 / 48,985 | 10,578 / 14,770 / 43,994 | 25,761 | 24,372 | 30.5 | 136.8 | settled 12 | 19 in all; median 1, max 5 | 1 of 12 | 2.2% / 3.2% |
| p3-base | 12 | 12 | 7,689 / 17,772.5 / 64,472 | 7,689 / 17,772.5 / 41,740 | 27,071 | 21,667 | 29.5 | 193.2 | budget 1, settled 11 | 1 in all; median 0, max 1 | 5 of 12 | 12.4% / 7.6% |
| p2-vanilla | 6 | 0 | 8,467 / 8,935.5 / 10,476 | 8,467 / 8,935.5 / 10,476 | — (none accepted) | — (none accepted) | 20 | 81.4 | settled 6 | 0 in all; median 0, max 0 | 0 of 6 | 0.0% / 0.0% |

Charged per accepted phase is every attempt's charged output summed over the accepted count; trace per accepted phase likewise. Accepted runs only, charged: p2-base 10,578 / 48,985 (median 15,120); p3-base as all attempts.

## Per session

| Run | Accepted / strict | Hidden | Mediated | Gate | Ending | Requests (charged / trace) | Charged output | Trace output | Compaction (calls / tokens) | Flat charges | Pi s | Session s | Strays | Reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p2-base-r01 | no / no | pass | 22/22 | 1 send-back, then green | settled | 39 / 39 | 18,209 | 18,209 | 0 / 0 | 0 | 170.1 | 195 | AGENTS.md | lint gate failed |
| p2-base-r02 | yes / yes | pass | 22/22 | 5 send-backs, then green | settled | 103 / 101 | 48,985 | 43,994 | 1 / 4,991 | 0 | 582.7 | 607 | — | — |
| p2-base-r03 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 30 / 30 | 14,420 | 14,420 | 0 / 0 | 0 | 138.2 | 162 | — | — |
| p2-base-r04 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 28 / 28 | 10,578 | 10,578 | 0 / 0 | 0 | 98.9 | 123 | — | — |
| p2-base-r05 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 25 / 25 | 18,017 | 18,017 | 0 / 0 | 0 | 161.7 | 187 | — | — |
| p2-base-r06 | no / no | pass | 22/22 | 1 send-back, then green | settled | 29 / 29 | 11,988 | 11,988 | 0 / 0 | 0 | 121.1 | 146 | — | lint gate failed |
| p2-base-r07 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 31 / 31 | 32,271 | 24,760 | 0 / 0 | 1 | 260.2 | 284 | AGENTS.md | — |
| p2-base-r08 | no / no | pass | 22/22 | 1 send-back, then green | settled | 33 / 33 | 12,961 | 12,961 | 0 / 0 | 0 | 131.0 | 155 | — | project tests failed; supplied tests changed: tests/test_home.py |
| p2-base-r09 | yes / yes | pass | 22/22 | 4 send-backs, then green | settled | 40 / 40 | 23,961 | 23,961 | 0 / 0 | 0 | 244.4 | 268 | — | — |
| p2-base-r10 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 26 / 26 | 11,654 | 11,654 | 0 / 0 | 0 | 112.2 | 137 | — | — |
| p2-base-r11 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 31 / 31 | 15,120 | 15,120 | 0 / 0 | 0 | 135.4 | 160 | — | — |
| p2-base-r12 | yes / yes | pass | 22/22 | 1 send-back, then green | settled | 30 / 30 | 13,683 | 13,683 | 0 / 0 | 0 | 129.5 | 154 | — | — |
| p3-base-r01 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 20 / 20 | 8,228 | 8,228 | 0 / 0 | 0 | 76.1 | 103 | — | — |
| p3-base-r02 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 30 / 30 | 15,189 | 15,189 | 0 / 0 | 0 | 150.8 | 178 | — | — |
| p3-base-r03 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 61 / 58 | 44,803 | 35,672 | 3 / 9,131 | 0 | 559.0 | 586 | — | — |
| p3-base-r04 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 19 / 19 | 11,296 | 11,296 | 0 / 0 | 0 | 98.7 | 125 | — | — |
| p3-base-r05 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 17 / 17 | 7,689 | 7,689 | 0 / 0 | 0 | 75.1 | 102 | — | — |
| p3-base-r06 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 29 / 29 | 20,356 | 20,356 | 0 / 0 | 0 | 226.9 | 253 | — | — |
| p3-base-r07 | yes / yes | pass | 27/27 | 1 send-back, then green | settled | 38 / 36 | 44,483 | 31,936 | 1 / 4,277 | 1 | 404.8 | 431 | — | — |
| p3-base-r08 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 62 / 60 | 41,065 | 26,912 | 2 / 5,591 | 1 | 471.3 | 499 | — | — |
| p3-base-r09 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 29 / 29 | 15,157 | 15,157 | 0 / 0 | 0 | 159.5 | 186 | — | — |
| p3-base-r10 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 20 / 20 | 10,847 | 10,847 | 0 / 0 | 0 | 97.8 | 125 | — | — |
| p3-base-r11 | yes / yes | pass | 27/27 | 0 send-backs, then green | settled | 40 / 37 | 41,269 | 34,980 | 3 / 6,289 | 0 | 480.1 | 507 | — | — |
| p3-base-r12 | yes / yes | pass | 27/27 | no verdict | budget | 52 / 48 | 64,472 | 41,740 | 5 / 14,842 | 1 | 675.8 | 703 | — | — |
| p2-vanilla-r01 | no / no | fail 2 | 20/22 | not armed | settled | 19 / 19 | 9,161 | 9,161 | 0 / 0 | 0 | 77.4 | 102 | — | hidden checks failed; project tests failed; supplied tests changed: tests/test_home.py; mediated tests failed |
| p2-vanilla-r02 | no / no | fail 3 | 19/22 | not armed | settled | 28 / 28 | 10,433 | 10,433 | 0 / 0 | 0 | 101.7 | 126 | — | hidden checks failed; mediated tests failed |
| p2-vanilla-r03 | no / no | fail 1 | 21/22 | not armed | settled | 15 / 15 | 8,710 | 8,710 | 0 / 0 | 0 | 76.6 | 101 | — | hidden checks failed; mediated tests failed |
| p2-vanilla-r04 | no / no | fail 1 | 21/22 | not armed | settled | 17 / 17 | 8,578 | 8,578 | 0 / 0 | 0 | 70.2 | 94 | — | hidden checks failed; mediated tests failed |
| p2-vanilla-r05 | no / no | fail 2 | 20/22 | not armed | settled | 21 / 21 | 10,476 | 10,476 | 0 / 0 | 0 | 87.8 | 112 | — | hidden checks failed; project tests failed; supplied tests changed: tests/test_home.py; mediated tests failed |
| p2-vanilla-r06 | no / no | fail 2 | 20/22 | not armed | settled | 25 / 25 | 8,467 | 8,467 | 0 / 0 | 0 | 85.4 | 109 | — | hidden checks failed; mediated tests failed |

Gate: `not armed` is plain Vanilla (no settle re-run). p3-base-r12 ended on the token ceiling before its first settle, so its gate gave no verdict; F.8 accepts from the trusted grading of the stopped snapshot, whatever the ending. Compaction calls are those in `run.json` (`compactions`); compaction tokens come from matching the proxy's per-request charges against the trace's replies, and in p3-base-r12 the split between compaction and flat charge is ambiguous by one request (the total reconciles). Flat charges: requests the proxy could not read usage for, charged 16,384 each. Session s: from the run directory's start to its `run.json`. Strays: `out_of_layout` (both are edits to the supplied `AGENTS.md`). The Phase-3 checkpoint already carries R.1a's `PHASE2_COMPLETED` and `PHASE2_FINISHED`; they are not flagged again.

Phase-3 form actions: every build wrote `<form ... action="/complaints" method="post">` literally, so `f7-roadmap`'s exact form-action check applied and passed; the `url_for` false failure did not arise.

Raw traces, workspaces and checkpoints are kept locally under `~/mellum-runs/base-spread/`; a research release is owed when the branch is pushed. Each session's directory here holds `run.json`, `gate.jsonl`, `mediated.json`, `layout.json` and, when accepted, `checkpoint.json`.
