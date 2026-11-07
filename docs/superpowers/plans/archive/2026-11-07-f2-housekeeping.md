---
phase: F
feature_cycle: F.2
cycle: 1
lifecycle: closed
---

# F.2 — housekeeping: the survey, the backlog, questions for Andre

## For Andre

- **Pi survey, corrected:** [the note](../../research/2026-11-07-pi-extension-surface-survey.md)
  maps Pi's extension surface against our units on the floor (21 units), and ranks what
  would turn prompt text into guarantees. Correction from its first draft: the harness runs
  **thinking on**. F.1's payloads carry `enable_thinking: true`; only `scripts/screen.sh`
  passes `--thinking off`.
- **Backlog pruned, 45 → 22 entries.** Removed: work that landed (LC.8, LC.7A), work that
  is now a remedy unit's engine, work R.1 or A.1 takes over, and entries whose reopen condition
  named an archived M, LC or INT cycle. Kept entries were rewritten off LC terms. The removal
  of the dashboard and content-tool-call assist is recorded in their kept entries, with the
  restore command.
- **Questions for you.** F.1 kept these because they are live tools outside the floor. For each
  group: still in use, and should it stay here, move to its own repo, or go?
  1. The flow harness: `learn/code/flow_run.py`, `loop_run.py`, `extensions/mellum-loop.ts`.
  2. Improve and scoring: `learn/code/improve.py`, `improve_distill.mjs`, `scoreboard.py`,
     `evidence.py`, `memory.py`, `lora/`.
  3. Scripts: `delegate.sh`, `mellum-smoke.py`, `scripts/baseline/`, `lesson-check.sh`,
     `lesson-lines.mjs`, `remedies-list.mjs`, `illustrate.py`, `terminal-pictures.py`,
     `mellum.mjs`.
  4. Root narrative docs: `LEARNING.md` (and `.pdf`), `LESSONS.md`, `THEORIES.md`, `EXAMPLE.md`.

## Steps

1. Roadmap row F.2 and this plan.
2. Prune the backlog by the triage Paul approved (the 23 removals named in the commit).
3. Bring the survey over from the old branch, re-checked against `integration`, ≤ 150 lines.
4. Close: `## Result`, archive this plan, squash-merge into `integration`.

## Ladder run

None: no product behaviour changes. The thinking correction rests on F.1's recorded payloads
([record](../../../../evals/2026-11-07-f1-payload/table.md)), not on a new run.

## Persuasion → enforcement

Changes nothing in a session. The survey is the map for R.1: it classifies each unit as
persuasion (text only), enforcement (a Pi hook that blocks, rewrites or guarantees) or mixed,
and ranks the guarantees to build first.

## Result

Closed 2026-11-07. The survey is on `integration` at 103 lines, re-checked against its 21
units and corrected (thinking on). The backlog went from 45 to 22 entries, 431 to 243 lines;
the commit names every removal. The questions above are open until Andre answers. No run;
`npm test` 639/0 (3 skipped), docs caps pass, the site builds.
