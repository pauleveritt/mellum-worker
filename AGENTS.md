# mellum-worker — agent notes

This repo ships the measured "Mellum as a bounded coding worker" recipe for
Pi and OpenCode. Read [`README.md`](README.md) first. The numbers come from
the ladder (`ladder/`) and are recorded in `docs/ladder/`.

## Spec-driven development

This project runs Superpowers SDD: brainstorm → spec → plan → execute →
review/close. **Read [`docs/sdd.md`](docs/sdd.md) before writing any spec,
plan, or roadmap edit**; it carries the document caps and why each exists.

- Specs: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
- Plans: `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`
- Research: `docs/superpowers/research/YYYY-MM-DD-<topic>.md`

[`ROADMAP.md`](ROADMAP.md) is the phase list and current pointer;
[`BACKLOG.md`](BACKLOG.md) is deferred work with reopen conditions. Brainstorm
within a phase; do not re-open settled, measured decisions without a ladder
run in `ladder/`.

**Evals are screens first, preregistered runs to decide** (`docs/sdd.md`):
use a few targeted runs and a short research note while exploring; fix
arms, n, scoring and the rule before runs that decide a change or claim.
Specs describe product behavior changes; plans are for work large enough
to need one.

## Document caps are not advisory

`ROADMAP.md` caps at 400 lines; a Ships or Excludes cell at 900 characters, a
Status cell at 1,000, a backlog entry at 1,200, a plan at 400 lines and 25%
fenced, a spec at 400 lines. `tests/docs-caps.test.mjs` enforces them. Over
cap means a research doc is owed, not that the wording gets trimmed.

Caps apply at every update. `## Now` is a pointer, never a narrative;
detail belongs in a phase row, backlog entry or linked research doc.
Remove resolved, retired and superseded backlog entries. Preserve decisions
and evidence with dated corrections; never edit archived plans.

## Working rules

- `npm test` runs the suite; every new test is shown to fail first.
- The ladder, from `ladder/`: `uv run python -m pytest` for its tests,
  `uv run python -m ladder.run_ladder --help` for runs. Never commit
  `trace.jsonl`, `stdout.txt` or `diff.patch`; raw evidence goes in a
  `research-YYYY-MM-DD` release.
- `node build.mjs` regenerates the agent templates after a prompt change, and
  a test fails on drift. `prompts/mellum-worker.md` is the only prompt source.
- Never add a `build`, `prepare`, `prepack`, or `install` npm script; OpenCode
  installs from Git through pacote and that breaks the install.
- A release is a tag that matches `package.json` and both README install
  lines, with a `CHANGELOG.md` section.

## Driving the worker: don't trust its self-exit (a lead under test)

The worker decides when it is done, and a run can exit confident on an
incomplete, self-authored test — the Phase 4 id miss. The direction being
measured is to define "done" with an acceptance test that is **external** (the
worker did not write it), **complete** (the whole spec, not the subset the
worker chose) and **unweakenable** (the worker cannot edit or delete it), and
to verify a run by re-running that test and re-dispatching its failure, never
by the worker's final message. This is M.11 (the mediated test) plus the
freeze-the-oracle guard; both are unmeasured until M.11's rung-9 screen, so
treat it as the lead it is, not a settled rule. See the
[exit-gate note](docs/superpowers/research/2026-10-18-harness-exit-gate.md) and
the M.11 row in [`ROADMAP.md`](ROADMAP.md).

## Keep the changelog current

`CHANGELOG.md`'s `## [Unreleased]` section is kept up to date as work lands,
not written at release time. This is a standing rule.

- **With each change:** a commit that changes what a user installs, runs,
  configures, or reads (extensions, prompt, templates, skill, README,
  recipe, the ladder's commands or records) adds its entry under
  `[Unreleased]` in the same commit, in the existing `Added` / `Changed` /
  `Fixed` / `Removed` headings. Internal-only commits (SDD records,
  backlog, roadmap, tests alone) need no entry.
- **At checkpoints:** at the end of each plan task, at phase close, and
  before a tag, compare `[Unreleased]` against
  `git log <last tag>..HEAD --oneline` and add anything missing.
- **At release:** `[Unreleased]` becomes `## [x.y.z] - YYYY-MM-DD` in the
  same commit that bumps `package.json` and the README install lines, and a
  new empty `[Unreleased]` goes above it.
- Entries say what changed for the user and why, in a sentence or two, not
  the commit subject.

## Finishing a phase

Update the phase's Status cell and the `## Now` pointer in `ROADMAP.md`, close
the plan with `## Result`, move it to `plans/archive/`, and remove any backlog
entry the phase resolved. Confirm claims against linked evidence, pass
`node --test tests/docs-caps.test.mjs` and `npm test`, and reconcile the
changelog before finishing the branch. A phase may close before a release
tag. This is a standing rule.
