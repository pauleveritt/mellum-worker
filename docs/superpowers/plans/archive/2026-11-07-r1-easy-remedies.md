---
phase: R
feature_cycle: R.1
cycle: 1
lifecycle: closed
---

# R.1 — Easy remedies, Base earned first

## For Andre

- **Goal:** earn `preset:base` against plain Vanilla, then measure the compile/import check and
  the mediated test on Base, and rebuild `preset:easy` from the winners. Spec:
  [`2026-11-07-r1-easy-remedies-design.md`](../../specs/2026-11-07-r1-easy-remedies-design.md); arms
  and rule: [preregistration](../../research/2026-11-07-r1-preregistration.md).
- **Order:** the settle fix first; then four ports and one new unit, each test-first with its own
  commit and changelog entry; then the Easy mediated tests, a small interleaved batch runner,
  and the runs.
- **What to look at:** Task 7's red/green dry-run, and the step-one table before Base is fixed.

## Global constraints

`AGENTS.md`'s working rules, plus R.1's own: a unit names no suite file, route or expected value.

## Review focus

- Two red settle gates in one session: both messages reach the model, in load order.
- A settle check that hangs (an import that starts a server) ends within its timeout, along with
  its whole process group.
- A `.py` write outside the workspace, or a non-`.py` write: the compile check leaves it alone.
- A mediated test edited or deleted in the workspace: the next check still runs the frozen copy.
- A batch killed partway through: the runner resumes without repeating a finished session.

## Task 1: Records

- [x] This plan; R.1 Status `active` and `## Now` pointing here in `ROADMAP.md`. Docs caps pass.
      Commit: `docs: open R.1`.

## Task 2: The settle fix

`extensions/mellum-quality.ts`, `mellum-guards.ts`, `mellum-verify.ts`; tests in the matching
`tests/*.test.mjs`. `CHANGELOG` Fixed.

- [x] Test `two red settle gates both reach the model`: a fake Pi that runs the handlers the way
      `emitBoundary` does (`runner.js:759`: each sees `event.entries` and replaces them), with
      quality and verify both red. Expect two entries, quality's first. It fails today.
- [x] Each handler returns `[...(event.entries ?? []), own]`.
- [x] `runBounded(cmd: string, args: string[], opts: {cwd, env, timeoutMs}) -> {code: number |
      null, out: string, timedOut: boolean, started: boolean}` in a new `extensions/bounded.ts`:
      `spawn` with `detached: true`, and on timeout `process.kill(-pid, "SIGKILL")`. Quality's ruff
      call and verify's pytest call use it (ruff 60 s, pytest 150 s). A timeout is red, with "timed
      out after N s"; `started: false` returns `undefined`. Tests: a `sleep 30` child with a 1 s
      timeout ends red within 3 s and leaves no child behind; a missing binary returns `undefined`.

## Task 3: Once-per-task injection and `name-the-layout`

Port `remedies/task-prompt.ts` and `extensions/mellum-task.ts` from lc40, with `f6d511e0`'s
`remedies/prompt/name-the-layout.ts` and its tests. `CHANGELOG` Changed: the line is shown once
per task, not on every user message.

- [x] Bring lc40's tests over first; see them fail on `integration`'s unit; port; see them pass.

## Task 4: `tool/bounded-commands`

Port `a1480516`, `60810b39` and the 120 s cap (`2f9e89a8`): the unit and
`tests/remedy-bounded-commands.test.mjs`. `CHANGELOG` Added.

## Task 5: `guard/foreground-log-follow`

Port `logFollowGuard` (`c9ee0b04`, `81f659ce`) into `mellum-guards.ts`, with the unit and its
tests; leave the overnight script behind. `CHANGELOG` Added.

## Task 6: `check/mediated-test` and its wiring

Port `e42712af` (the unit, `tests/remedy-mediated-test.test.mjs`) and `c9b7312f`
(`mediated_tests(suite, prompt_number) -> list[Path]` and the `MELLUM_MEDIATED_TEST` env in
`run_suite`, `fake-pi-mediated.sh`, its tests). Its settle entry appends, as in Task 2, and its
pytest uses `runBounded`. `CHANGELOG` Added.

## Task 7: Easy's mediated tests

`learn/code/suites/easy/mediated/test_01_<topic>.py`, written from `base/specs/` only (the grader
is read afterwards, to check coverage, never copied).

- [x] Test in `learn/code/tests/test_suites_single_source.py`: each of the 13 hidden checks in
      `grader/_easy_acceptance.py` names the mediated test that covers it (a mapping in the test
      file); the mediated tests pass `fixtures/known-good` and fail `fixtures/known-broken`.
- [x] A red witness: a copy of `known-good` with one spec reading broken (the title override)
      fails the mediated test.

## Task 8: `check/compile-import`

`remedies/check/compile-import.ts`, `tests/remedy-compile-import.test.mjs`. `CHANGELOG` Added.

- [x] Signatures: `moduleName(rel: string) -> string | null` (`pkg/mod.py` → `pkg.mod`; `null`
      outside the workspace or not `.py`); `compileCheck(file, cwd) -> string | null` (the error
      text, via `runBounded("uv", ["run","--offline","python","-m","py_compile",file])`, 30 s);
      `importCheck(modules, cwd) -> {module, error}[]` (one `python -c` per module, cwd on
      `PYTHONPATH`, 60 s, a timeout reported as that module's error).
- [x] Tests: a `write` with a `SyntaxError` → `isError: true` and the compiler's text appended; a
      valid `.py`, a `.md`, and a `.py` outside the workspace → unchanged; at settle a module that
      raises `ImportError` → one appended entry and `continue: true`, at most 3 times; a module
      whose import sleeps → red within the timeout; uv missing → no entry.

## Task 9: The batch runner

`scripts/r1_batch.py`, `learn/code/tests/test_r1_batch.py`.

- [x] `plan_sessions(arms: dict[str, list[str]], n: int) -> list[tuple[int, str]]`, round-robin
      `(round, arm)`; `run` calls the real `harness.py run --suite easy --grade --stall 180
      --host-card CARD --runs-dir DIR/<arm>-r<k>` per session and skips a session whose `run.json`
      exists; `report` writes `table.md` per arm: n, mean checks passed (`checks_ran − failed`), full
      passes, stalled, censored, budget endings, and median requests and output tokens over the
      sessions that are neither stalled nor censored.
- [x] Tests: interleaving order; resume skips finished sessions; `report` on hand-made `run.json`s
      leaves stalled and censored sessions out of the medians.

## Ladder run

Per the [preregistration](../../research/2026-11-07-r1-preregistration.md), on the M5 Max, b12110 on
:8001, Pi 1.4.0, thinking on, runs under `~/mellum-runs/r1/`, `watch_ladder` on screen first.

- [x] Card: `uv run python learn/code/conformance.py --out ~/mellum-runs/r1/host-card.json`;
      fill the preregistration's grader sha256s, execution policy and card; commit before Screen 1.
- [x] Screen 1 (n = 3 × 5 arms, about 26 min), a lead; the screen filter decides step one's arms.
- [x] Step one (n = 12 per arm), `report`; apply the rule; write `remedies/presets/base.json`.
- [x] Screen 2 and step two (n = 12 per arm), `report`; the rule; step three (n = 24) wrote `presets/easy.json`.
- [x] Records in `evals/2026-11-07-r1-*/` (raw stripped) and a research note; [ ] the raw release waits on Paul.

## Persuasion → enforcement

Settle entries are appended, and checks are killed with their process group: a red gate reaches
the model, and a hung check ends. `tool_result` turns a `SyntaxError` into a failed write.
`tool_call` bounds every bash call. The mediated test is a frozen copy run outside the project.
Only `name-the-layout` is prompt text, and it is measured as that.

## Close

Per [Branches and worktrees](../../../sdd.md#branches-and-worktrees):

- [x] Glossary entries; `learn/pathologies.md` entries for new failure shapes (21, 22).
- [x] R.1 Status, `## Now`, `## Result`, archived; `[Unreleased]` reconciled against
      `git log fcfc772..HEAD`; docs caps, `npm test`, ladder suite pass.
- [x] Squash-merge into `integration` (trees checked equal), never switching the main checkout; remove the
      worktree and branch with the owning tool. Push nothing without asking.

## Result

No unit beat Vanilla within budget: `preset:base` and `preset:easy` are `[]` ([note](../../research/2026-11-07-r1-easy-remedies.md)).
