---
phase: LC
feature_cycle: LC.19
cycle: 1
lifecycle: closed
---

# LC.19 — lesson 10, one spec file per phase

## Why

The lesson's old instrument was ladder rungs 6–9, retired in LC.24. LC.19A built
the replacement — per-module check readings and a `--specs joined|split` arm on
medium — and four attempts have now run against it
([preregistration](docs/superpowers/research/2026-10-25-lesson10-preregistration.md),
[record](docs/superpowers/research/2026-10-25-lesson10-run.md)):

- Attempts 1 and 2 hung on a foreground server.
- Attempt 3 completed every phase and scored 18/18 because nothing asked for
  `models.py`; the grader could not import the workspace.
- Attempt 4 ran the full arm: **phase-4 missing `joined` {5, 0} against `split`
  {0, 3}** — a tie at 0, so **no separation at n = 3**.

So the page cannot claim the layout changes what a worker reaches. What it can
claim, with the record behind it, is the finding that paid for the cycle: the
**acceptance criteria in the spec**, not the number of files they sit in, are
what got a 12B worker from "nothing imports" to 1 of 18 checks missing.

## Decisions taken before this plan

- **The page states the null and the mechanism.** Steps 3 and 5 stay `screen`;
  no `reference-run` is claimed. The Interpretation names `screen` as the weakest
  badge and says what would upgrade it.
- **The mechanism is the criteria, not the layout.** The page's Solution is the
  tech-stack layout table and the per-phase acceptance lists, quoted small, with
  the arm table as the evidence that the criteria moved the task and the layout
  did not.
- **The pathology is the unimportable workspace.** Two of six sessions never ran
  their checks: a syntax error in `app.py` and a `Complaint` whose `timestamp`
  has no default. That is the failure a learner most needs to recognise, and the
  page names it with `checks_ran: false` as the reading.
- **The layout question is reported as open, not answered.** n = 3 with two
  usable sessions per arm cannot separate anything, and re-scoping the lesson
  into a rationale (as LC.18 did) would throw away the instrument.

## Non-goals

- Another run, a larger n, or a re-run of the arms.
- Changing the worker, the prompt, the suites' graders or `expected.json`.
- A pass-rate claim: medium is 0/3 for both arms.
- Claiming the layout matters in either direction.

## Tasks

### Task 1: The record

**Files:** `docs/superpowers/research/2026-10-25-lesson10-run.md`

- [x] Attempt 4's table, the rule applied, and the finding — done before this plan.

### Task 2: The page

**Files:**
- Add: `learn/lessons/one-spec-per-phase.md`
- Test: `tests/lesson-one-spec-per-phase.test.mjs`

**Interfaces:**
- Consumes: the record's table and the suite's own files for excerpts.
- Produces: the page the index and nav will link.

- [ ] **Step 1: Write the lesson test first.** It asserts the six `##` headings,
  a two-sentence opening of 45 words or fewer with no badge or link, the badge
  pattern, `weakest badge is`, the record's session ids, and no `evals/`
  link. Run it and see it fail for the missing page.

- [ ] **Step 2: Write the page** in the six steps:

  - **Opening, two sentences.** The problem, then the answer, ≤45 words.
  - **Problem** — `screen`: a small worker handed a phased build drops a later
    phase; the failure this run actually produced was worse and more common —
    a workspace that no longer imports, so nothing is checked at all.
  - **Eval case** — the medium suite, four phases, `--specs joined` against
    `--specs split`, n = 3 per arm, deadline 2700, the phase-4 group in
    `check_groups` as the reading.
  - **Evidence of the problem** — the arm table, six sessions, with
    `checks_ran: false` on the two that never ran.
  - **Solution** — the criteria in the spec: the layout table from
    `tech-stack.md` and one phase's acceptance list, quoted small.
  - **Validation** — the same table read for what moved (missing 18 → 13 → 1) and
    what did not (phase 4, {5, 0} against {0, 3}).
  - **Interpretation** — the null, the weakest badge, the `checks_ran` lesson,
    and what would upgrade: n above 3 with a task above the pass floor.

- [ ] **Step 3: Run the lesson test and the shared site test.** Both must pass,
  including the auto-discovered two-sentence opening check.

### Task 3: Index, nav, changelog

**Files:** `learn/lessons/index.md`, `zensical.toml`, `CHANGELOG.md`

- [ ] **Step 1: Link entry 10** in the track index, replacing the unlinked
  digest line with the measured claim.
- [ ] **Step 2: Add the nav entry** after `lessons/prose-brief.md`.
- [ ] **Step 3: Changelog** — one `Added` entry for the lesson, saying what it
  claims and that it is a null on layout.
- [ ] **Step 4: `node --test tests/learn-site.test.mjs`, then commit.**

### Task 4: Evidence

- [ ] **Step 1: Bundle** attempts 3 and 4's session directories — six from
  attempt 4, the orphan from attempt 3 — as
  `research-2026-10-25-lesson10-runs.tar.gz`, `workspace/` and `profile/`
  excluded, with a manifest naming each attempt and each session id.
- [ ] **Step 2: Upload** to the `research-2026-10-25` release beside the
  attempts 1–2 bundle, and link it from the record.

### Task 5: Close

**Files:** `ROADMAP.md`, this plan

- [ ] **Step 1: LC.19's Status cell** → `complete 2026-10-25 — ` with the plan,
  the record, the page, the null's numbers and the `npm test` total, under 1,000
  characters.
- [ ] **Step 2: `## Now`** — Active becomes LC.18; LC.7A stays next.
- [ ] **Step 3: `## Result`** here: what shipped, what was measured, what is
  still open (the layout question at higher n).
- [ ] **Step 4: Archive.** `lifecycle: closed`, `git mv` to
  `docs/superpowers/plans/archive/`.
- [ ] **Step 5: Verify.** `node --test tests/docs-caps.test.mjs`, `npm test`,
  `git log --oneline`, commit `docs(lc19): close the cycle`.

## Risks

- **A null page that reads as advice.** "One spec file per phase" is not
  supported by the run; the page must say the criteria are what carried it, or a
  learner will reorganise files and learn nothing.
- **Two usable sessions per arm.** The page says 2 per arm, not 3, wherever the
  comparison appears.
- **The reading is per-module.** Quoting `failed_checks` totals without the
  module breakdown would hide that the whole difference sits in phases 2 and 4.

## Result

2026-10-25. Shipped: lesson 10, **One spec file per phase**, written from a
preregistered `joined`-against-`split` arm on the medium suite; its test; the
index entry, nav entry and changelog; and the attempts 3–4 evidence on the
`research-2026-10-25` release.

What was measured: six sessions, no censors, no contamination, one write outside
the layout. Phase-4 missing was `joined` {5, 0} against `split` {0, 3}, and total
missing {13, 1} against {4, 10}; passes 0/3 for both arms. The preregistered rule
saw a tie at 0 and stopped: **a null on spec layout**, so steps 3 and 5 stay
`screen` and no `reference-run` is claimed.

What the cycle did establish: the acceptance criteria in the spec, not the number
of files they sit in, are what moved a 12B worker from a workspace no check could
import to 1 of 18 checks missing. Two of six sessions recorded `checks_ran:
false` — a syntax error in `app.py` and a `Complaint` with no default
`timestamp` — which is the pathology the page names.

Open, and parked in `BACKLOG.md`: the layout question at n above 3 on a task
above the pass floor. `npm test` 368/368, `learn/code/tests` 62/62,
`docs-caps` 4/4.
