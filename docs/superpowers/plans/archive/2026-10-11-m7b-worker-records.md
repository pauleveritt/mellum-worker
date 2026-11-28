---
phase: M.7B
cycle: 1
lifecycle: closed
---

# M.7B Worker Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pi Worker runs (the pi-subagents child) write one schema-2 `kind: "worker"` record per finished run, so `/mellum learn` and `scripts/mellum.mjs learn` cover them.

**Architecture:** Mode's record code moves, unchanged, to `extensions/mellum-record.ts`. `extensions/mellum-guards.ts` (loaded only in the Mellum child) adds observers on `context`, `turn_end` and `agent_settled` and appends a record built with the shared `runRecord`. Its guard decisions are untouched. Replay tests rebuild child sessions from archived A10 traces; no model call.

**Tech Stack:** TypeScript under Pi 1.0.2 (`node --test`), Python 3.14 ladder (uv, pytest).

**Spec:** `docs/superpowers/specs/2026-10-11-m7b-worker-records-design.md`

## Global Constraints

- No change to any guard decision, the agent templates, `prompts/`, tools, sampling, or the filter. Listener return values are identical with recording on and off.
- Record file: `MELLUM_WORKER_RUNS` if set (`"0"` → no recording), else `~/.pi/agent/mellum-worker-runs.jsonl`. Record fields: `kind: "worker"`, `activation: "worker"`, `facts: null`, plus every schema-2 field `runRecord` writes; `server` from the 1,000 ms settings check (server-only keys).
- Recording never throws into Pi; on error, one stderr line `mellum-guards: run record not written: <reason>`.
- Never run `pi`, `/mellum` or anything that calls a model. Server contact is limited to read-only GETs, and only Task 6 makes any; Task 6 runs only if Paul says the GPU is free, and it is not part of this plan's required work.
- Never write to `~/.pi/agent` or ac-demo. Run node by its real binary; never with HOME set to an empty temp dir (a Volta shim loop spawned about 9,000 processes once); a 30 s limit on any command that changes HOME.
- `CHANGELOG.md` `[Unreleased]` entry in the same commit as each user-facing change; doc caps hold; every new assertion seen failing first. Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `m7b-worker-records` in a worktree off `main`; no push, tag, release, version bump or merge.

## Review Focus

1. **Guards loaded outside a Mellum child** (the ladder's direct mode loads them with `-e`; a user might too). They still record, so the ladder must isolate the path (Task 4), and the record is still well-formed when there is no system prompt (Task 2 test: no system message → `promptVersion` "unknown").
2. **A child that never sends `context`** before `turn_end` (an older Pi, or a different event order). The recorder writes from the turns it saw, never throws, and writes nothing when it saw no user message (Task 2 test).
3. **A nudge continuation that settles twice.** One line, holding the final state (Task 2 test).
4. **A run with no tool calls at all** (Mellum only replies). One line with `commands: []`, `files: []` and `lastCommand: "none"` (Task 2 test).
5. **Concurrent children appending to one file** (pi-subagents can run tasks in parallel). Each record is a single `appendFileSync` of one line ending in `\n`, so lines never interleave; a test writes two records from two recorder instances to one file and reads two parsable lines (Task 2 test).

---

### Task 1: Move the record code to a shared module

**Files:**
- Create: `extensions/mellum-record.ts`
- Modify: `extensions/mellum-mode.ts`, `extensions/mellum-learn.ts` (imports), `extensions/mellum-check.ts` (add `ServerCheck` and `serverCheck`)
- Test: existing `tests/mellum-mode*.test.mjs`, `tests/mellum-learn.test.mjs`, `tests/mellum-check.test.mjs`; new `tests/mellum-record.test.mjs`

**Interfaces:**
- Produces (moved verbatim from `mellum-mode.ts`, re-exported from it so existing imports keep working): `Msg`, `SpanStats`, `spanStats(span: Msg[]): SpanStats`, `RecordMeta`, `RunRecord`, `runRecord(task: string, span: Msg[], meta: RecordMeta): RunRecord`, `promptVersionOf(prompt: string): string`, `PACKAGE_VERSION`. `RecordMeta` gains `kind?: "mode" | "worker"`; `activation` accepts `"worker"`; `facts` accepts `null`. `runRecord` writes `kind: meta.kind ?? "mode"`.
- Produces in `mellum-check.ts`: `export interface ServerCheck { match: boolean | null; diffs: Diff[] }` (moved from `mellum-mode.ts`) and `export async function serverCheck(adminBase: string, opts: { timeoutMs: number; fetch?: typeof fetch }): Promise<ServerCheck>`, the GET-and-`settingsDiffs` logic Mode's activation runs today (moved; Mode calls it).
- Produces in `mellum-learn.ts`: `export function workerRunsFile(env, home): string | undefined` (`MELLUM_WORKER_RUNS`; `"0"` → undefined; default `<home>/.pi/agent/mellum-worker-runs.jsonl`); `recordFiles` uses it.

- [ ] **Step 1: Write failing tests** in `tests/mellum-record.test.mjs`: `runRecord` with `kind: "worker"`, `activation: "worker"`, `facts: null` writes those values; without `kind` it writes `"mode"`. In `tests/mellum-learn.test.mjs`: `workerRunsFile({MELLUM_WORKER_RUNS:"0"}, h)` is undefined, a set path wins, the default is under `h`; `recordFiles` with `MELLUM_WORKER_RUNS=0` omits the Worker file. In `tests/mellum-check.test.mjs`: `serverCheck` with an injected fetch returning the match fixture → `{match:true, diffs:[]}`, the drift fixture → `match:false`, a rejected fetch → `{match:null, diffs:[]}`.
- [ ] **Step 2:** Run `npm test`; the new tests fail (missing exports). Record in Progress.
- [ ] **Step 3:** Move the code; Mode imports from the new modules and re-exports the moved names. No logic change beyond `kind` and the widened types.
- [ ] **Step 4:** `npm test` green, with every pre-existing Mode, learn and check test passing unchanged. Commit `refactor(record): share the record code between Mode and the Worker` (no CHANGELOG entry: nothing user-facing).

### Task 2: The recorder in the guards extension

**Files:**
- Modify: `extensions/mellum-guards.ts`, `tests/mellum-guards.test.mjs`, `CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1's `runRecord`, `promptVersionOf`, `workerRunsFile`, `serverCheck`, `adminBaseOf` and `DEFAULT_BASE_URL` (from `mellum-check.ts`).
- Produces: `export function createRecorder(opts: { env: Record<string, string | undefined>; home: string; cwd: () => string; now: () => number; append: (file: string, line: string) => void; check: () => Promise<ServerCheck>; warn: (msg: string) => void }): { context(event): void; turnEnd(event): void; nudged(): void; blocked(): void; settled(ctx): Promise<void> }`. The default export wires it next to the guard set: `context` → `recorder.context`; `turn_end` → both; a non-undefined `beforeSettle` decision → `recorder.nudged()`; a `block` decision → `recorder.blocked()`; `agent_settled` → `recorder.settled(ctx)`. Listener return values are exactly those of today's guard set.

- [ ] **Step 1: Write failing tests** (a fake Pi with an `on` that records listeners, a temp file for `MELLUM_WORKER_RUNS`, the real node binary): the full sequence (system + brief `context`; a `bash` turn with a failing result, an `edit` turn, a `write` turn, a passing `bash`, an empty final turn that the nudge continues, a final text turn; `agent_settled`) → exactly one parsable line with `kind:"worker"`, `activation:"worker"`, `task` = the brief, `requests`, `files`, `edits`, `commands` with `mutates`, `lastCommand:"ok"`, `finalTurn`, `nudges:1`, `facts:null`, `promptVersion` from the system message; `agent_settled` twice → one line, final state (Review Focus 3); a run with no tool calls → `commands:[]`, `lastCommand:"none"` (Review Focus 4); no system message → `promptVersion:"unknown"`, and turns without any `context` → still one line, while a run with no user message at all writes nothing (Review Focus 1 and 2); `MELLUM_WORKER_RUNS=0` → no file; an `append` that throws → one `warn` call with the prefix and no throw; two recorder instances settling into one file → two parsable lines (Review Focus 5); the same sequence through the default export with recording on and with `MELLUM_WORKER_RUNS=0` → identical return values from every listener.
- [ ] **Step 2:** Run; fail. Record in Progress.
- [ ] **Step 3:** Implement. The task is the first `user` message's text; the span is every message after it; the record line is `JSON.stringify(record) + "\n"` in one `append` call. The settings check starts on the first `context` (or first `turn_end` if no `context` arrives) and `settled` awaits it with the check's own 1,000 ms limit.
- [ ] **Step 4:** `npm test` green. CHANGELOG "Added": Pi Worker runs now write run records to `~/.pi/agent/mellum-worker-runs.jsonl` (`MELLUM_WORKER_RUNS` sets the path, `0` turns it off), which `/mellum learn` reads. Commit `feat(worker): the guards extension records each Worker run`.

### Task 3: Replay real Worker runs

**Files:**
- Create: `tests/fixtures/worker/a10-rung{1,3,5}-r1.trace.jsonl`, `tests/fixtures/worker/a10-rung{1,3,5}-r1.final.md`, `tests/mellum-guards-replay.test.mjs`, `tests/fixtures/worker/README.md`
- Modify: `tests/mellum-cli.test.mjs`

**Interfaces:**
- Consumes: Task 2's `createRecorder` and the default export.

- [ ] **Step 1: Fixtures.** Extract `ablation-a10-delegated-v5.tar.gz` from `/Users/pauleveritt/projects/pauleveritt/mellum-worker-raw-research-2026-10-09/` into a temp dir. For rungs 1, 3 and 5, run r1, keep only `provider_request` (each payload's `messages`, `model`, `max_tokens`), `tool_call` and `tool_result` lines, and replace any absolute path under `/Users/` or `/private/` with `/home/user/...`. Copy `final.md` from `evals/2026-10-09-ablation-a10-delegated-v5/<run>/final.md`. The README says where they came from and how they were trimmed.
- [ ] **Step 2: Write failing tests.** A converter in the test turns the first request's messages into one `context` event (OpenAI-format messages mapped to Pi `Msg` shape: `role`, `content` as text parts, assistant `tool_calls` as tool-call parts, `tool` messages as tool results), each later request's new messages into `turn_end` events, and `final.md` into a last assistant text turn, then `agent_settled`. Feed the default export (with `MELLUM_WORKER_RUNS` at a temp file) and assert per fixture: one line; `requests` equals the number of `provider_request` lines; one `commands` entry per `bash` `tool_call`; `files` equals the sorted set of `write` and `edit` paths in the `tool_call` inputs; `finalReply` starts with `final.md`'s first line. In `tests/mellum-cli.test.mjs`: `scripts/mellum.mjs learn --file <the three replayed records> --json` with `cwd` set to the records' cwd reports `runs: 3`.
- [ ] **Step 3:** Run; fail (no fixtures, no converter). Record in Progress.
- [ ] **Step 4:** Make them pass. If a replay shows the recorder miscounts (for example, requests), fix the recorder and say so in Progress; never adjust the fixture to fit.
- [ ] **Step 5:** `npm test` green. Commit `test(worker): replay three real A10 Worker runs through the recorder` (no CHANGELOG entry).

### Task 4: Keep the ladder's runs out of the operator's log

**Files:**
- Modify: `ladder/ladder/run_ladder.py` (`child_env`), `ladder/tests/test_runner.py`

- [ ] **Step 1: Write the failing test:** for direct, delegated and mode runs, the env passed to the child has `MELLUM_WORKER_RUNS` under that run's scratch directory (call `child_env(...)` and `mode_env(...)` as the runner does, with a `tmp_path` scratch).
- [ ] **Step 2:** `cd ladder && uv run python -m pytest -q -m "not slow"`; it fails. Record in Progress.
- [ ] **Step 3:** `child_env` sets `env["MELLUM_WORKER_RUNS"] = str(Path(trace).parent / "mellum-worker-runs.jsonl")` (the trace sits in the run's scratch dir); `mode_env` inherits it through `child_env`.
- [ ] **Step 4:** Green. Commit `fix(ladder): keep Worker run records under scratch` (no CHANGELOG entry: ladder internals).

### Task 5: Docs, roadmap, changelog

**Files:**
- Modify: `README.md` ("Learn from your runs"), `tests/docs.test.mjs`, `skills/mellum-setup/reference/05-worker-pi.md`, `docs/recipe.md` (records section), `ROADMAP.md`, `CHANGELOG.md`, this plan

- [ ] **Step 1: Failing doc test first:** the README test that looks for "M.7B" changes to require `MELLUM_WORKER_RUNS` and "OpenCode" with "M.3" in the Learn paragraph. Run; it fails.
- [ ] **Step 2: Docs.** README: Pi Worker runs are recorded and `learn` reports them with Mode's; `MELLUM_WORKER_RUNS` next to `MELLUM_MODE_RUNS`; OpenCode runs join with M.3; keep the README's terse style. Setup phase 5: one sentence. Recipe: both record files, and that a Worker record has `facts: null` and `activation: "worker"`.
- [ ] **Step 3: Roadmap.** M.7B Status: what shipped, the replay results, "ships in v0.1.6"; the M.3 row's Ships cell adds "records OpenCode Worker runs (moved from M.7B), built against observed runs"; `## Now`. Caps hold.
- [ ] **Step 4:** CHANGELOG checkpoint against `git log v0.1.5..HEAD --oneline`. `npm test` and ladder pytest (not slow) green. Progress filled per task. Commit `docs: M.7B — Worker records in the README, recipe and setup skill; roadmap`. Leave `lifecycle: active` for Paul's merge.

### Task 6 (optional; only when Paul says the GPU is free): one live delegated run

- [ ] From `ladder/`: `uv run python -m ladder.run_ladder --mode delegated --profile baseline --rung 1 --repeat 1 --deadline 600 --out <scratchpad>/m7b-live < /dev/null`. Confirm the scratch `mellum-worker-runs.jsonl` has one line with `kind:"worker"`, the run's cwd, and requests matching the trace; record it in Progress. Do not commit the output.

## Progress

(Executors append here: task, failing-first evidence, commands and results.)

**Task 1** (record code moved to `extensions/mellum-record.ts`). Failing first: `npm test` with the new tests in `tests/mellum-record.test.mjs`, `tests/mellum-learn.test.mjs` (`workerRunsFile`) and `tests/mellum-check.test.mjs` (`serverCheck`) failed on missing exports (`mellum-record.ts` not found; no `serverCheck`, no `workerRunsFile`): 190 pass, 3 files fail. After the move: `npm test` 273 pass, 0 fail (268 before plus 5 new tests); every Mode, learn and check test unchanged. `runRecord` writes `kind` (default `"mode"`), and `facts: null` when given null (omitted when undefined, so Mode's records are unchanged).

**Task 2** (the recorder in `extensions/mellum-guards.ts`). Failing first: `node --test tests/mellum-guards.test.mjs` with the 10 new recorder tests added: 21 tests, 11 pass, 10 fail (`createRecorder is not a function`; `handlers.context is not a function` for the default-export test). After implementing: the same command, 21 pass, 0 fail; `npm test` 283 pass, 0 fail (273 before plus 10 new). Rulings applied: promptVersion from the first system message, else `ctx.getSystemPrompt()` at settle; one line per run (dedupe key task plus last message); recording off starts no server check; every default-export install in the test file sets `MELLUM_WORKER_RUNS` and a rejecting fetch. The default export's listener return values match with recording on and off.

**Task 3** (replay three real A10 Worker runs). Failing first: `node --test tests/mellum-guards-replay.test.mjs` with no converter and no fixtures: the module import fails (1 file fail); with the converter but no fixtures: 3 tests, 0 pass, 3 fail (`ENOENT` on the trace). `tests/mellum-cli.test.mjs` without the converter: import fails, 1 test fail. After: replay file 3 pass; cli file 15 pass (30 s limit, 1.6 s). Fixtures are trimmed A10 rung 1/3/5 r1 traces plus `final.md` (`tests/fixtures/worker/`, sizes in the README). Replay results, recorded vs expected from the trace, all matched, so the recorder needed no change: rung 1: requests 9 vs 9, commands 2 vs 2 (`npm test` failed then passed), files `calculator.js` vs `calculator.js`; rung 3: requests 14 vs 14, commands 1 vs 1, files `report.py`, `rows.py` vs the same; rung 5: requests 16 vs 16, commands 2 vs 2, files `export.py`, `render.py`, `totals.py` vs the same. `learn --json --file` over the three records reports `runs: 3`, 0 old and 0 bad lines. The replay then found a recorder defect, fixed in review round 1: `promptVersionOf` read only the first line, but a Worker child's system message carries `<!-- mellum-worker prompt v5 -->` after the pi-subagents preamble, so real Worker records said "unknown". It now matches the marker at the start of any line (first match); failing first: the replay tests (3) and a new `mellum-record` unit test expected "v5" and got "unknown" (4 fail); after, all green. The `learn` test also asserts `kind: "worker"` through `readRecords`.

**Task 4** (the ladder's child env keeps Worker run records under scratch). Failing first: `cd ladder && uv run python -m pytest -q -m "not slow"` with the new `test_worker_run_records_stay_under_each_runs_scratch` (direct, delegated and mode envs built as the runner builds them; the parent carries an operator `MELLUM_WORKER_RUNS=/operator/runs.jsonl`): 1 failed, 122 passed, 25 deselected; the assertion showed the operator path passing straight through (`PosixPath('/operator/runs.jsonl')`). After `child_env` sets `MELLUM_WORKER_RUNS` to `Path(trace).parent / "mellum-worker-runs.jsonl"` (`mode_env` inherits it through `child_env`): the targeted test 1 passed; `uv run python -m pytest -q -m "not slow"` 123 passed, 25 deselected; `npm test` 288 pass, 0 fail. No CHANGELOG entry (ladder internals).

**Task 5** (docs, roadmap, changelog). Failing first: `node --test tests/docs.test.mjs` with the two README Learn assertions changed (require `MELLUM_WORKER_RUNS`; Pi Worker writes records, OpenCode runs join with M.3, no "M.7B"): 2 fail (`says where Worker records live`, `says Pi Worker writes records`). After the README, recipe §4c, setup phase 5, ROADMAP (M.7B Status 586 characters, Ships 169, Excludes 56; M.3 Ships 117) and CHANGELOG edits: `npm test` and `cd ladder && uv run python -m pytest -q -m "not slow"` green (288 pass, 0 fail; 123 passed, 25 deselected). The plan stays `lifecycle: active` for the merge; the M.7B ROADMAP row, the README's Future work bullet and `## Now` are updated.

**Final review fixes.** (1) Recorder: the first `context` holding a user message is the baseline and later `context` lists are ignored (a compacted child loses the brief); failing first: a compaction test wrote no file; after, green (`252436b`). (2) `workerRunsFile` shares `modeRunsFile`'s rule (empty is off, leading `~` is HOME); failing first: the new asserts got the default path; CHANGELOG, README and recipe say "`0` or empty" (`c40dd96`). (3) Fixture README says `final.md` is the parent's report. (4) ROADMAP M.7B Status opens "built ... awaits merge". (5) BACKLOG entry: the recorder never resets after a settle. Final: `npm test` and the ladder pytest, counts in the sdd report.

## Result

2026-10-11. Merged to `main`; shipped in v0.1.6. The guards extension writes
one schema-2 `kind: "worker"` record per finished Pi Worker run to
`MELLUM_WORKER_RUNS` (default `~/.pi/agent/mellum-worker-runs.jsonl`), read
by `/mellum learn`; the record code is shared with Mode in
`extensions/mellum-record.ts`; the ladder keeps Worker records under
scratch. Three A10 Worker runs replayed with no model call matched their
traces (requests 9/14/16, commands 2/1/2, files 1/2/3) and exposed a
prompt-version defect, fixed. R9 (brief fixed at the first context, turns
accumulated, so compaction keeps the brief) kept by Paul. The live
delegated run (Task 6) was not run. Suites at merge: `npm test` 289, ladder
pytest (not slow) 123.
