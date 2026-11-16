# Spec-driven development in this repository

A **phase** is the container: the Learning Center, and historically the M
series. A **feature cycle** is one row inside a phase, named `LC.13A` or
`M.7C`.

A feature cycle delivers **one lesson**. A cycle may instead be housekeeping
or infrastructure — the harness, a baseline, a re-base, a consent record — and
says so in its Ships cell. A cycle with no named deliverable of either kind is
not a cycle.

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
| Roadmap **Ships** or **Excludes** cell | 900 chars | A verdict doc is owed |
| Roadmap **Status** cell | 1,000 chars | A verdict doc is owed |
| **Backlog entry** | 1,200 chars | A research doc is owed; the entry keeps a link and a reopen condition |
| **Plan** | 400 lines, 25% fenced | Split the feature cycle |
| **Spec** | 400 lines | Split the design |

Over cap does not mean "trim the wording". It means a verdict or research doc
is owed: move the narrative to `docs/superpowers/research/`, link it, and let
the entry shrink to a summary plus a reopen condition.

**Caps apply at every update, not only at close.** A growing cell signals
that a verdict doc is owed now. The current limits are calibrated against
this repository's content; any recalibration must be justified by actual
documents and recorded here, not used to bypass a failing check.

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
phase: LC
feature_cycle: LC.13A
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

Closed feature cycles keep their roadmap rows: state, date and links. There is
no row archive. An over-cap closed row owes a research doc.

2026-10-20: a whole closed series may move to its own file once it has a
close and a verdict. The M series is in `ROADMAP-M.md`, linked from
`ROADMAP.md`, and is not edited afterwards. Individual closed rows still stay.

## Docs are a presentation layer

Every primary document must render as plain Markdown on GitHub without a
generator. The roadmap and backlog live at the repository root; specs,
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

A feature cycle does not require a release tag to close. When releasing, the
tag, package version, README install lines and changelog must agree.

## Standing rules

- Measured settings are not changed without a ladder run in `ladder/`,
  recorded in `evals/`; raw evidence goes in a `research-YYYY-MM-DD`
  release, never in git.
- Every new test is shown to fail before the code that makes it pass.
- A release is a tag; the package version, the tag, and the README install
  lines agree, and `CHANGELOG.md` has a section for it.
