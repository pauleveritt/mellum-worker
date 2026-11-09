# F.7: qualified phase acceptance

## For Andre

**Date:** 2026-11-09. **Cycle:** F.7, cut from `658bbea5` ([design](../specs/2026-11-09-f7-qualify-acceptance-design.md)).
**What is measured:** deterministic replay of real and mutated builds through the trusted grading
path; retention and digest checks; the [matrix](2026-11-09-f7-qualify-acceptance/matrix.md). No
model or GPU ran. **What is conjecture:** whether the corrected acceptance changes any model's
outcome or cost. Nothing here says so, and no recorded score changed.

**What changed.** Medium's hidden grader and mediated test accept a captioned state such as
`Status: Open`, and both check that direct and route creation share one rising ID sequence.
Medium's hidden grader goes from 18 to 19 checks. The original stays selectable as `--grader
658bbea5`. Easy gains a selectable four-phase bundle, `--grader f7-roadmap` (30 checks); Easy's
default stays at its 13 Phase-1 checks. Every written Easy and Medium requirement is mapped.

**What to look at:** the Medium row counts below, and whether you read the Andre columns the way I do.

| Medium, 33 defective and 10 valid builds | Defects rejected | Valid builds passed |
| --- | ---: | ---: |
| Ours, hidden `current` | 33 | 10 |
| Ours, mediated | 33 | 10 |
| Ours, original `658bbea5` | 30 | 7 |
| Andre, `test_medium.py` | 11 | 6 |
| Andre, grader at `67f0138f` | 2 | 9 |

On Easy Phase 1 (six defects, three valid), ours rejects 6/6 and passes 3/3 on both hidden and
mediated; Andre's four-check grader rejects 1/6 and passes 3/3. **These counts describe our chosen
witnesses, not a defect rate**, and his files were written against his own roadmap and stack.

### Original scores stand

The `658bbea5` bundle reproduces digest `bb62e770…`, the digest in all six [Medium screen](../../../evals/2026-11-09-medium-final-screen/table.md)
records. Retained Base r02/r03 replay under it to exactly the four recorded misses. Under
`current` each misses exactly two of 19: the retained identity check and the new cross-path check.
Their route/order failures disappear; with only their IDs repaired, both pass all 19. These are
replays of saved builds, not rescored runs, and the n = 3 Medium screen stays at zero strict passes.

### The corrections

- **Status.** A state label is the exact word, or that word after a `Status`/`State` caption and
  colon, read without any controls beside it. Negation, hidden text, two states, a state that
  never changes, and the word only in complaint text remain rejected. Easy keeps the exact badge
  its roadmap asks for. A hole also closed: `Not` directly before the word in nested markup
  (`<p>Not <strong>Open</strong></p>`) passed the original.
- **IDs.** The sequence is direct, route, direct, route; strictly rising integers; no earlier ID
  changes. A separate route counter passed the original check and now fails. The original check
  keeps its name and body.
- **Mediated superset, on these witnesses.** The first matrix found Medium defects (and the Easy
  redirect) that hidden rejected and mediated passed: redirected pages, hidden navbar, scattered
  date numbers, disabled inputs and buttons. A fresh branch review found more: a crash on HTML
  comments, unusable fields, and over-strict Easy checks. Each is repaired test first. Hidden-only
  false failures it found stay as [backlog entries](../../../BACKLOG.md).

### Requirement maps

`learn/code/suites/{medium,easy}/acceptance-map.json`: 42 entries for Medium, 44 for Easy. Tests parse each roadmap
and fail on an unmapped phase bullet, a named check that does not exist, a status that disagrees
with its checks, or a requirement left to hidden grading alone.

| | Covered | Mediated-only | Gap |
| --- | ---: | ---: | ---: |
| Medium | 35 | 5 | 2 |
| Easy | 41 | 2 | 1 |

Mediated-only keeps legitimate requirements the hidden grader omits: uvicorn reload, template
inheritance, the short welcome (noted on its entry), the project's own tests. Gaps carry reasons:
pinned versions (fixed by `uv.lock`) and Medium's Bootstrap CDN, named in its tech stack but in no
Acceptance list.

### Reconciling Andre's tests

Keep ours wherever the matrix separates them. No defect in the matrix is rejected by his and
passed by ours, so nothing was added from his to ours. His `test_medium.py` is the visible
frozen gate of his one-pass arm and is deliberately small. It false-fails `Status: Open` on `>Open<`
and a textual date, and it passes both ID defects; r02/r03 fail it only on that same label check.
His grader predates F.4 and passes most defects here. Both are inputs, not ground truth, and his
later Medium result is on another stack.

## Ladder run

No run. Deterministic replay decides, per the design. `uv run python learn/code/qualify_matrix.py`
reproduces the matrix (about 15 minutes; `--write` regenerates it). `harness qualify` reports
QUALIFIED for Medium `current` and `658bbea5`, and Easy `current` and `f7-roadmap`.

## Persuasion → enforcement

No Pi hook applies. `grader_history` digests and byte-retention tests stop a historical grader
drifting; map tests stop a requirement going unmapped. `npm test` checks the committed matrix's
invariants and replays a sample of rows live; only the script recomputes every row. No prompt text changed; `mediated.json` records the sha256
of whichever mediated file a later run is handed. Runtime wiring of the four-phase bundle is F.8.

## What would falsify this / Risks

A valid build the corrected predicate rejects, or a defect it passes, requires a dated correction.

- **Witness choice bounds the claim.** 33 and 6 builds are finite, and the mediated column leaves
  out the two checks that start a real server. "Superset" means on these witnesses.
- **The label predicate reads elements.** State as bare text among other card text, with no element
  of its own, is still rejected. Visibility is `hidden` and inline style only: CSS such as Bootstrap's
  `d-none` is not observed, so a label hidden that way still counts on hidden and mediated.
- **The Easy bundle cannot grade a Phase-1-only build.** Its Phase 2–4 modules import `models` and
  need the phase scoping F.8 adds. Nothing selects it at run time yet.
- **Hard shares the label predicate and wording.** Deliberately out of scope; see [the backlog](../../../BACKLOG.md).
- **Mediated tests changed.** Easy's Phase-1 original is retained in the bundle and Medium's in
  `658bbea5`; a comparison across this change must say which file was handed.
