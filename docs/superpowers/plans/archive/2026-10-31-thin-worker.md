---
phase: LC
feature_cycle: LC.29
cycle: 1
lifecycle: superseded
---

# Thin worker — plan

Executes [the thin-worker spec](../specs/2026-10-31-thin-worker-design.md):
make `mellum-worker.ts` mode + commands only, move remediation and delegation
into remedy units, retarget `check` to llama-server, split acceptance, rebuild
the tier presets to nest and match measurement, and align the lessons.

Branch `refactor-thin-worker`. Each step is test-first and commits on its own.

## Step 0 — approval (resolved 2026-10-31: keep the baselines)

Decided: refactor only, keep today's numbers. The refactor is
**behaviour-preserving for the measured arm** — `baseline-worker` = the thin
worker + the exact units the measured `worker` ran (`context/narrow-tools`,
`context/add-project-facts`, `guard/break-repeat-loops`,
`nudge/nudge-empty-turn`, `guard/block-foreground-server`,
`guard/stay-in-workspace`; **not** `context/use-short-prompt`, which the fat
worker never used). A parity run (Step-2/4 gate) proves equivalence; the
2026-10-31 Q4/A6000 records stand as the `baseline-worker` result, no re-run.

## Step 1 — check → llama-server only

- Point expected settings at `templates/llama-model-settings.json`
  (`provider: llamacpp`, `nCtxMin: 50000`, `baseUrlDefault`).
- Remove oMLX admin-auth probing and vLLM branches from `mellum-check.ts`.
- `DEFAULT_MODEL` → the llama-server Mellum id; keep the session-model fallback.
- Test first: `mellum-check` reports a clean match against a llama-server probe
  and flags a mismatch; the oMLX/vLLM paths are gone.

## Step 2 — strip the worker

- Delete from `mellum-worker.ts`: the `withFacts`/`factsBlock` injection and the
  `narrowTools` call inside `filterForMellum`; the `createGuardSet` wiring
  (`tool_call`, `turn_end`, `agent_before_settle`, `guardBlocks`/`nudges`).
- Move `collapseHandoffs` + the `context` hook to `delegate/collapse-handoffs`,
  and the `session_before_compact` refusal to `delegate/guard-compaction`
  (new units, each shown to fail first against the behavior the worker gave).
- `filterForMellum` keeps only: drop pre-marker history, swap the system prompt.
- The worker's tests shrink to mode + commands; the moved behavior is proven by
  the units' tests. Keep `narrowTools`/`withFacts` exported (the units use them)
  or move them to the units — whichever leaves one home per function.

## Step 3 — split acceptance into single-principle derivers

- From `mellum-acceptance.ts`, one deriver per principle:
  `acceptance/app-boots-and-routes`, `acceptance/page-renders`,
  `acceptance/named-nav-links`, `acceptance/redirect-contract`,
  `acceptance/required-text`.
- Make these and the verify/redispatch gate (`mellum-verify`) loadable as remedy
  units so a preset can name them.
- Each deriver: dry-run green on the done fixture, red on its own miss (the
  redirect deriver red on the Phase-4 id-in-route-only build), per AGENTS.md §6.

## Step 4 — rebuild the tier presets

- `baseline-worker` = thin worker (± `delegate/*`, per Step 0).
- `easy` = baseline + the units the recorded easy win used
  (`tool/background-long-commands`, the acceptance derivers it needed, `mellum-verify`).
- `medium` = easy + the redirect deriver (the recorded medium win's addition).
- `hard` = medium + its units.
- Each preset cites the `evals/` record it encodes. Nesting is enforced by a
  test: `easy ⊂ medium ⊂ hard`.

## Step 5 — align the lessons

- Fold in [the lesson-alignment plan](2026-10-29-uniform-lessons.md) scope: every
  lesson that cites a host says llama-server, not oMLX/vLLM, as a live
  instruction; dated corrections where a number changed.
- Point lessons at the new unit/preset names where they reference remediation.

## Gates (every step, and at close)

- `npm test` and the moved unit tests green; new tests shown to fail first.
- `node --test tests/docs-caps.test.mjs`; `uv run zensical build` clean.
- `CHANGELOG.md` `[Unreleased]` updated per step (user-facing: worker surface,
  check, presets, lessons).
- **Parity run (the baseline-consistency gate):** one local Q4 run of the thin
  worker + `baseline-worker` preset, confirming it reproduces the measured
  fat-worker behaviour (n=1 presence check — the stack is wired and behaves
  equivalently, not a new comparative rate). Recorded in `evals/`. Today's
  2026-10-31 Q4 numbers stand as the `baseline-worker` record if parity holds.

## Result

Superseded 2026-11-07 by the re-boot, which replaced the Learning Center phase with F (Floor),
R (Remedies) and A (Architect); see `ROADMAP.md` and `ARCHIVE.md`. LC.29 stands as it is on
`main` at 63b6563; its further work continued on the unmerged `lc40-thin-worker` branch, which
is a reference only. Nothing here was measured at close. Anything still wanted returns as an F, R
or A row through its own small cycle.
