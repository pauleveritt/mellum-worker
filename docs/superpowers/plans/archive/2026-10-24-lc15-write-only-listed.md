---
phase: LC
feature_cycle: LC.15
cycle: 1
lifecycle: closed
---

# LC.15: Write only the files you list

## Goal

Write the sixth findings lesson, **Write only the files you list**, and build
the one instrument it needs: a file-set check that says whether a run wrote
outside the layout the suite allows. The inventory put this page in the "new
instrument" column, because the graders score behaviour and lint and nothing
compares the written file set to a declared layout.

## Classification

Bounded, multi-part: an existing flow (the suites harness) gains one check,
then the page cites it. Recorded design, since no partner is available
overnight (delegated 2026-10-24):

- **The check is about paths, not behaviour.** After the child exits, hash the
  workspace and compare with the pristine copy taken before it started.
  Created and modified paths are matched against `allow` and `ignore` globs
  from the suite's `layout.json`; whatever matches neither is
  `out_of_layout`.
- **Artefacts are ignored explicitly.** `.venv`, `__pycache__`, `*.pyc`,
  `*.log`, `*.db`, `.pytest_cache` and `grader_tests` are declared in the
  suite's ignore list, so a run is not accused of writing a virtualenv.
- **A check that cannot fail is not a check.** The rules are unit-tested both
  ways: a clean workspace reports nothing outside, and a workspace with
  `notes.txt` reports exactly that.
- **The reading is a list, not a pass.** `out_of_layout` goes into `run.json`
  beside the passes, because the lesson's claim is that runs can pass and
  still be wrong.

## Inputs

- [The arm inventory](../research/2026-10-24-lc13a-arm-inventory.md), which
  says lesson 6 needs a grader rather than an arm.
- [The ditch](../../../learn/getting-started/ditch.md), the hand-driven
  session where writes outside the layout were observed.
- `learn/code/suites/easy`, `learn/code/harness.py`,
  [`learn/lesson-template.md`](../../../../learn/lesson-template.md).
- `main` at `d5881e6`; worktree `.worktrees/lc15-write-only-listed`, branch
  `lc15-write-only-listed`.

## Deliverables

- `learn/code/harness.py`: `file_hashes`, `layout_report`, a `layout` field on
  `Suite`, and `out_of_layout` in `run.json`.
- `learn/code/suites/easy/layout.json`, and the same for medium and hard.
- Unit tests for the check, in `learn/code/tests/test_harness.py`.
- `learn/lessons/write-only-listed.md`, six steps, badges 1–5, no oMLX
  citation.
- `tests/lesson-write-only-listed.test.mjs`, the index link, the nav entry, a
  changelog entry.
- At close: the LC.15 Status cell, `## Now`, `## Result`, plan archived.

## Constraints

- No worker, prompt, guard or suite-content change: this is a read-only check.
- The reading is preregistered here before the run: easy, `worker`, n=3, and
  the number reported is `out_of_layout` per session with the file list. A run
  that hits the 600 s deadline is reported as DEADLINE and not as a clean
  result.
- If no session writes outside the layout, the page says exactly that: a null
  for easy, with the ditch's hand-driven observation as the screen it is.

## Acceptance

`npm test`, `learn/code/tests` and `docs-caps` pass; `qualify --suite easy`
still passes; the page's numbers appear in the run record; no `evals/`
link on the page.

## Result

**Closed 2026-10-24.** Lesson 6, **Write only the files you list**, plus the
instrument it needed.

- **Instrument.** `layout.json` per suite (`allow`/`ignore` globs);
  `file_hashes` and `layout_report` in `learn/code/harness.py`; a `layout`
  field on `Suite`; `out_of_layout` in `run.json`. Three unit tests, both
  directions: a clean workspace reports nothing outside, one with `notes.txt`
  reports exactly that. `qualify` still passes for easy, medium and hard.
- **Reading.** Easy, `worker`, n=3: passes 2/3, and **`out_of_layout` empty in
  all three sessions** — 0 of 3 wrote outside the layout. The page states the
  null and rests on the ditch's hand-driven session, which it labels a screen.
- **Medium not run.** Every medium session in LC.13A died at the 600 s
  deadline, so a medium reading here would measure the deadline. Backlogged.
- **Mid-cycle fix.** The first three runs wrote the ignored artefacts
  (`.venv`, `__pycache__`, `.pytest_cache`) into `created`, producing a
  7,800-line `layout.json`. The ignore list now filters the record as well as
  the verdict; the three runs keep their pre-fix file lists and their verdicts
  were already correct.
- **Shipped.** Page, two-test lesson file, index link, nav entry, changelog.
- **Checks.** `docs-caps` 4/4, `npm test` 353/353, `learn/code/tests` 45/45,
  `zensical build` clean.
