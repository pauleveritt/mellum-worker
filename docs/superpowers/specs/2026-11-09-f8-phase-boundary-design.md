# F.8 — A verified, bounded phase boundary

## For Andre

**Date:** 2026-11-09. **Cycle:** F.8, infrastructure, cut from `integration` at `3875af59`. **Why:** the
[review](../research/2026-11-09-phase-worker-review.md) found that a session can end, or a run can move
on, with nothing having verified the work. **Result sought:** one requested phase either ends with a
trusted accepted checkpoint or says exactly why not, each guarantee shown failing first on deterministic
tests. **No model run, no preset change, no rate or savings claim.** Default runs keep their behaviour
apart from the gate fixes below, and recorded scores stay as they are.

### Goals

1. **Gate verdicts** (`remedies/mediated-test.ts`). Each settle check ends in one of `green`, `red`,
   `exhausted` or `infrastructure`, appended to a log the harness names (`MELLUM_GATE_LOG`, read at load
   and removed from the environment). `red` sends the model back. `infrastructure` (the command could not
   start, no report, exit 3, 4 or 5, or an incomplete inventory) gets one silent retry, costs no send-back,
   never reaches the model, then lets settle proceed as unverified. A timeout stays `red`. Once the cap is
   used, the gate still runs a final check, so a last repair is verified; it records `green` or `exhausted`.
2. **Green means proven.** A small pytest plugin, written beside the frozen copy, streams each outcome to a
   report. `green` needs exit 0, a finished report and a pass for every `test_*` function found in the
   frozen source. Exit 0 alone is never green. Dependencies come from `pyproject.toml` and `uv.lock` frozen
   at load, in their own `mellum-gate-envs/<digest>` (never shared with the grader's env, because a session
   user owns it). The run strips `PYTEST*`, `PYTHON*`, `UV_*` and `VIRTUAL_ENV`, disables plugin autoload
   and ignores workspace conftest and config. With no `pyproject.toml` it falls back to `VERIFY_PYTEST` and
   records that. This is not an OS sandbox: the boundary below is the trusted verdict.
3. **Feedback.** From the report: every failing test's name and its assertion message, capped per failure
   and overall, with no captured server output. A collection error shows its message. A timeout says the
   run was stopped, after how long, and which test was running.
4. **Handover.** Mediated tests always go through `hand_over`, including local runs, so no suite path is
   exported. The directory belongs to the session's user. `loadMediated` reads the files once, deletes them
   and the directory, removes `MELLUM_MEDIATED_TEST` from `process.env`, and caches the result on
   `globalThis` so the show and settle halves can both load. The harness still removes the directory at
   the end. This closes the observed route (a path in the shell environment plus readable copies), not
   every route: the suite remains on disk for a session that searches for it.
5. **Supplied tests.** New explicit unit `guard/supplied-tests`, in no preset. `MELLUM_SUPPLIED_TESTS`
   names files relative to the project; bytes are read at load and the variable removed. `tool_call`
   refuses `write` and `edit` on them. After **every** tool result, any file changed, deleted or replaced
   by a symlink is restored and the result says so and suggests a separate test file. Other paths,
   including new tests, are untouched. The harness sets the list from `_prepared_tests` when the unit is
   loaded and restores those bytes before each prompt. Whatever slips past shows up as `integrity_ok:
   false` and rejects the phase.
6. **Command bound.** `MELLUM_BOUND_SECONDS` is clamped to 120. A chosen timeout that is not a positive
   finite number takes the default.
7. **Phase runs.** `harness run --suite S --phase N [--from-checkpoint DIR]` sends only prompt N. Prompts
   come from `prompts/NN.md`, else the new `phase-prompts/NN.md`; Easy's 02–04 go there so its default run
   stays one prompt. `phase_scope` keeps grader modules and expected nodes for phases up to N (works for
   any `test_phaseN_` suite). `grader_identity` records the phase; unscoped digests do not change. Mediated
   tests are cumulative up to N, taken from the selected bundle's `mediated/` by filename over the suite's,
   in phase mode only. `--phase` with `--single-prompt` is refused.
8. **The boundary.** After a phase run, on any ending, the harness runs trusted acceptance on the stopped
   snapshot and writes `boundary` into `run.json`: phase, ending, last gate verdict, hidden, project, lint,
   contamination and mediated results, `accepted`, reasons. **Paul's decision: `accepted` needs a strict pass
   and the mediated tests up to N.** Strict is the [count rule](../research/2026-11-08-easy-count-rule.md):
   hidden checks up to N, project tests and the lint gate (`--phase` forces grading), with no contamination
   or record failure. Mediated tests run through `evaluate`'s trusted path, every function required, and
   are recorded apart from strict. A stopped snapshot that passes this is accepted; an exit message is not.
9. **Checkpoints.** Accepted only. `_application` copies the snapshot with the trusted config;
   `flow_run.git_init_workspace` and `git_checkpoint` commit it; `checkpoint.json` holds suite, phase,
   grader identity, file digests and the verdict. `--from-checkpoint` refuses, before any session or token,
   on a wrong suite, a phase other than N−1, changed files, or a failed re-run of acceptance up to N−1.
   Seeding copies the tree without `.git`. `harness checkpoint --workspace DIR --suite S --phase N --grader G
   --out DIR` makes one from a saved build, with no model; with no trace beside it, contamination is
   recorded `not_checked`.
10. **Advancing.** In a multi-prompt run with a settle gate armed, a prompt whose last verdict is not
    `green` stops the run (`termination_reason: unverified_exit`, reported as its own completion). A run
    with no gate is unchanged.

11. **Handover to Andre, 2026-11-10.** Each guarantee is one commit, and `remedies/` imports nothing from
    `learn/code`, so he can take or refuse each on its own. The atomic branch outlives the squash until he
    answers. `research/2026-11-09-handover-to-andre.md` gives him each finding, its evidence, the code and
    what refusing costs, with unit checks kept apart from measured results.

### Non-goals and anti-goals

No phase sequencing or retries (R.2), architect mode, new default remedy or preset. No change to the
prompt, sampling or budgets. The two hidden-grader false failures stay in the backlog: they reopen on
Phase 3 or later, and R.1a is Phase 2. `mellum-verify.ts`'s own gate is unchanged. A unit naming a suite
file, route or expected value is void.
**No Docker** (Paul, 2026-11-09): the cleanup tests reach Linux on `ubuntu-latest` CI when this branch is
pushed, which is Paul's call; until then the roadmap and research note say Linux was not exercised.

**Left to the builder:** Report format, message caps, helper names, and where boundary code sits (`learn/code/phase_boundary.py`
preferred). Node stand-ins for pytest write the report protocol; each suite side has a real pytest test.

## Ladder run

None in this cycle: deterministic tests decide, each shown failing first, on fake Pi sessions and real
builds through the trusted path. Easy `base-r02` (`~/mellum-runs/f6/easy-final-count/`, not committed) becomes
the Phase-1 checkpoint offline; r02–r04 already pass hidden, project and all 16 mediated checks through
`evaluate`. If it is rejected, use the next strict build; if every one fails a mediated check, stop and raise
it, because R.1a then has no seed. R.1a is the next inference, started only when Paul asks.

## Persuasion → enforcement

`tool_call`: the bash bound and the supplied-test refusal. `tool_result`: restoration, on every route.
`agent_before_settle`: the gate and its verdict. Everything else is outside Pi and does not depend on the
model: the budget proxy stops generation, the harness grades the snapshot, and only trusted green makes a
checkpoint. Failure feedback changes, reporting facts; no instruction is added.
