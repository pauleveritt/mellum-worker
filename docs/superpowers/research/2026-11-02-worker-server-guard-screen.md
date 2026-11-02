# Screen: does the foreground-server guard help the worker? (2026-11-02)

## What is measured / what is conjecture

**Measured (this screen):** the Easy challenge suite run on the real local model,
the worker with its default guards versus the worker with the foreground-server
guard added, n = 3 each. **Conjecture:** anything about Medium/Hard, other hosts,
or the shipped default — this is a lead, not a ship decision.

## Why

A bare `/challenge easy` on the worker can launch `python app.py` / uvicorn in
the foreground; the call never returns and the session burns to the stall or the
deadline (pathologies.md entry 8, "a server nobody can stop"). The worker ships
with that guard **dormant** — it trades retries for safety and no run had
measured it as a net win. The question: does adding it to the worker improve the
Easy outcome enough to justify changing a frozen setting?

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

## Result

_(pending — filled in after both arms run)_

## What would falsify this / risks

- n = 3 on one tier on one local host is thin; variance can dominate (the same
  Easy task has passed bare and hung bare). A lead here is not evidence to ship.
- The guard can cost retries: treatment may pass yet run more turns, which the
  turn count will show.
- Easy may not exercise the hang enough; a null here does not clear Medium/Hard.
