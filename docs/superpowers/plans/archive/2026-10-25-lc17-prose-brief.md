---
phase: LC
feature_cycle: LC.17
cycle: 1
lifecycle: closed
---

# LC.17: A prose brief stops at its first reply

## Goal

Write the eighth findings lesson, **A prose brief stops at its first reply**,
and the instrument its claim needs: a way to send a suite's phases as **one
brief** instead of steps, without copying the suite.

## Classification

Bounded, and the design was approved in conversation on 2026-10-25:

- **A flag, not a copied suite.** `--single-prompt` concatenates the suite's
  own prompts into one request. A `medium-oneprompt/` directory would duplicate
  the base and the grader, and two graders can disagree — then the comparison
  is not one change.
- **Medium only.** The easy suite has one prompt, so it cannot express
  "steps versus one brief"; medium's four phase briefs are the steps.
- **The arm is the prompt shape**, so it is a harness flag rather than an
  `arm_settings` entry: no environment variable changes the shape of a brief.

## Instrument

`learn/code/harness.py`:

- `run_suite(..., single_prompt=False)` sends `"\n\n".join(suite.prompts)` once
  instead of one request per prompt.
- `_run_sessions(..., single_prompt=False)` passes it through and records
  `single_prompt` in `run.json`, so a record can never be silent about which
  shape produced it.
- `harness.py run --single-prompt`.
- One test: with the flag, a two-prompt suite is invoked **once** and its log
  contains both briefs; without it, twice.
- `sweep_group`: after the last prompt, every process the run left in its
  group is ended and recorded as `leaked` in `run.json`. Two tests, and an
  end-to-end check that a backgrounded sleeper is found and killed.
- `machine` and `deadline` in `run.json`, because an M1 Pro wall and an M5 Max
  wall are not the same number even when they are the same session.

## Inputs

- [The arm inventory](../research/2026-10-24-lc13a-arm-inventory.md): lesson 8
  is "expressible" — a one-prompt variant of an existing suite.
- [The lessons 1–2 record](../research/2026-10-24-lessons-1-2-screen.md) and its
  **correction**: these runs are on an **M1 Pro, 8 cores, 32 GiB**, while the
  backend records were taken on an **M5 Max, 128 GB**. Peak tokens transfer
  between machines; walls do not.
- `learn/code/suites/medium`, [`learn/lesson-template.md`](../../../../learn/lesson-template.md).
- `main` at `7068c7d`; worktree `.worktrees/lc17-prose-brief`, branch
  `lc17-prose-brief`.

## Deliverables

- The flag and its test (done: 46 harness tests pass).
- [A preregistration](../research/2026-10-25-oneprompt-preregistration.md) that
  fixes arms, n, the medium deadline (measured by a timing probe, not guessed)
  and the reading **before** the arm runs.
- The run: `worker` on medium as steps and as one brief, n=3, same machine, same
  session length.
- `learn/lessons/prose-brief.md`, six steps, badges 1–5, no oMLX citation.
- `tests/lesson-prose-brief.test.mjs`, the index link, the nav entry, a
  changelog entry.
- At close: the LC.17 Status cell, `## Now`, `## Result`, plan archived.

## Constraints

- No worker, prompt, guard or suite-content change.
- Every wall reported is an M1 Pro wall and says so; no comparison with an
  M5 Max wall anywhere.
- A session that hits the deadline is reported as DEADLINE and never pooled as
  a pass or a failure.
- If the one-brief arm matches the steps arm, the page states a null and
  retires the "loses four passes" claim.

## Acceptance

`npm test`, `learn/code/tests` and `docs-caps` pass; the page's numbers are in
the run record; no `evals/` link on the page; `qualify --suite medium`
still passes.

## Session state, 2026-10-25 (written before a session reset)

**Cycle open.** Worktree `.worktrees/lc17-prose-brief`, branch
`lc17-prose-brief`, based on `main` at `7068c7d`.

Done and committed on this branch:

- `045d0c9` `--single-prompt`, plus `machine` and `deadline` in `run.json`.
- `cfa5aad` the process sweep: a run's leftover group is ended and recorded as
  `leaked`.
- `54fab82` threads `--single-prompt` through `suite all`.
- The preregistration (`research/2026-10-25-oneprompt-preregistration.md`) and
  **both sessions have run**:
  - steps `39df1a`: tests pass, lint fails (`F401`), 53 requests, peak 11,369,
    wall 894 s.
  - one brief `ad1bb7`: **passes**, 52 requests, peak 3,761, wall 961 s.

**The result reversed the lesson's direction** and the page must say so: at
n=1 the one-brief arm passed where the steps arm failed, on lint rather than
tests. The page is **not written yet**; that is the next task.

Remaining for this cycle: `learn/lessons/prose-brief.md` (six steps, badges
1–5, all `screen`, n=1 named), its test, the index link for item 8, the nav
entry, the changelog, the Status cell, `## Now`, `## Result`, archive, merge.

**Outside this cycle, still open:** the user's uncommitted `zensical.toml`
(site name → "Small AI Learning Center") and `learn/index.md`, which leave one
test failing because `tests/learn-site.test.mjs` still asserts the old name;
the machine-calibration decision (A+C: calibration tokens/second per run);
and LC.19 (ladder rungs 6–9 on llama.cpp), approved but not started.

## Result

**Closed 2026-10-25.** Lesson 8, **A prose brief stops at its first reply**,
plus three instrument changes.

- **Instrument.** `--single-prompt` (one brief, not steps), `machine` and
  `deadline` in `run.json`, and the process sweep that ends what a run leaves
  behind and records it as `leaked`. 49 harness tests, including an end-to-end
  check that a backgrounded sleeper is found and killed.
- **Screen.** Steps: tests pass, lint fails (`F401`), 53 requests, peak 11,369,
  894 s. One brief: **passes**, 52 requests, peak 3,761, 961 s — both on an
  M1 Pro, 32 GiB, 1,800 s deadline.
- **The direction reversed.** The pathology did not appear; the only failing
  arm was the stepped one, and its failure was an unused import rather than a
  missing phase. The lesson's old claim (four passes lost, 2.4× the time) is
  retired and the page says so.
- **Shipped.** Page, lesson test, index link, nav entry, changelog.
- **Checks.** `learn/code/tests` 49/49, `docs-caps` 4/4, `npm test` 356/357 with
  the one failure belonging to the uncommitted site-name rename in the shared
  worktree, not to this cycle.
