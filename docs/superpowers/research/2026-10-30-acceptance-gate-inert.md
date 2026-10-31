# The acceptance gate was inert — easy remedy screens, 2026-10-30

## What is measured / What is conjecture

**Measured.** On the local M3 (Metal, cached Q4, `llama-server`, same rig as the
2026-10-30 vanilla baselines), easy n=3, bare arm plus remedy stacks:

| stack | pass | note |
|---|---|---|
| bare | 1/3 | home-phase miss + one quality trip |
| + quality | 1/3 | quality trips gone (all `quality_ok=true`); home miss dominates |
| + acceptance + ncm + quality + nonblock (+ cap120) | 1/3 | **same** home miss; gate never fired |

The last stack is the important one. The two fails missed the four Phase-1 home
checks (`tests=False`, `missing=4`) at only 17 and 20 turns — too few for a
redispatch loop. The trace confirms it: `[mellum-ncm]` appears **0 times**, one
`agent_settled`, no redispatch. The worker wrote `main.py` six times and never
`app.py` (the spec says *"`app.py` holds the FastAPI application as `app`"*), so
the app could not be imported — a wrong-module-name miss the acceptance contract
is meant to catch.

**Root cause (measured).** `mellum-ncm` read its `NCM_TEST` config **once at
extension-load**, inside the default export body — before `mellum-acceptance`'s
`session_start` handler set `NCM_TEST`. Extensions initialise before any
`session_start` fires, so `ncm` captured an empty `NCM_TEST`, its settle guard
`(test === "" && !all)` stayed true, and the gate was silently off for the whole
session. A second, downstream fault: even once it runs, `ncm` invoked pytest with
`cwd` but no `PYTHONPATH`, so a held-out contract in the sibling `../contract/`
dir hit `ModuleNotFoundError: app` at collection (the harness grader already
solves this via `grade_env` → `PYTHONPATH=workspace`; `ncm` did not reuse it).

**Fix (unit-tested, not yet measured on the suite).**
- `ncm` reads config at settle time (`gateConfig()`), not at load — so
  acceptance's late `NCM_TEST` is seen.
- `ncm` runs the verify with `verifyEnv(cwd)` — `PYTHONPATH=cwd`, `VIRTUAL_ENV`
  stripped — mirroring `grade_env`, so the contract imports the worker's app.
- Separately, `mellum-contract` was renamed `mellum-acceptance` and extended to
  derive page-HTML checks (doctype, `lang`, nav, a spec-quoted tagline) for GET
  routes the spec calls pages — all from `readSpec()`, never the grader. Proven
  by mutation on the suite's fixtures: green on `known-good` (8 pass), red on
  `known-broken` (2 page tests fail on missing `lang=en`).

**Conjecture.** That with the gate now firing, acceptance + ncm will lift easy
above 1/3 by catching the home-miss / wrong-module and redispatching until the
contract is green. Unmeasured — the re-run is the next step. `cap-turns(120)`
bounded the edit-churn thrash (reps terminated ≤21 turns), but that is an
efficiency observation at small n, not a pass-rate claim.

## What would falsify this / Risks

- **Re-run still 1/3 with the gate firing.** If `[mellum-ncm]` now appears but
  pass rate does not move, the redispatch *message* is too opaque for a small
  model to act on (e.g. it cannot infer "rename `main.py` to `app.py`" from a
  traceback) — a different remedy problem, not a wiring one.
- **Proxy, not parser.** The page checks are regexes over `response.text`, not a
  DOM parse; a false pass (a `lang=` in a comment) or a false fail is possible.
  The hidden grader stays the oracle — the contract is only the redispatch gate.
- **Module-name assumption.** The contract derives `app.py`/`app` from the spec;
  a worker using another name is correctly rejected, but a spec that names a
  different module must be parsed for it, or the gate false-fails.
- **No smoke test that the gate fires.** This whole class hid because nothing
  asserted `ncm` actually redispatches end-to-end. A cheap smoke run (a build
  known to miss a check must produce a `[mellum-ncm]` redispatch) would catch a
  future regression; owed as follow-up.
