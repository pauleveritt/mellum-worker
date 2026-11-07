# Spec-driven development in this repository

A **phase** is the container: F (Floor), R (Remedies) and A (Architect) since
the 2026-11-07 re-boot; M and the Learning Center (LC) before it. A **feature
cycle** is one row inside a phase, named `F.1` or `R.2`.

A feature cycle delivers **one result**: a product change, or a remedy unit
measured on quality *and* budget (wall time, turns, context size). A cycle may
instead be housekeeping or infrastructure — the harness, a baseline, a clean-up
— and says so in its Ships cell. A cycle with no named deliverable of either
kind is not a cycle.

Three files hold the state, and only three: [`ROADMAP.md`](../ROADMAP.md) (the
active phases and `## Now`), [`BACKLOG.md`](../BACKLOG.md) (deferred work with
reopen conditions) and [`ARCHIVE.md`](../ARCHIVE.md) (closed phases, verbatim).
There is no per-phase roadmap file.

Every feature cycle runs the Superpowers cycle:
**brainstorm → spec → plan → execute → review/close.** A cycle that reaches a
plan without a brainstorm has skipped a step, not saved one; brainstorming
scales its ceremony to the request and always ends with your partner's
approval before implementation.

- Specs: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
- Plans: `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`
- Research and verdicts: `docs/superpowers/research/YYYY-MM-DD-<topic>.md`

The M.1 design and plan were written in the weights repo, which may go private; `docs/recipe.md` summarizes them.
Everything after that lands here.

## Why this file exists

A written convention that nothing checks gets ignored under deadline
pressure. So: caps, and a checker. `tests/docs-caps.test.mjs` fails the suite
when a document is over cap; the caps are the ones below.

This regime follows `ds4-engine`: whole-file caps as well as cell caps,
short pointers instead of repeated narrative, and evidence kept separately
from feature-cycle state. Its predecessor reached 998 roadmap lines, roughly 800 of
them backlog. Individually reasonable entries can still overwhelm a document;
prose rules and an executable gate are both needed.

## Document caps

| Document | Cap | Over cap means |
| --- | --- | --- |
| `ROADMAP.md` whole file | 400 lines | Something owes a move to `research/` or deletion |
| Roadmap **Ships** cell | 400 chars | The detail belongs in the spec or plan |
| Roadmap **Excludes** cell | 250 chars | The detail belongs in the spec or plan |
| Roadmap **Status** cell | 300 chars; a closed or superseded row carries a link | A verdict doc is owed |
| **Backlog entry** | 1,200 chars | A research doc is owed; the entry keeps a link and a reopen condition |
| **Plan** | 400 lines, 25% fenced | Split the feature cycle |
| **Spec** | 400 lines | Split the design |
| Spec, dated 2026-11-07 or later | 100 lines | Split the design |
| Plan or research note, dated 2026-11-07 or later | 150 lines | Split the cycle, or move evidence to a sibling directory |

Over cap does not mean "trim the wording". It means a verdict or research doc
is owed: move the narrative to `docs/superpowers/research/`, link it, and let
the entry shrink to a summary plus a reopen condition.

**Caps apply at every update, not only at close.** A growing cell signals
that a verdict doc is owed now. The current limits are calibrated against
this repository's content; any recalibration must be justified by actual
documents and recorded here, not used to bypass a failing check.

## Branches and worktrees

- Each feature cycle runs on its own branch, in its own worktree, cut from
  `integration`. Inside it, commits stay small and atomic (test shown failing
  first).
- At close, the cycle is **squash-merged into `integration`** as one commit whose
  message names the row, what shipped and what was measured. Then its worktree is
  removed and its branch deleted, so a cycle is reverted as a unit.
- `integration` collects closed cycles and reaches `main` by pull request. Nothing
  is pushed without asking.

## Short documents, three fixed sections

From 2026-11-07, every spec, plan and research note is short enough for a
co-maintainer to read in one sitting, and carries three sections the checker
looks for:

- **`## For Andre`**, at the top: what changed, why, the result, what to look at.
- **`## Ladder run`**: rung first, then arms, n and the decision rule — or why
  no run is needed and what proves the change instead.
- **`## Persuasion → enforcement`**: which Pi extension hook the cycle uses and
  what it guarantees, as opposed to what prompt text merely asks for.

`For Andre` is the first level-two section, outside fenced examples. All three
sections contain an assessment, not an empty heading. Before proposing prompt
text, assess the applicable Pi hooks from the extension-surface survey. Name
the hook and its guarantee; when no Pi hook applies, explain why and identify
the mechanism that enforces the behavior instead. Review verifies that choice;
the document checker verifies structure and length. Andre's own notes, merged
from `origin/main`, keep his shape: the checker lists each one as exempt by
name, and our documents cite them as input rather than restating them.

Each implementation plan also carries a non-empty `## Close` section. It links
the [branch/worktree procedure](#branches-and-worktrees) and schedules the squash
into `integration`, verifies the resulting tree, then removes the cycle worktree
and branch. Use the owning tool to clean up a managed worktree, and run cleanup
from a retained checkout. Keep the main checkout's reference branch untouched.

Say it once. Detail that a reader does not need to act goes to a linked
research note or a sibling evidence directory, not into the spec or plan.

## `## Now` is a pointer, not a narrative

It names what is in flight, what is parked and why, and what comes next
(one sentence each), linking to the feature-cycle row or backlog entry
carrying the detail. It never re-narrates a decision that already has a home.
Measurements and history belong in Status cells and research docs.

## Backlog discipline

Every entry states a reopen condition. An entry over cap owes a research doc
and shrinks to a summary, a link, and its reopen condition. Resolved entries
are removed once their outcome is recorded in a feature-cycle row or a
research doc the row links. Retired and superseded entries are removed too; an entry
without a meaningful reopen condition is deleted, not kept just in case.
Cite entries by heading anchor, never by line number.

## Plan front matter

```
---
phase: F
feature_cycle: F.1
cycle: 1
lifecycle: active
---
```

`phase` names the container, `feature_cycle` the row, `cycle` its ordinal, and
`lifecycle` is `active`, `closed`, or `superseded`. Plans archived before
2026-10-24 carry `phase: <row>` and `cycle: 1` with no `feature_cycle`; they are
not edited, and their `phase` reads as the row it named. Closed and superseded
plans end with `## Result` (date, what shipped or superseded the work, what
was measured). Active plans must not claim a result in advance. At close,
fences over 15 lines become `path:line` references to what shipped: a plan
records intent and outcome, not a second copy of the code.

## Archive

Closed and superseded plans move to `docs/superpowers/plans/archive/` once
their `## Result` is written. Archived documents are never edited afterwards,
even to fix a stale path or a claim later proved wrong; a dated correction
belongs in the document that supersedes them.

Archived plans stay out of the checker scope. Historical debt is not a
current regression, and repeatedly flagging it trains people to ignore the
gate. Specs and research are not archived: decisions and evidence stay at
their original paths, with dated corrections beside the original reasoning.

A roadmap row is a pointer, not a report: what ships, what is out, the state,
and links to the spec, plan, record or note that hold the detail. The cell caps
were lowered from 900/900/1,000 on 2026-11-07, after rows on the old branch grew
to near 1,000 characters by restating their plans.

Closed feature cycles keep their roadmap rows (state, date and links) while
their phase is active. An over-cap closed row owes a research doc.

When a whole phase closes, with every row closed or superseded and a short
verdict at its head, its section moves verbatim to `ARCHIVE.md` and is not
edited afterwards. `ROADMAP.md` keeps only active phases.

2026-11-07: this replaces the 2026-10-20 rule that a closed series moves to its
own file (`ROADMAP-M.md`). Per-phase roadmap files are retired; M, LC and INT
are in `ARCHIVE.md`.

## Docs are a presentation layer

Every primary document must render as plain Markdown on GitHub without a
generator. The roadmap, backlog and archive live at the repository root; specs,
plans and research live under `docs/superpowers/`. A future documentation
site presents these sources rather than making its syntax a dependency.

## Kept as it was written

When a decision is reversed, record the reversal beside the original,
dated, rather than silently editing it away. Preserve why the earlier
decision made sense on the evidence then available.

## Research notes

Open with an honesty header stating plainly **What is measured** and **What
is conjecture**, and end with **What would falsify this** and **Risks**.
Evidence that is not text (transcripts, run records) goes in a sibling
`YYYY-MM-DD-<topic>/` directory when suitable for Git. Raw ladder traces,
stdout and patches remain outside Git and are published as research-release
assets after review; a sibling manifest can record their provenance.

## Evals: screens first, preregistered runs to decide

- **Screens find a lead.** While a question is open, run the fewest targeted
  runs that can move it (often two or three), then write a short research
  note saying what ran, what it showed and n. No preregistration, spec or
  plan is needed for an exploratory screen.
- **Screens are sized by what they read, not by habit.** A *presence* — the
  block arrived, the guard fired, a file left the layout — is settled at
  n = 1. An *absence* or a *comparison* needs n >= 3: one quiet session is not
  an absence, and one session per arm is not a comparison. A page that states
  n = 1 may not say "null", "void" or "separated"; a test enforces the wording.
- **Preregistered runs decide.** Before a run that decides a default,
  product change or comparative claim, fix the arms, n, reading and decision
  rule in a preregistration. Screens do not establish comparative rates.
- **Specs describe product behavior.** Write a spec when product behavior
  changes; write a plan only when the work is large enough to need one.
- **Measure what ships.** Use the ladder with the product's settings and
  host path. A setting the product does not share is a harness finding,
  not a claim about the shipped worker. Keep the harness thin.
- **Before blaming the model,** reconstruct its task, files, tool replies
  and environment, and check that the scoring can distinguish the arms.

This does not reopen measured decisions: promotion still requires an
applicable ladder run recorded in `evals/`.

## Closing a feature cycle

Before closing a feature cycle or finishing its branch:

1. Update its Status cell and the `## Now` pointer in `ROADMAP.md`, and
   remove backlog entries it resolved once their outcome has a record.
2. **Glossary:** add or update one `###` entry for any concept the cycle
   introduced. The rule already applies to every page; at close it is the last
   chance, and a page that links a term nobody defined is how a glossary rots.
3. **Pathologies:** if the cycle's evidence showed a failure shape
   [`learn/pathologies.md`](../learn/pathologies.md) does not carry, add it with
   the record that shows it. If it showed none, add nothing — an entry needs an
   observation behind it, so "update the page every cycle" would fill it with
   hypotheses.
4. Confirm every claim is supported by the linked evidence; keep screens,
   revised scores and comparative measurements distinguishable.
5. Write the plan's `## Result`, set its lifecycle to `closed` or
   `superseded`, and move it to `docs/superpowers/plans/archive/`.
6. Run `node --test tests/docs-caps.test.mjs` and `npm test`, and reconcile
   `[Unreleased]` with commits since the latest release tag.
7. Squash-merge the cycle into `integration` and verify tree equality before
   removing its worktree and branch, following [Branches and worktrees](#branches-and-worktrees).

A feature cycle does not require a release tag to close. When releasing, the
tag, package version, README install lines and changelog must agree.

## Standing rules

- Measured settings are not changed without a ladder run in `ladder/`,
  recorded in `evals/`; raw evidence goes in a `research-YYYY-MM-DD`
  release, never in git.
- Every new test is shown to fail before the code that makes it pass.
- A release is a tag; the package version, the tag, and the README install
  lines agree, and `CHANGELOG.md` has a section for it.
