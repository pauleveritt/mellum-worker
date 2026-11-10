# R.1a: one watched local Easy Phase 2 from a Phase-1 checkpoint

One counted session, n = 1: a presence, not a rate. Easy, `--grader f7-roadmap --phase 2`, from the
`base-r02` Phase-1 checkpoint (`ffced376`). Base as counted: `--arm vanilla --remedy
tool/bounded-commands,check/mediated-test-settle --grade --stall 180`. Apple M5 Max, pinned Q4
(`b12110-cd959bae9`), Pi 1.4.0, host card passed. See the [note](../../docs/superpowers/research/2026-11-09-r1a-easy-phase2.md).

| Run | Accepted | Strict | Hidden (phases 1–2) | Mediated | Gate | Completion | Requests | Charged output | Trace output | Pi seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| base-r01 | yes | yes | 21/21 | 22/22 | green after 4 send-backs | settled | 97 | 47,860 | 42,372 | 606.9 |

Gate verdicts, in order: red (timestamp, card), red (card), red (card), red (card), green.
Project tests passed with the supplied test unchanged; the session added `tests/test_complaints.py`.
Out of layout: `PHASE2_COMPLETED`, `PHASE2_FINISHED` (short note files the session wrote). Accepted checkpoint commit
`cc908686`. Raw trace kept locally under `~/mellum-runs/r1a/`; a research release is owed when pushed.
