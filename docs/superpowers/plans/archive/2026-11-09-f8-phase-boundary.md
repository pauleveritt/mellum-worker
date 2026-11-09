---
phase: F
feature_cycle: F.8
cycle: 8
lifecycle: closed
---

# F.8 — A verified, bounded phase boundary: implementation plan

> **For agentic workers:** use superpowers:subagent-driven-development or superpowers:executing-plans, task by task.

**Goal:** one requested phase ends in a trusted accepted checkpoint, or says exactly why not.
**Architecture:** portable Pi-side units in `remedies/` (no import from `learn/code`); harness-side acceptance in a new `learn/code/phase_boundary.py`.
**Tech stack:** Node 24 + Pi hooks; Python 3.14 + pytest under `uv`. **Spec:** [design](../../specs/2026-11-09-f8-phase-boundary-design.md).

## For Andre

**What changes:** nine guarantees, each one commit you can take or refuse: Tasks 1–5 are small Pi-side changes; Tasks 6–9 need our trusted grading path. **What to look at:** Task 2's definition of green and Task 8's acceptance rule. The [handover report](../../research/2026-11-09-handover-to-andre.md) lists what each costs you to refuse.

## Global constraints

- No model or GPU run. No preset, prompt, sampling or budget change. No Docker. No push without Paul.
- Every test seen failing before its code. Each task is **one commit**, explicit paths only, ending with the attribution line; a user-visible change adds its `[Unreleased]` entry in that commit.
- Nothing names a suite file, route or expected value in `remedies/`. Default (no `--phase`) runs and unscoped grader digests stay as they are, except where the spec says.
- Tests run where Paul can see them (Terminal panel). Node: `node --test tests/<file>`. Python: `uv run python -m pytest learn/code/tests/<file> -v`.

## Review focus (each has a test in its owning task)

- A parametrized or class-based acceptance test counts by its base function (Task 2).
- A session killed mid-write leaves a truncated last line in the gate log: read as unverified, no crash (Task 7).
- `.venv` and `__pycache__` in a build never reach a checkpoint, and the digest is stable across re-verification (Task 8).
- A supplied test replaced by a directory of the same name is restored (Task 5).
- The show and settle halves loaded as two units both receive the handed tests (Task 4).

## Tasks

Every task: write the named tests → run, see them fail → implement → run, see them pass → commit.

### Task 1: clamp the bound — `remedies/tool/bounded-commands.ts`, `tests/remedy-bounded-commands.test.mjs`
`boundSeconds()` returns `Math.min(value, MAX_TIMEOUT_SECONDS)`. A chosen timeout that is not a finite number above 0 takes the bound. Tests: `MELLUM_BOUND_SECONDS=300 installs 120`; `a chosen timeout of 0, -1, NaN or "600" takes the default`. `meta.does` states the clamp.

### Task 2: green means proven — create `remedies/gate-run.ts`, test `tests/remedy-gate-run.test.mjs`
**Produces:**
```ts
export type Frozen = { name: string; source: string };
export type FrozenProject = { pyproject: string; lock: string | null };
export type GateRun = { status: "green" | "red" | "infrastructure"; failures: { test: string; message: string }[];
  missing: string[]; detail: string; timedOutSeconds?: number; running?: string; execution: "frozen" | "workspace" };
export function expectedTests(files: Frozen[]): string[];            // `def test_*`, including inside classes
export function freezeProject(cwd: string): FrozenProject | null;    // bytes read now; null with no pyproject.toml
export function runGate(dir: string, files: Frozen[], project: FrozenProject | null, cwd: string, timeoutMs?: number): GateRun;
```
`runGate` writes the frozen files and a plugin `_mellum_gate_report.py` into `dir`. The plugin appends JSON lines to `$MELLUM_GATE_REPORT`: `{event:"collected",tests}`, `{event:"start",test}`, `{event:"outcome",test,when,outcome,message}` (message is `longrepr.reprcrash.message`), `{event:"collect_error",message}`, `{event:"finished",exit}`.
Command: `uv --no-config run --offline [--frozen] --project <dir>/env --no-editable python -m pytest <dir> -q -p _mellum_gate_report -p no:cacheprovider -c <dir>/pytest.ini --rootdir <dir> --confcutdir <dir> --noconftest --import-mode=importlib`; `UV_PROJECT_ENVIRONMENT=<tmpdir>/mellum-gate-envs/<sha256 of config>`; `PYTHONPATH=<cwd>:<dir>`; strips `PYTEST*`, `PYTHON*` (then sets the above), `UV_*`, `VIRTUAL_ENV`, `CONDA_PREFIX`; sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. With `VERIFY_PYTEST` set or no project, uses that pytest command and `execution: "workspace"`.
Classification, in order: timeout → `red`; could not start or exit 127 → `infrastructure`; no report → `infrastructure`; any failed outcome or collect error → `red`; `finished` exit 0 with every expected function passed → `green`; anything else (exit 3/4/5, a skip, a short inventory) → `infrastructure`.
Tests: `exit 0 with no report is not green`; `exit 0 missing one expected function is infrastructure`; `a failing outcome is red and keeps its assertion, not the server log`; `a hang is red, names the test that was running and its seconds`; `parametrized and class tests count by base function`; `a workspace pyproject edited after load changes nothing` and `a real pytest run under uv is green on a passing project` (real `uv sync` first so `--offline` works on CI).

### Task 3: verdicts at settle — `remedies/mediated-test.ts`, `tests/remedy-mediated-test.test.mjs`, `tests/settle-entries.test.mjs`
**Consumes:** Task 2. `settleMediated` freezes the project at load. Each settle: stop session processes, run, and on `infrastructure` run once more without telling the model. Then: `green` → settle; `infrastructure` → settle; `red` with sends left → send back; `red` at the cap → settle as `exhausted`. The final check always runs. Appends `{at, status, used, failures: [names], detail, execution}` to the path in `MELLUM_GATE_LOG` (read at load, removed from `process.env`; a write failure never blocks settle). Feedback: every failing name, then each message capped at 400 characters for the first 6, total at most 1,500, location stripped by `withoutLocation`; a timeout says it was stopped, after how long and which test was running. Stand-ins in existing tests move to the report protocol.
Tests: `the last repair after the cap is still checked and can be green`; `a red at the cap records exhausted`; `an infrastructure failure retries once, never reaches the model, costs no send-back`; `a caught launch error records infrastructure`; `feedback keeps assertions and drops captured server output`; `the gate log path is not left in the environment`.

### Task 4: close the handover — `remedies/mediated-test.ts`, `learn/code/harness.py:hand_over`, `run_suite`; both test suites
`hand_over(files, place, owner=None)`: directory 0o700, owned by `owner` when given. `run_suite` always hands over and sets `MELLUM_MEDIATED_HANDED=1`. With that flag `loadMediated` reads, removes the files and directory, deletes both variables and caches on `globalThis[Symbol.for("mellum.mediated")]`, so a second half gets the same files. Without the flag it never deletes. Tests: node `handed tests are gone and the path is out of the environment before any tool runs`; `a user's own named test is never deleted`; `show and settle loaded separately both get the files`. Python `a local run exports no suite path`; `no handed copy survives a run`.

### Task 5: supplied tests — create `remedies/guard/supplied-tests.ts`; harness wiring; `tests/remedy-supplied-tests.test.mjs`, `learn/code/tests/test_harness.py`
`MELLUM_SUPPLIED_TESTS`: relative paths, joined by the delimiter; bytes read at load, variable removed; unset installs nothing. `tool_call` blocks `write`/`edit` resolving to one. `tool_result` after every tool compares by `lstat` and bytes, restores (removing a symlink or directory in the way) and appends a note naming the file and suggesting a separate test file. Harness: `supplied-tests.ts` in extras sets the list from `grading._prepared_tests` and restores those bytes before each prompt. Tests, one per route: `edit`, `write`, `sed -i`, `rm`, `mv`, symlink, a directory in its place; `a new test file is left alone`; `an unchanged file adds no note`. Listed in the generated remedies list, in no preset.

### Task 6: phase scope and prompts — create `learn/code/phase_boundary.py`, `learn/code/suites/easy/phase-prompts/0{2,3,4}.md`; test `learn/code/tests/test_phase_boundary.py`
**Produces:** `Suite.phase: int | None = None`; `phase_scope(suite, n) -> Suite`; `phase_prompt(suite, n) -> str` (`prompts/NN.md`, else `phase-prompts/NN.md`, else `SystemExit`); `phase_mediated(suite, n) -> list[Path]` (bundle `mediated/` over suite `mediated/` by filename, numbers ≤ n). `evaluate` drops `test_phase{m}_*` for m > phase when copying the grader. `grader_identity` adds `phase`. New prompts follow `prompts/01.md`'s wording with each phase's title. Tests: `a Phase-1-only Easy build passes f7-roadmap at phase 1`, `and fails at phase 2`; `phase 1 of f7-roadmap keeps exactly the 13 checks`; `unscoped digests are unchanged`; `Easy's default still has one prompt`; `phase_mediated takes 01 from the suite and 02 from the bundle`.

### Task 7: the boundary — `phase_boundary.py`, `harness.py` (`--phase`, `--from-checkpoint`, `_run_sessions`); fixture suite `tests/fixtures/suites/phased`, fake Pi `fake-pi-build-then-spend.mjs`
**Produces:** `gate_verdicts(run) -> list[dict]` (skips an unparsable line); `mediated_result(workspace, suite, files) -> dict` via `evaluate(..., include_project=False)`, each `ast`-found function required; `decide(...) -> dict`, the `boundary` block. `--phase` forces grading; refused with `--single-prompt`. Tests: `a budget ending is graded on the stopped snapshot and can be accepted`; `green in session with a failing trusted grade is rejected`; `a passing hidden grade with a failing mediated test is rejected, recorded apart`; `lint failure rejects`; `contamination rejects`; `no gate log reads as unverified`; `a truncated gate log does not crash`.

### Task 8: verified checkpoints — `phase_boundary.py`, `harness.py` (`checkpoint` subcommand)
**Produces:** `write_checkpoint(workspace, suite, boundary, out) -> dict`, using `grading._application` then `flow_run.git_init_workspace`/`git_checkpoint`; `verify_checkpoint(path, suite, phase) -> dict` (`SystemExit` on wrong suite, wrong phase, changed files or failed acceptance); `seed(path, workspace)` (no `.git`). Tests: `only an accepted boundary makes a checkpoint`; `a changed file is refused before any session`; `phase other than N−1 is refused`; `the earlier phase is re-run and a regression refused`; `seeding carries no .git`; `checkpoint CLI records contamination not_checked without a trace`; `no .venv or cache in the tree, digest stable`. Then, offline, replay Easy `base-r02`; stop and raise per the spec if all strict builds fail.

### Task 9: no advance on an unverified exit — `harness.py` loop, `execution_outcome`
After each prompt with a settle unit armed, a last verdict other than `green` writes `termination_reason: unverified_exit` and breaks; `execution_outcome` reports it as its own completion. Tests: `a red exit stops before prompt 2`; `a green exit continues`; `a run with no gate is unchanged`.

### Task 10: close-out documents — see Close.

## Ladder run

None: deterministic tests decide. The only replay of a real build is Task 8's offline check of `base-r02`. R.1a is next, on Paul's word.

## Persuasion → enforcement

`tool_call` holds the bound and refusal, `tool_result` restores, `agent_before_settle` gives the verdict. Budget stops, grading and checkpoints are outside Pi and need no cooperation from the model. Only failure feedback text changes.

## Close

Research note (`2026-11-09-f8-phase-boundary.md`: each guarantee and its test; Linux not exercised unless CI ran; what R.1a now needs); the [handover report](../../research/2026-11-09-handover-to-andre.md) (per finding: evidence, code, cost of refusing; covers the re-boot; merge risks up front), also published as a private page for Paul to send. ROADMAP F.8 Status and `## Now`; BACKLOG for anything deferred; glossary entries (gate verdict, verified checkpoint, phase scope); pathologies only if evidence showed a new shape; `[Unreleased]` reconciled. `## Result`, archive this plan. Run `node --test tests/docs-caps.test.mjs`, `npm test` (about 31 min), ladder pytest, `uv run zensical build`. Fresh whole-branch review. The [squash into `integration`](../../../sdd.md#branches-and-worktrees) follows Paul's word, verified for tree equality; **the atomic branch and worktree stay until Andre answers** (Paul's handover, 2026-11-10), then go by the owning tool from a retained checkout.

## Result

2026-11-09. Shipped the nine guarantees as one commit each (`78158d9`..`6f2d123`), then three review fixes
(`53bc953`, `a22a693`, `1d30391`): the gate keeps uv's location variables and never builds the project;
a collection error keeps its last line; the root-run restore never follows a planted symlink. Measured:
deterministic tests only, each seen failing first, plus Easy `base-r02` accepted offline as a Phase-1
checkpoint (`ffced376`) that verifies for phase 2. No model or GPU run; Linux cleanup unexercised. Rulings
and deferred minors are in the [research note](../../research/2026-11-09-f8-phase-boundary.md#whole-branch-review).
