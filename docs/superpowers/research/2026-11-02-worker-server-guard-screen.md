# Screen: does the foreground-server guard help the worker? (2026-11-02)

## What is measured / what is conjecture

**Measured (this screen):** the Easy challenge suite run on the real local model,
the worker with its default guards versus the worker with the foreground-server
guard added, n = 3 each. **Conjecture:** anything about Medium/Hard, other hosts,
or the shipped default — this is a lead, not a ship decision.

## Why (premise — later found wrong; see Result)

The screen was set up on the belief that the worker ships **without** the
foreground-server guard, so that adding it would be a measurable change. That
belief was wrong: `extensions/mellum-guards.ts:57` has `blockForegroundServer:
true` in the worker's default `ENABLED` set. The guard is already in the Baseline
Worker. The correction and what to measure instead are in the Result.

## Arms (only delta: the server guard)

- **control** — `--arm worker`: `MELLUM_MODE=1`, guards `{emptyFinalNudge:3,
  loopBreaker:true}`.
- **treatment** — `--arm server-guard`: the same, plus `blockForegroundServer:true`.

## Design

- Suite: `easy`. n = 3 per arm. `--grade`. Deadline 600 s; stall as configured.
- Model: `Mellum2.1-12B-A2.5B-Thinking`, Q4_K_M on llama-server at `127.0.0.1:8001`.
- Command: `uv run python learn/code/harness.py run --suite easy --arm <arm>
  --grade --repeat 3 --runs-dir runs/server-guard-screen/<arm>`.

## Scoring and the rule

- Primary: pass rate (x/3).
- Secondary: turns and wall per rep; count of reps ended by stall or deadline
  (the hang the guard answers).
- **Rule (screen, not a decision):** if treatment ≥ control on pass rate **and**
  cuts hang-terminations without a large turn penalty, it is a lead to add the
  guard — then a preregistered ladder run before the worker default changes. If
  it is no better, or worse, leave the guard dormant and opt-in via `/remedy`.

## Result (2026-11-02 — screen abandoned, premise wrong)

**The Baseline Worker already includes the foreground-server guard.**
`extensions/mellum-guards.ts:57` sets `ENABLED = { emptyFinalNudge: 3,
loopBreaker: true, blockForegroundServer: true, confineToWorkspace: true }`.
There is nothing to add.

**The two arms were not a clean add.** `MELLUM_GUARDS` *replaces* `ENABLED`
(`mellum-guards.ts:272`), and the `server-guard` arm's
`{emptyFinalNudge, loopBreaker, blockForegroundServer}` omits `confineToWorkspace`.
So both control (`worker`) and treatment (`server-guard`) already had the server
guard; the only delta was that the treatment **lost** the workspace guard. The
screen would have measured removing `confineToWorkspace`, not adding a server
guard.

**The control ran before the error was caught** (`worker`, Easy, n=3): 2/3
passed — rep1 pass 53t/300s, rep2 pass 64t/486s, rep3 fail 31t/592s. The rep3
failure was **not** a foreground-server hang: its `run.json` has `guard_blocks:
0`; it simply did not produce a passing home page before the deadline. The
treatment arm was stopped.

**What to measure instead**, to answer the real open question ("does
`blockForegroundServer` earn its place in the worker?", since it already ships):
ablate it *out* — control `worker` (ENABLED, guard on) vs a worker with
`MELLUM_GUARDS={emptyFinalNudge:3, loopBreaker:true, confineToWorkspace:true}`
(worker minus only the server guard), one variable held clean. A dedicated
`no-server` arm would make that a one-flag run.

## What would falsify this / risks

- n = 3 on one tier on one local host is thin; variance can dominate (the same
  Easy task has passed bare and hung bare). A lead here is not evidence to ship.
- The guard can cost retries: treatment may pass yet run more turns, which the
  turn count will show.
- Easy may not exercise the hang enough; a null here does not clear Medium/Hard.
