---
phase: F
feature_cycle: F.3
cycle: 1
lifecycle: closed
---

# F.3 — a trustworthy instrument

## For Andre

- **Why:** a read-only review of `integration` (2026-11-07,
  [note](../../research/2026-11-07-instrument-review.md)) found two things that would make R.1's
  numbers wrong: the suites are the pre-correction ones, and the budget is mis-measured.
- **Suites:** the single-source suites come over from the old branch (16cf9f9, 7b791ff, 9105bd4):
  each roadmap is the one authority, with an Acceptance list per phase. The prompts name the phase
  and point at the spec. Hard gets `migrations.py` in its layout, its dead assertion goes, and its
  Phase 5 grader no longer depends on module order. `--specs original` reruns the old prompts byte
  for byte.
- **Budget:** `wall` was the gap between the first and last trace rows (F.1 showed 59.8 s for a
  900 s hang). It is now the elapsed time of the Pi processes. `run.json` gains `completion`
  (settled, stalled, deadline or error). `turns` now counts the assistant replies that completed,
  and `requests` counts every provider request.
- **What to look at:** the smoke table in `## Result` shows the new fields on two Vanilla Easy
  sessions, and one of them ran out its deadline.

## Scope

In: the items above, plus `AGENTS.md`'s "Run standard" (the floor is measured on
`learn/code/harness.py` with thinking on, not on `scripts/screen.sh`), and the path-dependent
test in `tests/mellum-delegate.test.mjs`. Out: remedies, the settle-layer fixes, a stronger
`qualify`, the port-8000 preflight, and the acceptance package and its drivers, which arrive with
R.1, the cycle that reads them.

Calls made in brainstorming (Paul: "go with your recommendation"): the note is built from the
review's summary in `FIXES.md`, because the full text was not kept. Of the old `execution.json`
commit (d9dd5d2), only the execution record and `completion` are ported. Pinned grader versions,
`grade.json` and the scorecard printer stay out.

## Task 1: Records

- [x] This plan, the review note, and the F.3 Status set to active in `ROADMAP.md` with `## Now`
      pointing here. `node --test tests/docs-caps.test.mjs` passes. Commit: `docs: open F.3`.

## Task 2: Single-source suites

Files: `learn/code/suites/{easy,medium,hard}/**`, `learn/code/harness.py` (`--specs`),
`learn/code/tests/test_suites_single_source.py`, `learn/getting-started/the-harness.md`,
`CHANGELOG.md`.

- [x] Port the test file from `lc40-thin-worker`, dropping three tests whose subjects are not on
      `integration`: `test_the_base_preset_is_the_measured_tier3_stack` and the two Medium
      mediated-test tests. Run it and see it fail (no Acceptance lists, no `original` variant).
- [x] `git checkout 9105bd4 -- learn/code/suites`. Integration's suites equal `16cf9f9^`'s, so this
      is the three commits' suite content and nothing else. No `mediated/` directory comes along.
- [x] `--specs` drops its `choices`. Its help names `original`, `joined` and `split`.
      `load_variant` already refuses an unknown variant.
- [x] Port the-harness.md's paragraph about `original`, and add one `Changed` entry under
      `[Unreleased]`.
- [x] The test file and the full learn/code suite pass. Commit:
      `feat: make the suites single-source, with the roadmap as the authority`.

## Task 3: Honest budget

Files: `learn/code/harness.py` (`run_suite`, `report`, `_run_sessions`),
`learn/code/tests/test_harness.py`, `CHANGELOG.md`.

Interfaces:

- `run_suite` writes `run/execution.json` with `elapsed_seconds` (float, `time.monotonic` from
  the first Pi start to the last Pi end, summed across a suite's prompts), `exit_code` (the last
  child's), `termination_reason` (`"exited"`, `"deadline"` or `"stalled"`) and `cleanup_ok` (no
  live process left in a Pi group or the workspace after the sweep). It writes the record in the
  `finally`, so a stopped run still gets one.
- `report(run)` returns `wall` as `execution.json`'s `elapsed_seconds`, or `None` when that file
  is absent. A trace's timestamps never stand in for it. `turns` counts the assistant
  `message_end` rows whose `stopReason` is not `"error"` or `"aborted"`. `requests` is unchanged.
- `execution_outcome(run) -> dict` gives `completion`, which is `"deadline"` or `"stalled"` from
  the termination reason, then `"error"` when the exit code is not 0 or the last assistant reply
  ended in an error or abort, and otherwise `"settled"`. It also gives `exit_code` and
  `cleanup_ok`. `_run_sessions` merges these into `run.json`. A leaked server stays a separate
  fact, in `cleanup_ok` and `leaked`, so it does not turn a settled session into an error.

Tests, each shown failing first, all against the existing fake-Pi fixtures:

- [x] `test_a_run_records_process_elapsed_time`: `fake-pi.sh`. `execution.json` has
      `termination_reason == "exited"`, `exit_code == 0`, `elapsed_seconds > 0`, and
      `cleanup_ok is True`.
- [x] `test_a_deadline_is_recorded_as_the_completion`: `fake-pi-slow.sh` with `deadline=1`.
      `run.json` has `completion == "deadline"` and `wall >= 1`.
- [x] `test_wall_is_the_process_time_not_the_trace_span`: a trace whose rows span 1 s, and an
      `execution.json` saying 900. `report` gives `wall == 900`. Without the file, it gives `None`.
- [x] `test_turns_count_completed_replies_not_requests`: three `provider_request` rows and three
      assistant `message_end` rows, one with `stopReason: "error"`. `requests == 3` and
      `turns == 2`.
- [x] `test_a_settled_run_says_so`: `fake-pi.sh`. `run.json` has `completion == "settled"`.
- [x] Update any existing test that asserted the trace-span `wall`, and say so in the commit.
      Full learn/code suite passes. One `Changed` entry under `[Unreleased]`. Commit:
      `fix(harness): measure the budget from the process, and record completion`.

## Task 4: Run standard and a path-dependent test

- [x] `AGENTS.md` "Run standard": the floor and the R cycles are measured with
      `learn/code/harness.py` (Pi's default thinking, which is on). `scripts/screen.sh` is the
      ladder rig, thinking off, and its numbers do not mix with the harness's. Commit:
      `docs: name the harness, thinking on, as the run standard`.
- [x] `tests/mellum-delegate.test.mjs` "smokeCommand is agnostic": make the suite-value check
      ignore the script's own absolute path. Show it fail first by running the test with
      `smokeCommand`'s path resolved under a directory named `roadmap` (a scratchpad copy). Then
      `npm test`. Commit: `test: check smokeCommand's arguments, not its install path`.

## Ladder run

A smoke on the harness, not a measurement: `harness.py run --suite easy --arm vanilla
--repeat 1` twice on the local llama.cpp server on `:8001` (Mellum 2.1 Q4_K_M, thinking on).
The first run uses the default deadline of 600 s. The second uses `--deadline 90`, so that its
deadline fires. The pass rule is about the record only: both `run.json` files carry `completion`,
a process-measured `wall`, and `turns` next to `requests`, and the second says `deadline`. The
hidden checks are reported, but nothing is concluded from them at n = 1. The watcher is on screen
during both runs. The record goes in `evals/2026-11-07-f3-smoke/`, with `run.json` and
`table.md` only.

## Persuasion → enforcement

Nothing in a session changes, and no Pi hook is added. This cycle is the instrument that R.1
uses to judge its hooks. Without it, a guard that saves 800 s of a foreground-server hang would
look like it saves nothing, and a deadline kill would read as a settled run.

## Close

- [x] `## Result` with the smoke table, budget beside quality. Archive the plan, update the
      roadmap's Status and `## Now`, and reconcile the changelog.
- [x] Green: `npm test`, `uv run --with pytest python -m pytest learn/code/tests`, and
      `cd ladder && uv run python -m pytest -m "not slow"`.
- [x] Squash onto `integration` (skill §15), check the trees are equal, then remove the worktree
      and delete the branch. Write the next brief in `FIXES.md`.

## Result

Closed 2026-11-07. Shipped as planned, with two deviations. **(1) `context` was a third budget
error,** found in the smoke and fixed in the cycle, test first: Pi's `usage.input` leaves out the
cached prefix, so the record read 1,703 for an 11,438-token prompt. **(2) The deadline session ran
at 20 s, not 90 s,** because both full sessions settled in under 50 s. Smoke
([record](../../../../evals/2026-11-07-f3-smoke/table.md)), Vanilla on Easy, Pi 1.4.0, thinking
on, n = 1 each. Two runs settled, at 48.6 s and 41.4 s, with turns equal to requests, context
11.4k and 11.2k, and hidden 4/4. The third hit its 20 s deadline at 20.0 s, with 7 turns of 8
requests and no hidden run. Gap for R.1: `run.json` does not name the Pi version, and a bare `pi`
here is Volta's 1.1.0. Green at close: npm 639/0 (3 skipped), learn/code 193 passed, ladder fast
201, docs caps 6/6. The trace-wall backlog entry was removed, and the glossary now has Turns,
Requests, Wall and Session completion as measured.
