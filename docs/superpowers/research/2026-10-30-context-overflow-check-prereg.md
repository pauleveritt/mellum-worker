# Preregistration: E2 Reading More Than Fits, lesson check

**What is measured.** Nothing yet: fixed on 2026-10-30 before the deciding
run, at the commit that adds this note, under the condition-produced rule
([spec](../specs/2026-10-29-uniform-lessons-design.md), correction of
2026-10-29).

**What is conjecture.** That reading eight 40 KB notes whole sets off at
least one compaction on a 64k window, and that `context/trim-tool-output`
keeps the session from compacting while it still finds every owner.

## The condition

The LAN vLLM host (`scripts/baseline/lan-profile/`, the 6-bit Mellum,
`contextWindow` 65,536), Pi 1.3.0 with its default compaction (enabled,
reserve 16,384 tokens). The challenge, `learn/challenges/context-overflow/`:
eight notes, about 80,000 tokens in all, each naming its owner only in its
last section; `record.json` caps `compactions` at 0.

## Arms and running

`scripts/lesson-check.sh E2`, the page's two lines:

- **Before:** `--remedy context/repair-think-tags`
- **After:** `--remedy context/repair-think-tags,context/trim-tool-output`

Both `--repeat 1 --deadline 900 --stall 180`, no `--grade`.

## Rule

- **The lesson holds** if the before session FAILS with a record failure on
  `compactions` and the after session PASSES (hidden test passed, no record
  failure).
- A before session that fails without a compaction does not count as the
  lesson holding; it is recorded and the check is run once more.

## Leads behind it

Two screens, one session per arm: before 2 then 6 compactions (the second
also wrote a wrong list); after 0 compactions, peak 4,918 tokens, passing.

## What would falsify this

A bare-of-the-unit session that reads the notes without compacting: then the
model searched by itself and the condition does not force the failure.

## Risks

- One session per arm.
- Pi's compaction defaults could change with a Pi upgrade; the record names
  Pi 1.3.0.

## Result, 2026-10-30

Run at `687e7b3` (`runs/E2-check-20261029T223047Z-687e7b3`, recorded under
`evals/2026-10-30-context-overflow-check/`).

- **Before:** FAIL: 13 compactions, peak 50,720 tokens, 99 requests, and the
  hidden test failed (a wrong owners list).
- **After:** PASS: no compaction, peak 5,326 tokens, 13 requests.
- **The lesson holds.** With the two screens, the session without the unit
  compacted in 3 of 3 sessions (2, 6, 13 times); a lead on reliability, not a
  rate.
