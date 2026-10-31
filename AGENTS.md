# mellum-worker — agent notes

This repo ships the measured "Mellum as a bounded coding worker" recipe for
Pi and OpenCode. Read [`README.md`](README.md) first. The numbers come from
the ladder (`ladder/`) and are recorded in `evals/`.

## Spec-driven development

This project runs Superpowers SDD: brainstorm → spec → plan → execute →
review/close. **Read [`docs/sdd.md`](docs/sdd.md) before writing any spec,
plan, or roadmap edit**; it carries the document caps and why each exists.

- Specs: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
- Plans: `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`
- Research: `docs/superpowers/research/YYYY-MM-DD-<topic>.md`

[`ROADMAP.md`](ROADMAP.md) is the feature-cycle list and current pointer;
[`BACKLOG.md`](BACKLOG.md) is deferred work with reopen conditions. Brainstorm
within a cycle; do not re-open settled, measured decisions without a ladder
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
detail belongs in a feature-cycle row, backlog entry or linked research doc.
Remove resolved, retired and superseded backlog entries. Preserve decisions
and evidence with dated corrections; never edit archived plans.

## Working rules

- `npm test` runs the suite; every new test is shown to fail first.
- The ladder, from `ladder/`: `uv run python -m pytest` for its tests,
  `uv run python -m ladder.run_ladder --help` for runs. Never commit
  `trace.jsonl`, `stdout.txt` or `diff.patch`; raw evidence goes in a
  `research-YYYY-MM-DD` release.
- **Run standard — use the two scripts, don't hand-assemble flags.**
  `scripts/screen.sh <rung> <model-id>` is the measurement rig (direct, mediated:
  `tuned`, repeat 3, redispatch 5, effort-ramp, thinking off, **guards on**, the
  default prompt, the mediated tool set, `--model omlx/<model-id>`).
  `scripts/product.sh <rung>` is the shipped worker (`--mode mode`, guards and
  facts on). Both write to `runs/` (git-ignored) and want
  `ladder/scripts/watch_ladder.py` alongside; promote a kept run to
  `evals/<date-topic>/` with the raw stripped. Per-run
  `--prompt`/`--tools`/`--thinking` tweaks or source edits are ablations,
  recorded as such — not how a standard run is made.
- `prompts/mellum-worker.md` is the only prompt source.
- **Run Python through `uv run`, never a bare `python`/`python3`** — the pinned
  env and lockfile are what make a run reproducible. (`npm test` is the one
  non-Python exception.)
- Never add a `build`, `prepare`, `prepack`, or `install` npm script; OpenCode
  installs from Git through pacote and that breaks the install.
- A release is a tag that matches `package.json` and both README install
  lines, with a `CHANGELOG.md` section.
- **Git discipline.** Atomic, pushed commits (one change, one reason, test shown
  to fail first), so any change is individually revertible; tag known-good
  milestones `checkpoint-YYYY-MM-DD-<what>` (never a release tag). The flow
  harness also checkpoints the workspace per passing phase and reverts a
  breaking change rather than carrying it forward.

## Flow harness: the hidden grade is the oracle, and keep it agnostic

The spec-driven flow (`learn/code/flow_run.py` + `extensions/mellum-flow.ts`)
drives the fixed model through a suite; the lessons that held up:

- **The suite's hidden grader is the oracle; the examiner's self-authored gate is
  a proxy.** A brittle gate can false-fail a correct build (score each phase on
  its own gate so one can't cascade); a weak gate can pass a wrong one. Judge by
  the hidden grade.
- **Agnostic — never code to the eval.** Fixes are general test/harness
  discipline with no suite-specific route, table, column or expected value;
  reading the grader to diagnose is fine, encoding its answers is not.
- **For a fixed small model, prefer harness guarantees over prompt rules** — a
  prose rule lands unreliably; restore the fixture before grading, score
  per-phase, inject the real schema, git-checkpoint each phase. These don't
  depend on the model behaving.

## Glossary

`learn/glossary.md` is the single source of terminology. It uses `###`
entries parsed by `zensical-glossary`; every page’s first prose occurrence of
a term is linked automatically. Do not hand-link a term.

- When a page introduces a concept, add or update one `###` entry in the
  glossary before finishing the page.
- Check the page’s first occurrences after a build; the extension skips code,
  headings and links by design.
- Build with `uv run zensical build` (preview with `uv run zensical serve`); CI
  does the same. Both packages are `dev` dependencies, so run `uv sync` after
  pulling a change to `pyproject.toml` or `uv.lock`.
- Borrow shared terms from `../satyrn-evals/_engine/glossary.md` when they
  mean the same thing (`guard`, `finish nudge`), but define the local meaning
  rather than copying a Satyrn-specific contract.

## Driving the worker: don't trust its self-exit (a lead under test)

The worker decides when it is done, and a run can exit confident on an
incomplete, self-authored test — the Phase 4 id miss. The direction being
measured is to define "done" with an acceptance test that is **external** (the
worker did not write it), **complete** (the whole spec, not the subset the
worker chose) and **unweakenable** (the worker cannot edit or delete it), and
to verify a run by re-running that test and re-dispatching its failure, never
by the worker's final message. This is the mediated test plus the
freeze-the-oracle guard; the rung 9 results behind it are screens, so treat it
as the lead it is, not a settled rule. See the
[exit-gate note](docs/superpowers/research/2026-10-18-harness-exit-gate.md), the
M.11 row in [`ROADMAP-M.md`](ROADMAP-M.md) and the BACKLOG entries "The mediated
test" and "Freeze-the-oracle exit gate".

## Keep the changelog current

`CHANGELOG.md`'s `## [Unreleased]` section is kept up to date as work lands,
not written at release time. This is a standing rule.

- **With each change:** a commit that changes what a user installs, runs,
  configures, or reads (extensions, prompt, templates, skill, README,
  recipe, the ladder's commands or records) adds its entry under
  `[Unreleased]` in the same commit, in the existing `Added` / `Changed` /
  `Fixed` / `Removed` headings. Internal-only commits (SDD records,
  backlog, roadmap, tests alone) need no entry.
- **At checkpoints:** at the end of each plan task, at cycle close, and
  before a tag, compare `[Unreleased]` against
  `git log <last tag>..HEAD --oneline` and add anything missing.
- **At release:** `[Unreleased]` becomes `## [x.y.z] - YYYY-MM-DD` in the
  same commit that bumps `package.json` and the README install lines, and a
  new empty `[Unreleased]` goes above it.
- Entries say what changed for the user and why, in a sentence or two, not
  the commit subject.

## Finishing a feature cycle

Update the cycle's Status cell and the `## Now` pointer in `ROADMAP.md`, close
the plan with `## Result`, move it to `plans/archive/`, and remove any backlog
entry the cycle resolved. At close, also add a glossary entry for any concept the
cycle introduced, and a `learn/pathologies.md` entry for any failure shape its
evidence showed — or nothing, if it showed none. Confirm claims against linked evidence, pass
`node --test tests/docs-caps.test.mjs` and `npm test`, and reconcile the
changelog before finishing the branch. A cycle may close before a release
tag. This is a standing rule.
