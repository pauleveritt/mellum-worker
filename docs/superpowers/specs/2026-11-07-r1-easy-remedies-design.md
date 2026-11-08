# R.1: Easy remedies, Base earned first

Status: approved 2026-11-07 (Paul).

## For Andre

- **What changes:** the settle layer is fixed. Base (`preset:base`) and `preset:easy` are built
  from measurement on Easy's 13 current checks; neither is carried over from the old worker.
  One new unit, `check/compile-import`. Four units port from `lc40-thin-worker`, each test-first.
- **Why:** remedies were about to be measured on a floor with no fix for the stall that ended 2 of
  3 Easy screens. Paul's call was to earn a minimal Base first, so later units get a fair chance.
  Every number still traces to plain Vanilla, which runs in every batch.
- **Calls made here:** a screen at n = 3 before each counted batch, the decision rule below, and
  rebuilding `preset:easy` in R.1. All three are Paul's, from 2026-11-07.
- **What to look at:** the decision rule, and the Easy mediated tests (written from the spec, not
  from the grader).

## Behaviour

1. **Settle fix.** Every `agent_before_settle` handler in `extensions/` and `remedies/` returns
   `[...event.entries, ownEntry]`. Pi 1.4.0 hands each handler the earlier handlers' entries and
   keeps whatever the last handler returns (`runner.js:759`), so today a second red gate erases
   the first one's message. Each settle check's subprocess runs under a timeout that kills its
   whole process group. Checks call `uv run --offline`. A timeout while the model's code runs (an
   import or a test) is red; a check that cannot start is ours, and never blocks settle.
2. **`check/compile-import`** (new). On `tool_result` for a successful `write` or `edit` of a
   `.py` file inside the workspace, the unit compiles that file. On a `SyntaxError` it marks the
   result `isError` and appends the compiler's message. At settle, it imports each module the
   session wrote, with the workspace on the import path, under the timeout above, and sends any
   failures back, at most a fixed number of times. It keys on the file extension and the model's
   own writes, and names no suite file.
3. **Ported test-first from lc40:**
   - `tool/bounded-commands` (`a1480516`, `60810b39`): a 30 s bash timeout when the model gives
     none, and a cap of 120 s on one it chooses.
   - `guard/foreground-log-follow`, with its guard in `mellum-guards.ts` (`c9ee0b04`, `81f659ce`).
   - `check/mediated-test` and its harness wiring (`e42712af`, `c9b7312f`), with
     `remedies/task-prompt.ts` and `extensions/mellum-task.ts`, which show the test once per task.
   - `prompt/name-the-layout` as lc40 has it, injected once per task (`f6d511e0`), the version the
     n = 6 lead measured; `integration` appends it to every user message. `guard/foreground-server`
     is already on `integration`, with Andre's `f0e31ea`.
4. **Easy mediated tests** under `learn/code/suites/easy/mediated/`, written from
   `base/specs/`. They are a superset of the 13 hidden checks. In a dry run they pass the
   `known-good` fixture and fail `known-broken` and a build with a spec reading missed. No grader
   value is copied in.
5. **Presets.** `remedies/presets/base.json` holds step one's winners (empty if none win), and
   `easy.json` becomes `preset:base` plus step two's winners. Both are rewritten only from
   recorded results.

## Ladder run

Harness, Easy, M5 Max, llama.cpp b12110 on :8001, `--pi-binary ~/.local/bin/pi`, thinking on,
`--host-card`, runs outside the repo, `watch_ladder` on screen. Each tier's `budget.json`
applies. Arms are interleaved round-robin.

- **Step one:** Screen 1 (n = 3, a lead), then a counted batch (n = 12): Vanilla against the
  thin worker plus each candidate from item 3.
- **Step two:** Screen 2, then a counted batch: Vanilla, Base, and Base plus each step-two unit.

The [preregistration](../research/2026-11-07-r1-preregistration.md) carries the arms, the screen
filter, grader identity, the execution policy and the full decision rule (Paul, 2026-11-07):
- A stall handler wins when it at least halves Vanilla's stalled-or-censored sessions (Vanilla
  needs at least 2 of 12), costs at most 1 check on average, and keeps median requests and output
  tokens (stalled and censored sessions left out) within 20% of Vanilla's.
- A quality unit wins with at least 1 check more on average, or 3 more full passes, under the
  same budget limit.

## Persuasion → enforcement

- **Settle (`agent_before_settle`):** with appended entries and group-killed timeouts, a red gate
  is guaranteed to reach the model, and a hung check can no longer hang the session.
- **`tool_result`:** a `SyntaxError` comes back as a failed write in the very next request; the
  model is not asked to remember to compile.
- **`tool_call`:** `bounded-commands` rewrites the bash input, so a foreground command returns
  control no matter what the prompt says.
- **The mediated test:** a frozen copy run outside the project. The model cannot weaken it.
- `prompt/name-the-layout` is the one persuasion candidate. No hook can see the reading of a
  layout, so it is measured as prompt text and labelled that way.

## Non-goals and anti-goals

- No Medium or Hard runs; no pods (F.6); no architect mode (A.1); no change to the model,
  sampling or oracle.
- A unit that names a suite file, route or expected value is void as evidence.
- A screen is never stated as a rate. Ladder-rig numbers (thinking off) are never mixed in.

## Left to the builder

The timeout values (each below the 180 s stall cutoff), the compile/import re-dispatch count,
the interpreter the compile check calls (it must be the workspace's), and how the mediated tests
are split across files.

## Risks

- Vanilla on b12110 may stall rarely. Then no stall handler can win and Base is
  `name-the-layout` or Vanilla. That is a valid result.
- An import gate may push the model to delete code to make an import pass. The step-two screen
  watches for it.
