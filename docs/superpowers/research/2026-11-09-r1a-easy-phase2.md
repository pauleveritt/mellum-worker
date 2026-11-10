# R.1a: one watched local Easy Phase 2, accepted

## For Andre

**Date:** 2026-11-09. **Cycle:** R.1a, cut from `integration` at `64999fd2` (F.8 squashed).
**What is measured:** one counted session on the Mac, recorded in [the evals record](../../../evals/2026-11-09-r1a-easy-phase2/table.md).
**What is conjecture:** any rate, any cost comparison, and whether Phase 3 or 4 goes the same way.

**Result.** Mellum, running as Base exactly as counted (bounded commands plus the settle re-run), built
Easy's Phase 2 (the complaints board) from the accepted Phase-1 checkpoint, and the phase boundary
accepted it. This is the first phase accepted from model work under trusted, phase-scoped acceptance.
One success establishes presence only.

| Measure | R.1a |
| --- | --- |
| Accepted / strict | yes / yes: hidden phases 1–2 21/21, project tests with the supplied test unchanged, lint |
| Mediated tests, phases 1–2 | 22/22 functions |
| Gate | red four times, then green; never `exhausted` or `infrastructure` |
| Ending | settled on its own; no stall, no budget ending, nothing left running |
| Cost | 97 requests, 47,860 charged output tokens (42,372 in the trace), 607 s of Pi time |
| Ceiling | 128 requests / 64,000 charged output: 76% and 75% used |
| Checkpoint | Phase 2 accepted, commit `cc908686`; Phase 3 can start from it |

**What to look at:** the gate log in the record. The first check failed on the model's timestamp and on
one card per complaint; the next three on the card alone; the fifth went green. Feedback carried each
failing assertion, as F.8 intended.

### What the session did

It read the roadmap, wrote `models.py`, `app.py`'s board route and `templates/complaints.html` (ten
edits to the template), and added its own `tests/test_complaints.py` rather than
editing the supplied test. It never started a server. It left two short note files
(130 and 161 bytes), `PHASE2_COMPLETED` and `PHASE2_FINISHED`, in the project root: the layout report
flags them, nothing grades them, and they ride into the Phase-2 checkpoint. Of 13 tool results marked as
errors, six were its own pytest runs failing, four were edits that did not match, three other commands.

### Setup facts worth keeping

- **The shell's `pi` is not the pinned one.** Volta's Pi 1.1.0 comes first on PATH; the pinned 1.4.0 is
  `~/.local/bin/pi`, which `scripts/r1_batch.py` already uses. The first conformance check failed
  `tooling` for that reason; with `--pi-binary ~/.local/bin/pi` all seven checks passed.
- **The Phase-2 heading check passed.** The model wrote the heading exactly, so the backlog's false
  failure did not arise here; it stays open for a build that adds text to the heading.

### Not comparable

The Easy count's medians (Base 51.5 requests, 33,993.5 output tokens) are Phase 1 on the A40 pod. This
is Phase 2 on the Mac, one session. Neither the phase nor the host matches, so no ratio is drawn.

## Ladder run

Easy rung, `--grader f7-roadmap --phase 2 --from-checkpoint` the `base-r02` checkpoint, one arm (Base as
counted), n = 1, counted (host card passed). The reading, fixed before the run: accepted within the Easy
ceiling or not. It was accepted. Raw trace kept under `~/mellum-runs/r1a/`; a research release is owed
when the branch is pushed.

## Persuasion → enforcement

Nothing persuaded the model to finish: `agent_before_settle` re-ran the frozen mediated tests and sent
the failures back four times; `tool_call` bounded every command. The verdict came from the harness's
trusted grading of the stopped snapshot, and the checkpoint from that verdict alone.

## What would falsify this / Risks

- A second attempt failing would not contradict this: presence at n = 1 says it can happen, not how often.
- Re-grading the saved workspace under the same grader and getting a rejection would. The workspace and
  checkpoint are retained for that.
- Phase 3 meets the other known false failure (`_post_forms` compares form actions exactly), so fix it
  under a new grader identity before Phase 3 is graded.
