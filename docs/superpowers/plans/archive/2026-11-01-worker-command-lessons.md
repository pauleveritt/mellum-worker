---
phase: LC
feature_cycle: LC.30
cycle: 1
lifecycle: closed
---

# Worker-command lessons — plan

## Why

The thin worker (LC.29) is now **mode + the `/mellum` commands** and nothing
else — all remediation moved to units. But the commands are taught nowhere: the
easy track is E1–E7, a remedy build-up, and S0 is a meta "how a lesson works"
page. With the worker thin, driving it *is* the first skill a learner needs, so
the early track should teach the commands before the remedies.

Measured backing (2026-11-01, local Q4, n=3): bare 1/3 → thin worker 2/3 → thin
worker + `preset:easy` **3/3** on easy. The ladder is real: learn to drive the
worker, then add the remedies.

## What the easy track should comprise

Two parts, in order:

1. **The S-series — the worker commands** (new; this plan). One command or
   coherent pair per lesson, each with a runnable example.
2. **The E-series — the remedies** (exists, unchanged). The remediation
   build-up on top of the thin worker; after E7 you have the easy preset.

Proposed S-series:

| # | Lesson | Command(s) | Teaches |
| --- | --- | --- | --- |
| S1 | Turn the worker on | `/mellum on`, `/mellum off` | switch the small model in as a bounded worker; what mode changes |
| S2 | Run one task | `/mellum <task>` | one-shot delegation; the handoff block the parent sees |
| S3 | Check the setup | `/mellum check` | confirm the llama-server matches the measured profile |
| S4 | See the last run | `/mellum last` | read what the worker did, out of its own context |
| S5 | Learn from runs | `/mellum learn` | distil repeated failures into `AGENTS.md` facts |

## Open decisions (confirm before writing pages)

1. **S0.** Keep the current S0 · Start Here (the before/after loop, no model) as
   the track entry and number the commands S1–S5 (recommended — the loop teaches
   how every lesson is read, which still holds), **or** fold the loop into
   Getting Started and number the commands from S0.
2. **Format & home.** Command lessons are *walkthroughs* (do X, see Y), not the
   remedy before/after the 6-step template is built for. Either (a) keep them in
   `learn/lessons/` with a lighter command-lesson shape, or (b) put them in
   `learn/getting-started/` as how-tos and have the easy index point at them.
   Recommended: (a) — they are lessons the learner takes in order, and `/lesson`
   already sequences the track.

## Steps (once the decisions are settled)

1. Write the S-series pages in the chosen home and shape; each shows the command
   and a runnable example a learner can reproduce in Pi.
2. Update `learn/lessons/index.md` and `learn/lessons/easy/index.md` so the easy
   track reads: S-series (commands) → E1–E7 (remedies).
3. Wire the `/lesson` picker: the S-series IDs in `mellum-lessons` parsing and
   `scripts/lesson-lines.mjs` so `/lesson S1` opens the right page and `r` runs
   its example.
4. Add a glossary `###` entry for any command concept a page introduces.
5. `CHANGELOG.md` `[Unreleased]` — this changes what users read.

## Gates

- `node --test tests/docs-caps.test.mjs`, `npm test`, clean `uv run zensical build`.
- Every command example is runnable against a local llama-server (the shipped
  Getting Started setup), not oMLX/vLLM.

## Result

Closed 2026-11-01 (commit `b41de18`). The **Start tier** ships: S1–S5 under
`learn/lessons/start/`, teaching `/mellum on`·`off`·`<task>`·`check`·`last`·`learn`.
Each is a full six-step page reusing an existing illustration (no new art),
discoverable with `/lesson S1`..`S5`, in the Lessons nav under "Start Here", and
linked from the Lessons and Easy index pages. Added a **Handoff block** glossary
entry and a `CHANGELOG.md` line. Gates: node suite 677 pass / 0 fail / 1 skip,
`zensical build` clean.

### The two open decisions, settled

1. **S0 stays the loop.** `S0 · Start Here` keeps teaching the before/after loop
   (no model); the commands are numbered S1–S5 on top of it.
2. **Home — corrected from the plan.** The plan recommended `learn/lessons/` with
   a *lighter* shape. The enforced lesson contract overrode that: the `/lesson`
   tutor (`tests/lesson-tutor.test.mjs`) requires every indexed lesson to carry
   the full six-step frame, an illustration and a command, and `lessonIndex` only
   discovers `easy|medium|hard` plus `start-here.md`. So the command lessons live
   in a new **`learn/lessons/start/` tier** with the full frame, not a lighter
   shape at the `lessons/` root. `lessonIndex` now scans `start/` and ranks the
   Start tier (S0–S5) ahead of Easy/Medium/Hard; the tutor track-order test admits
   the tier, and the contract test exempts the command lessons (no before/after
   arm). Reusing existing illustrations avoided the per-nav-page art requirement.

### Backing

The ladder result the tier rests on stands: bare 1/3 → thin worker 2/3 → worker +
`preset:easy` 3/3 on easy (local Q4, n=3), recorded in
`evals/baseline/2026-11-01-local-q4-thin/`.
