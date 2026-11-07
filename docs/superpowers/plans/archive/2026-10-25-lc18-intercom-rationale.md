---
phase: LC
feature_cycle: LC.18
cycle: 1
lifecycle: closed
---

# LC.18 — lesson 9, the intercom block as a rationale

## Why

Lesson 9 was "The intercom block is a prefill tax": pi-subagents' intercom
instructions rode in the child's prompt on every request, and A11 measured the
child prompt shrinking with the bridge off. But LC.8 retired the delegated child,
its templates, the intercom phases and the ladder's `delegated` mode. There is no
mechanism left to arm, and the roadmap re-scoped the cycle on 2026-10-24: the page
states **why the transcript was not kept**, not what it cost.

## Decisions taken before this plan

- **A rationale, not a measurement.** All five steps carry `conjecture`. The page
  does not restate A11's character counts or its prefill percentage; a number
  whose mechanism no longer ships reads as a claim about today's worker.
- **The evidence is the removal and the replacement.** What LC.8 deleted, and
  what `collapseHandoffs` does instead: one block per closed span, built after
  the fact, from the span's own messages.
- **No arm, and the page says so** where the Eval case would be, with the reason.
  Validation rests on checks that exist today: the handoff tests.
- **The transferable rule is the lesson**, not the retired mechanism:
  summarise a delegate's work once, never re-send its transcript on every turn.

## Non-goals

- Re-adding a delegate mechanism, or a screen or arm for one.
- Quoting A11's numbers, or citing `evals/` — lesson pages may not link it.
- Changing the worker, the prompt, the guards or the handoff block.

## Tasks

### Task 1: The plan and the failing test

**Files:** `tests/lesson-intercom-block.test.mjs`

- [ ] **Step 1: Write the lesson test first** — six `##` headings, steps 1–5
  badged `conjecture`, `weakest badge is `conjecture``, `position: 9`, no
  `evals/` link, no `reference-run`, and the page names `collapseHandoffs`,
  the summary block, and says there is no arm.

- [ ] **Step 2: Run it and see it fail for the missing page.**

### Task 2: The page

**Files:** `learn/lessons/intercom-block.md`

- [ ] **Step 1: Opening, two sentences**, ≤45 words, no badge or link: the
  problem (a transcript paid on every turn) then the answer (one summary block
  per span).
- [ ] **Step 2: Problem** — the intercom instructions in every request, and the
  tempting alternative when a parent cannot see what a child did: keep the
  child's transcript in the parent's context.
- [ ] **Step 3: Eval case** — no arm, and why: LC.8 deleted the mechanism on
  2026-10-20. What the page rests on instead.
- [ ] **Step 4: Evidence of the problem** — the removal itself, with the commit,
  and the code path that exists now.
- [ ] **Step 5: Solution** — `collapseHandoffs` and the summary line, quoted
  small from `extensions/mellum-worker.ts`.
- [ ] **Step 6: Validation** — checks only: the handoff tests, the command and
  what it said. No table.
- [ ] **Step 7: Interpretation** — weakest badge `conjecture`, the rule that
  transfers, and what would upgrade it (a mechanism re-added and measured).

### Task 3: Index, nav, changelog

**Files:** `learn/lessons/index.md`, `zensical.toml`, `CHANGELOG.md`

- [ ] **Step 1: Link entry 9** and drop the "not written yet" line for lesson 9,
  leaving the index with no unwritten scheduled lesson.
- [ ] **Step 2: Nav entry** before `lessons/one-spec-per-phase.md`, matching
  position order.
- [ ] **Step 3: Changelog** — one `Added` entry.
- [ ] **Step 4: `node --test tests/learn-site.test.mjs` and commit.**

### Task 4: Close

- [ ] **Step 1: LC.18's Status cell** and `## Now` (Active becomes LC.7A's page).
- [ ] **Step 2: `## Result`**, `lifecycle: closed`, `git mv` to archive.
- [ ] **Step 3: Verify** — `node --test tests/docs-caps.test.mjs`, `npm test`,
  then commit `docs(lc18): close the cycle`.

## Risks

- **A rationale that reads as a measurement.** Every step says `conjecture` and
  the page must not borrow the retired percentages to sound stronger.
- **A stale reason.** If a delegate mechanism returns, the page is the first
  thing that owes an arm; the Interpretation says so.
- **The handoff block's own cost.** It is one block per span, and a span with
  fifteen commands still produces a bounded message; the page says the bound is
  the point, not that the block is free.

## Result

2026-10-25. Shipped: lesson 9, **The intercom block is a prefill tax**, as the
roadmap re-scoped it — a rationale whose five steps carry `conjecture`, whose Eval
case says there is no arm and why (LC.8 deleted the mechanism on 2026-10-20), and
whose Solution is `collapseHandoffs`' one-summary-block-per-span, quoted small from
`extensions/mellum-worker.ts`. Its own test, the index entry, the nav line and a
changelog entry land with it.

Nothing was measured: the page restates no percentage from the retired arm, links
no `evals/` record, and claims no `reference-run`. What it validates is the
mechanism's contract — 93 handoff tests — and `npm test` 380/380, docs caps 4/4.

Open, and stated in the Interpretation: the pairing (transcript against summary,
on the suites) needs a delegate mechanism re-added and measured. That is a new
cycle, not a gap in this one.
