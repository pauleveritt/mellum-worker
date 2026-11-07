# Does coder feedback help? — preregistration

Date: 2026-10-26. Status: preregistration, no result yet. Fixes the arms, n,
scoring and rule BEFORE the run, so the decision isn't eyeballed off one-off
runs (which flip-flopped: the raw feedback looked like it caused gate-editing
on phase 4; the labelled feedback then looked like it kept the coder on the
app — neither is a measurement).

## Background

`test()` can write the failed gate's labelled failure to `REVIEW.md`, which
`code()` reads, so the coder sees what its APP did wrong on a retry (see
`2026-10-26-coder-feedback-loop.md`). The concern: showing a small model its
failures might make it edit the test instead of the code. The labelling
(fix-the-app, strip test paths) is meant to prevent that. Whether the net
effect helps or hurts is unmeasured.

## Arms (one binary, env-toggled)

- **control** — `MELLUM_CODER_FEEDBACK=0`: the coder gets NO gate-failure
  feedback (the known-good path; the 31/34 baseline came from here).
- **feedback** — default: `test()` writes the labelled, path-stripped failure
  to `REVIEW.md` for the next `code()`.

Everything else identical: hard suite, forced flow, Mellum 2.1 6-bit via oMLX,
`--thinking medium --context-window 40000 --attempts 6 --concurrency 1
--retry-concurrency 2`.

## n and scoring

- **n = 3 per arm** (6 hard runs total; a screen-plus, since one run can't
  separate the feedback effect from the examiner drawing a different gate).
- **Scoring: the hidden grader** (`result.json` `graded`, plus the granular
  hidden score where available) — never the examiner's own gate. Report, per
  run: hidden grade, visible pass, which phases passed (esp. 4 and 5), and
  wall-clock. Watch specifically whether the coder edits a gate test.

## Decision rule

Adopt **feedback** as the default only if, across the three runs, its hidden
grade is **>= control** AND it does not regress the easy phases (no new
gate-editing / phase-3–4 thrash that control doesn't show). If it's worse or a
wash, keep control (feedback off) and record the negative result. A single
run deciding either way is a lead, not the verdict.

## What would falsify / risks

- **High run-to-run variance.** The examiner writes a fresh gate each run and
  the coder samples differently, so n=3 may still be noisy; treat a small
  hidden-grade gap as a wash, not a win.
- **The confound we can't remove cheaply:** the two arms don't share frozen
  gates (the examiner runs per-arm). The hidden grade is the outcome, which is
  more stable than the proxy gate, but it's still per-run.
- Everything via `uv run`; the live feed visible; runs recorded under
  `evals/` if kept.
