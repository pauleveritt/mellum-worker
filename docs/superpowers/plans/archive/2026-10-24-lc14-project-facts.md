---
phase: LC
feature_cycle: LC.14
cycle: 1
lifecycle: closed
---

# LC.14: Project facts

## Goal

Write the fifth findings lesson, **Project facts**, as a six-step page. The
arm is already measured: the block reaches the model in every `worker`
request and did not move the easy suite at n=3. No new measurements.

## Classification

Bounded, and recorded as such: one page, one test, one index line, no
preregistration because no new run happens. The partner delegated overnight
completion of this cycle on 2026-10-24, so the design gate is this section:
the page states a **null** and a **lead**, keeps every number to the facts
record, and claims nothing the record does not.

## Inputs

- [The facts record](../research/2026-10-24-project-facts-screen.md) and its
  [preregistration](../research/2026-10-24-project-facts-preregistration.md).
- [`learn/lesson-template.md`](../../../../learn/lesson-template.md),
  [`learn/lessons/primary-agent.md`](../../../../learn/lessons/primary-agent.md)
  for the re-based shape.
- `extensions/mellum-facts.ts` for the block and the `MELLUM_MODE_FACTS` knob.
- `main` at `043db73`; worktree `.worktrees/lc14-project-facts`, branch
  `lc14-project-facts`.

## Deliverables

- `learn/lessons/project-facts.md`, six steps, badges on 1–5, an
  Interpretation naming its weakest badge.
- `tests/lesson-project-facts.test.mjs`, in the shape of the other four.
- An index link for item 5 and a `zensical.toml` nav entry.
- A `CHANGELOG.md` entry under `[Unreleased]`.
- At close: the LC.14 Status cell, the `## Now` pointer, this plan's
  `## Result`, and the plan moved to `plans/archive/`.

## Constraints

- No `evals/` link and no oMLX citation; the page is llama.cpp only.
- Every number on the page appears in the facts record: `1/2` valid,
  `0/3`, injection `26/26`, `22/22`, `11/11` against `0/17`, `0/48`,
  `0/51`, and the one invalid session.
- The foreground-server lead is labelled a lead, not a finding, and its owner
  is named: the pathology is Andre's, deferred to LC.7A.
- Do not change the worker, prompt, guards or facts block.

## Tasks

1. Write the page from the record.
2. Write the test; watch it fail on the missing page.
3. Link the page from the index and the nav; add the changelog entry.
4. Close: checks, Status cell, `## Now`, `## Result`, archive.

## Acceptance

`node --test tests/docs-caps.test.mjs`, `npm test` and
`learn/code/tests` pass; the page names llama.cpp and its settings, links the
facts record, cites no oMLX record, and every number in it is in that record.

## Result

**Closed 2026-10-24.** Lesson 5, **Project facts**, is a re-based six-step page
on llama.cpp.

- The arm was already measured and needed no new run: the block reached the
  model in 26/26, 22/22 and 11/11 `worker` requests and in none of the
  `no-facts` sessions, and did not move the easy suite — 1/2 valid against
  0/3, with one worker session invalid on contamination.
- The page states the **null** with the injection count beside it, retires the
  oMLX "1/12 to 9/12" claim, and carries the foreground-server observation as
  a **lead** attributed to Andre's P2 and deferred to LC.7A.
- Shipped: the page, a two-test lesson file, the index link, the nav entry and
  a changelog entry.
- Checks: `docs-caps` 4/4, `npm test` 351/351, `zensical build` clean.
