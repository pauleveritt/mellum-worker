# F.7 — Qualified phase acceptance

## For Andre

**Date:** 2026-11-09. **Cycle:** F.7, infrastructure, cut from `658bbea5`. **Why:** acceptance is
the only thing that lets a run claim a finished phase, and the [review](../research/2026-11-09-phase-worker-review.md)
found one false failure and one coverage hole in Medium before any more inference is bought.
**Result sought:** every written Easy and Medium requirement traced to a check or an explicit,
reasoned gap; corrections versioned beside the originals; each repair shown on real builds both
ways. **No model run, runtime remedy, preset or F.8 work.** Recorded scores stay as they are.

### What already holds (checked 2026-11-09, read-only)

- Medium's current grader digest is `bb62e770…`, the digest in all six [Medium screen](../../../evals/2026-11-09-medium-final-screen/table.md) records.
- Retained Base r02/r03 replay to the four recorded misses (identity plus three route/order checks).
- Your `ladder/fixtures/acceptance/test_medium.py` (`67f0138f`) passes known-good 8/8. On r02/r03
  it passes seven of eight: it misses both ID defects and false-fails `Status: Open` on `>Open<`.
- Easy's roadmap has four phases; its grader, mediated test and prompt cover Phase 1 only.

### Goals

1. **Requirement map.** `suites/{easy,medium}/acceptance-map.json`: one entry per requirement
   with source line, hidden check ids, mediated check ids, and a status of `covered`,
   `mediated-only`, `hidden-only` or `gap` (a gap needs a reason). A test parses the roadmap and
   fails if any phase bullet is unmapped or any named check does not exist. Tech-stack and
   layout rules are hand-listed entries.
2. **Medium status correction.** A card's state label may be the exact word (today's form) or
   that word after a `Status`/`State` caption and colon, including nested markup and a form
   beside it in the same element. Negation, both words, hidden text, and the word appearing only
   in complaint text stay rejected, by the hidden grader and the mediated test alike (the mediated
   test must be a superset of the oracle). This applies to Medium only: Easy's Phase 4 says "a badge
   reading exactly", so Easy keeps the exact form.
3. **Shared ID allocation.** A new Medium hidden check and mediated check interleave direct and
   route creation (direct, route, direct, route): integer ids, strictly increasing, unique, and no
   earlier id changes. The existing check id is retained unchanged. Medium current becomes 19 checks.
4. **Versioning.** The pre-correction Medium grader and mediated tests are retained byte for byte
   as bundle `658bbea5` under `grader-versions/`. `--grader` selects the hidden checks; bundled
   mediated files are stored and byte-tested, not wired (no runtime change). A test asserts that
   bundle's digest equals `bb62e770…`, so the recorded scores remain reproducible.
5. **Easy Phases 2–4 (Paul's decision; recommended yes).** Author hidden and mediated checks from
   Easy's own roadmap into a selectable bundle, `f7-roadmap`, holding the 13 Phase-1 checks
   unchanged plus Phases 2–4, with Easy-specific strictness (exact badge, UTC timestamp, Bootstrap
   card). Easy `current` stays at 13 checks with digest `33764460…`, asserted by test. Easy's map
   resolves check ids against this bundle. R.1a needs this; nothing at runtime selects it until
   F.8/R.1a wires it.
6. **Qualification.** New tests fail first on the unrepaired code. Known-good builds and valid
   alternatives pass. The r02/r03 builds are kept as fixtures with provenance. Mutation witnesses
   fail: separate high-range route counter (passes today's hidden check), renumbering on append,
   route overwrite with `max+1`, negated label, both labels, label only in complaint text.
7. **Andre comparison.** Run the Medium witnesses through his `test_medium.py` and his `67f0138f`
   Medium grader, and a small Easy-native Phase-1 witness set through his four-check Easy grader,
   copies pinned by sha under the research sibling directory. Record a matrix. Ours stands wherever
   it rejects more real defects or accepts more valid builds; any written requirement his catches
   and ours misses is added to our mediated test and mapped.

### Non-goals and anti-goals

Not changing any recorded score or the F.6 verdict. Not deleting a legitimate requirement because
the hidden grader omits it: those stay `mediated-only` in the map. Not adding mediated-only
requirements to Medium's hidden grader here, because that would change its meaning beyond the two
repairs. Not changing prompts, remedies, presets, budgets or harness runtime paths. Not touching
Hard, though it shares the same label predicate; that goes to the backlog with R.3 as its reopen.
A fix that passes r02/r03 by naming their markup or values is void: predicates derive from the
written contract.

### Calls left to the builder

Fixture directory name; whether the matrix is a parametrized test or a recorded script (it must be
reproducible by one command); exact caption punctuation accepted beyond the colon; mediated test
wording. Mutants that show further gaps are repaired in the same cycle, test first, in the
mediated test; Medium's hidden grader stays at the two repairs and 19 checks. A further hidden
defect goes to the backlog unless it blocks a listed witness.

## Ladder run

None. Deterministic replay decides: real builds, positive and negative, through the trusted grader
path, plus `harness qualify` for both suites and bundles. Model rates are out of scope; a corrected
grade is never reported in place of a recorded one, and any later rescore is labelled by bundle.

## Persuasion → enforcement

No Pi hook applies to offline grading, and no prompt text changes. Enforcement is by trusted
grader selection and digest (`grader_history`), the map-completeness test, byte-retention tests and
the qualification matrix in `npm test`, so an unmapped requirement or a silently changed
historical grader fails the suite. Later `check/mediated-test` runs receive the corrected Medium
file; `mediated.json` already records each handed file's sha256, and nothing here starts a run.
