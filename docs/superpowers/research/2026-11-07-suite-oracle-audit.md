# Suite oracle audit at bc5db20

## For Andre

**What is measured:** deterministic hand mutations of the three known-good builds,
scored against the shipped hidden checks at `bc5db20`, plus historical byte and
grader comparisons. Source: local repository and scratch audit, 2026-11-07.
**What is conjecture:** how often a model would produce these failures, whether a
remedy would prevent them, and any change in model pass rate after repairing checks.

The review found that every hidden test function can fail, yet incomplete
assertions allow incorrect builds to pass and one valid board order to fail.
The [repair design](../specs/2026-11-07-suite-oracle-repairs-design.md) addresses
these as F.4 before R.1. No archived F.3 plan or historical run is rewritten.

## Evidence and findings

The input revision is `bc5db208211c97a6956fa93225b40929804c0c9c`.
Every experiment used copies; no source or main-checkout file was edited.
Python ran through `uv run`, with pytest supplied by `--with pytest`.
The retained [summary](2026-11-07-suite-oracle-audit/summary.json) contains derived
outcomes and per-check witnesses; raw scratch output is not committed.

| Area and source at input revision | Executed witness | Outcome before repair |
| --- | --- | --- |
| Harness `score_workspace_details`, :987 | Workspace conftest replaces item runtest with a no-op | Known-broken Easy becomes 4/4 |
| Same invocation | Workspace pytest.ini deselects checks | Known-good becomes a grading failure |
| Shared Phase 4, :109 | Valid newest-first board | Hard 33/34, sole failure unstated initial ordering |
| Hard migrations, :31 | Named index on wrong table/column | 34/34 |
| Hard migrations, :50 | Empty view; ordinary table replacing view | Each 34/34 |
| Hard migrations, :59 | NOT NULL note column | 34/34 |
| Hard migrations, :77 | Rerun changes ticket notes, ledger unchanged | 34/34 |
| Hard Phase 6, :10 | Return fixed report totals without reading database | 34/34 |
| Medium Phase 4, :62 | No model state changes; render both state words | 18/18 |
| Medium Phase 4, :62 | Change every complaint's state | 18/18 |
| Shared Phase 3, :53 | Form controls outside form | Medium 18/18; Hard 34/34 |
| Shared Phase 4 | Remove state-change controls | Medium 18/18; Hard missing Resolve 34/34 |
| Medium Phase 3, :35 | Retain only latest five complaints after append | Standard order 18/18; reversed modules 16/18 |
| Shared Phase 4, :112 | Reverse board on resolve and again on reopen | Medium 18/18; Hard 34/34 |
| Medium Phase 4, :38 | Reset counter after seeds, reusing their IDs | 18/18 |
| Identity | String IDs in Medium; float IDs in Hard | 18/18 and 34/34 respectively |
| Hard Phase 5, :13/:25/:45 | Bad rejection effects/redirect/audit fields or missing archive audit | Each 34/34; summary lists individual builds |
| Harness hidden-only invocation | Add a failing project-owned test | Easy 4/4; Hard 34/34 |
| Easy Phase 1, :26 | Redirect root with 307 to correct HTML elsewhere | 4/4; direct request confirms 307 |
| Easy Phase 1, :48 | Remove nav landmark; brand only in comment | Each 4/4 |
| Shared contract, :28 | HTML4 PUBLIC doctype | Easy 4/4 |
| Easy Acceptance, roadmap :41-54 | Missing templates/assets/title/hero/launcher behavior | Each tested mutant 4/4 |
| Phase 2, :26/:75 | Seed sentence with suffix; numeric tokens instead of date | Medium each 18/18; Hard seed suffix 34/34 |
| Hard Visits, :8 | Wrong optional defaults; integer whole-number averages | Each 34/34 |
| Harness layout report, :482 | Delete project metadata, lock, starter and roadmap | No created/modified/out-of-layout paths reported |
| Current versus old timestamp grader | Per-instance timestamp through post-init | Current Medium 18/18, Hard 34/34; old each loses one check |

Known-good baselines: Easy 4/4, Medium 18/18, Hard 34/34.
Known-broken controls fail: Easy language; Medium three POST redirects;
Hard two report-sum checks. Every one of 56 test-function instances has an
executed failing witness; this does not establish clause completeness.
Hard's ordinary known-good build also passes with reversed module order.

All 25 historical prompt/spec files materialize byte-identically to `16cf9f9^`.
Medium/Hard's first four grader modules are byte-identical; Easy's Phase 1 module
matches both. Expected node IDs match collected test-function definitions.
Hard prompts map uniquely in order: P1-P5, index, P6, backfill, view, P7, note.
Single-source tests passed 37/37; eight targeted harness tests passed.

## Inspection findings and limits

- Hard tech-stack :22 prohibits all ticket-row changes; roadmap :168-180
  explicitly permits/requires the backfill. The authoritative roadmap resolves
  priority, but the secondary instruction still misdirects an implementer.
- Default prompts point to the phase/spec. Medium joined/split still restate
  workflow instructions; the clean-prompt invariant only tests defaults.
- Layout permits all imported modules, plus extra undocumented helpers.
  Out-of-layout writes are recorded but do not enter the overall pass decision.
- Fresh runs expose no grader files during the session; scoring leaves them
  afterwards. The scorer uses mutable workspace metadata and inherited environment.
- Easy requests only Phase 1. Later phases in its roadmap are outside its run.
- No live model measurements, exhaustive input exploration, hostile-code sandbox
  assessment, or historical-record rescore was performed.

## Ladder run

No ladder/model run: this audit diagnoses deterministic tests and harness behavior.
The witnesses establish concrete false outcomes, not comparative model rates.
Repairs must retain legitimate positive cases as well as reject these mutants.

## Persuasion → enforcement

No Pi hook or prompt policy was tested or changed. The evidence supports repairing
the offline test runner and assertions, independently of worker obedience.

## What would falsify this

A witness that no longer produces its stated outcome against the exact input
revision, or a cited requirement that actually mandates the rejected ordering.
A repair invalidates a bug witness prospectively, not this dated observation.

## Risks

Finite mutants cannot prove oracle completeness. A trusted pytest environment is
not a security sandbox for arbitrary application Python. New graders change the
measurement instrument, so historical and repaired pass rates need distinct identity.
