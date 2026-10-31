---
phase: LC
feature_cycle: LC.13A
cycle: 1
lifecycle: closed
---

# LC.13A: the Lessons re-base on llama.cpp

## Goal

Make the Lessons track consistent with the settlement Getting Started now
teaches — llama.cpp, prompt v5, the easy/medium/hard suites — and with the
lesson template. Every page's evidence comes from the new instrument; the
oMLX citations leave the pages, and `evals/` keeps the oMLX records
exactly as they are.

## Inputs

- [The nudge preregistration](../../research/2026-10-24-nudge-llamacpp-preregistration.md)
  and [the arm's record](../../research/2026-10-24-nudge-llamacpp-screen.md).
- [`docs/sdd.md`](../../../sdd.md): screens first, preregistered runs to
  decide, caps applied at every update.
- [`learn/lesson-template.md`](../../../../learn/lesson-template.md) and
  [`learn/lessons/baseline.md`](../../../../learn/lessons/baseline.md), the
  only page already on the taught backend.
- `evals/baseline/2026-10-20-reference-llamacpp-rungs1-5` and
  `docs/superpowers/research/2026-10-21-basic-remedies-runs.md`, the only
  llama.cpp evidence the track already has.
- `main` at `7c94a6a`, on branch `lc13a-lessons-rebase` **corrected
  2026-10-24**: this plan was written for `main` at `73fadc8` with the work on
  a `lessons-rebase` branch cut from `lc13-guards`, but the LC.13 commits are
  on `main`, no `lc13-guards` branch exists, and the branch is
  `lc13a-lessons-rebase`.

## Deliverables

- An arm inventory: for each of Paul's ten lessons, the arm, whether the
  suites harness can express it today, and its cost.
- Preregistered arms in staircase order, recorded in
  `docs/superpowers/research/`, not in `evals/`.
- `learn/lessons/*.md` rewritten: no oMLX citation, `backends: [llamacpp]`,
  the template's subsections and columns, `screen` badges where the arm is a
  screen and `cited` only where a preregistered arm supports it.
- A `ROADMAP.md` row and `## Now` pointer, kept current as the work lands.

## Constraints

- Do not delete or edit `evals/`; the oMLX records are evidence for
  their own backend and keep their place.
- No comparative claim without a preregistration that fixed the arms, n,
  reading and rule first.
- One change between arms. The guard arm's void result is the cautionary
  case: two arms that never differ in behaviour cannot be compared. The
  context-budget arm repeated the lesson on 2026-10-24: two windows that no
  request approaches are one policy.
- n = 3, from [`learn/lesson-template.md`](../../../learn/lesson-template.md):
  "Use n = 3 for the baseline and for a claim you will state." **Corrected
  2026-10-24**: this plan previously said n = 10 and forbade a rate below it,
  which contradicted the template and the two n=3 llama.cpp records. The
  nudge screen's n=5 remains the reason to be wary of small n, not a new
  standard; a page that states a rate at n=3 says so in its Reading.
- Keep the claim narrow in each page, and never quote a rate from n < 10.
- The worker, the guard, the prompt and the Baseline Worker change only in
  an arm that measures the change, with a re-baseline.

## Findings carried into this phase

- **n = 5 on easy is noise.** The same policy scored 2/5 and 3/5 in two
  samples of one task, with zero fires in both. Any rate a lesson states
  needs n = 10 or more.
- **The nudge's condition does not match this backend.** `isEmptyAssistantTurn`
  continues only `stop`; the empty finals recorded here were `error`
  (context overflow) and `length` (output cap). The guard is not wrong, it is
  shaped for a different ending.
- **The context window is not the block it looked like.** The guard arm's
  overflow did not recur: seven sessions across 50,176 and 56,064 peaks of
  857–4,699 tokens, zero compaction attempts, `A-50k` 3/3. The window stays
  at 50,000 and the refusal stays, but neither may be called the overflow's
  cause. Easy's demand is variable, so every pass count travels with its
  peak ([record](../../research/2026-10-24-context-budget-screen.md)).
- **A hung request is invisible in the recorded wall.** `report()` derives
  wall from trace timestamps, and a request that never returns writes no
  rows: one session recorded 164 s for a 600 s deadline kill. Backlog, not
  a mid-arm patch.

## Tasks

### Task 1: The guard arm (done, void)

**Record:** [the screen](../../research/2026-10-24-nudge-llamacpp-screen.md).

Preregistered, run, closed: worker 2/5, no-nudge 3/5, zero nudge fires in
ten sessions, medium not run by the staircase's rule. Nothing to re-run;
the context budget has to be settled first.

### Task 2: The arm inventory

**Output:** a research note beside this plan.

For each of Paul's ten lessons: the arm, the harness support, and a verdict —
re-citable from the 45-session llama.cpp record, expressible today, needs a
new `arm_settings` entry, or needs rungs 6–9 that have never run on
llama.cpp. Include the lesson that has no arm at all. This is reading, not
running.

### Task 3: The context budget (done, void)

**Preregistration:** [the context budget](2026-10-24-context-budget-preregistration.md).
**Record:** [the screen](2026-10-24-context-budget-screen.md).

Preregistered, run, closed: `A-50k` 3/3 and `B-56k` 2/3, with peak demand of
857–4,699 tokens against windows of 50,176 and 56,064. Neither window was
approached, so the arm is void for its question and no setting changed. Two
findings carry forward: easy's peak demand varies by more than an order of
magnitude across recorded samples, so no page may describe it as fitting or
needing a window; and a hung provider request does not appear in the
recorded wall. Task 4 is no longer blocked on this, because 50,000 passed.

### Task 4: Arms in staircase order

Easy first, n = 3; medium only on a majority; hard only on a majority of
medium, and skipped when medium shows no headroom. Each arm gets its own
preregistration and record, and its page is rewritten as it lands.

**Arm 1, project facts (done, null).** [Preregistration](2026-10-24-project-facts-preregistration.md),
[record](2026-10-24-project-facts-screen.md). `worker` 1/2 valid against
`no-facts` 0/3, with the block injected in 26/26, 22/22 and 11/11 requests and
in none of `no-facts`; one `worker` session invalid on contamination. Null on
passes at n=3, no medium run. The lead is unregistered and belongs to LC.7A:
all three `no-facts` sessions hung on a foreground server command
(`uvicorn app:app --reload` twice, `python app.py` once) after 143–460 s of
silence, and the removed bullet is `- Do not: start servers`.

**Arm 2, lessons 1 and 2 (done, both null).** [Preregistration](2026-10-24-lessons-1-2-preregistration.md),
[record](2026-10-24-lessons-1-2-screen.md). Easy at n=3: `bare` 1/3,
`worker` 2/3, `no-prompt` 1/3. `bare` passing a session means the
primary-agent contrast does not re-base — the page retires the 8/15 instead.
The prompt stays a null, one session apart, as the 45-session record found.
Medium took `worker`'s majority and then proved unmeasurable: all six sessions
in both arms ran the full 600 s deadline while still working. The arm also
found and fixed a nudge-counting bug: a prompt boundary is not a nudge.

**Booked, not run:** the foreground-server arm. The pathology is Andre's (P2,
from his PR #1 and prompt v10, deferred to LC.7A) and the bullet is Paul's, so
a three-way arm (facts bullet, the dormant guard at `420ba1d`, or both) waits
for LC.5 and lands on LC.7A's page.

**Pages (done).** All four rewritten: `primary-agent`, `short-prompt`,
`thinking-working-memory`, `guards-for-empty-turns`, plus the index's
one-liners. No page links `evals/`, two are honest nulls, one is a void
arm, and lesson 3 says plainly that it has no instrument here.

### Task 5: Close

**Output:** Status cell, `## Now`, this plan's `## Result`, archived.

Confirm every page's claim against its record, run
`node --test tests/docs-caps.test.mjs` and `npm test`, and reconcile
`[Unreleased]`.

## Acceptance

No page under `learn/lessons/` cites an oMLX record; every page states the
backend and settings its evidence came from and links its record; every
number on a page appears in that record; and the four checks pass.

## Result

**Closed 2026-10-24.** Infrastructure cycle, not a lesson: it re-based the
Lessons track on llama.cpp and built the arms the later lesson cycles need.

- **Four arms closed.** Guard: void, zero nudge fires in ten easy sessions.
  Context: void, peak demand 857–4,699 against windows of 50,176 and 56,064,
  no setting changed. Facts: null on passes, block injected in every `worker`
  request, plus the foreground-server lead booked to LC.7A. Lessons 1 and 2:
  both null at n=3; `bare` passed a session, so lesson 1's contrast retires
  rather than re-bases.
- **Pages re-based.** `primary-agent`, `short-prompt`,
  `thinking-working-memory` and `guards-for-empty-turns` no longer cite an
  oMLX record; the index's one-liners match them. Two pages are nulls, one a
  void arm, one an explicit missing instrument.
- **Instrument.** `no-facts` became an arm; the four arm knobs are cleared
  from the inherited environment; a nudge is counted only inside one prompt;
  a `before_compact` row exists when a compaction is allowed; the recorder
  loads after the worker again, because Pi lets each handler replace the
  payload.
- **Measured, not used.** Medium is unmeasurable at the 600 s deadline today
  for every arm tried, on a machine 1.7–3× slower than the 45-session
  record's. No medium claim is made anywhere.
- **Owed.** The `research-2026-10-24` raw-evidence release (run JSON, traces,
  stdout, patches from `/tmp/mellum-eval-runs`).
- **Checks.** `node --test tests/docs-caps.test.mjs` 4/4, `npm test` 349/349,
  `learn/code/tests` 42/42, `zensical build` clean.
