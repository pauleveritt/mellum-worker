# Run a task in Pi where the primary delegates to a local worker

> **2026-11-07: the `delegate` tool and its nudge are no longer registered by default.**
> Loading `mellum-worker.ts` adds neither (spec
> [worker-without-delegate](superpowers/specs/2026-11-07-worker-without-delegate-design.md)).
> The code is kept and `/mellum <task>` still runs the architect path, but the "type the task and
> the primary delegates" flow below needs an opt-in unit that is not built yet.

The primary explores and decides; the worker implements. Load one extension and
the primary can hand bounded, test-driven briefs to a fresh local worker by
itself — you type the task, it delegates, it verifies, it reports.

## One-time: the model server

The worker and the primary both run on the same local model server (one slot;
the primary is paused on the tool call while the worker runs, so the slot is
free). Start it:

```bash
cd /Users/mac/projects/mellum-worker
uv run scripts/backend.py start      # Mellum on :8001 (llama-server)
```

Check it is up: `uv run scripts/backend.py health`.

## Launch Pi as the delegating primary

From the project you want the code to land in:

```bash
PI_CODING_AGENT_DIR=/Users/mac/projects/mellum-worker/learn/code/profile \
pi --provider llamacpp --model Mellum2.1-12B-A2.5B-Thinking --no-skills \
   -e /Users/mac/projects/mellum-worker/extensions/mellum-worker.ts
```

`PI_CODING_AGENT_DIR` points Pi at the profile that defines the `llamacpp`
provider (base URL `:8001`). `-e …/mellum-worker.ts` loads the worker, which
registers the `delegate` tool on the primary.

## Run a task

Type what you want built and how you will know it is done. The primary writes
the failing test, calls `delegate` with a brief, reads the worker's report, and
runs the test to verify. For example:

> Add a `/health` route to this FastAPI app that returns `{"status": "ok"}`.
> The test command is `uv run --frozen python -m pytest tests`.

You do not type `/mellum`. The nudge in the extension keeps the primary on the
division of labour — it decides the layout and the test, the worker writes the
code. Any generic brief works: the tool names no suite, file or command.

## How it is wired

- `delegate` spawns this same extension headless: `pi -p --no-approve
  --no-skills --no-prompt-templates --no-themes -e <mellum-worker.ts> "/mellum
  <brief>"`. `--no-approve` is essential — without it the worker's write/edit
  calls block waiting for approval and the run returns nothing.
- The spawned child runs with `MELLUM_WORKER_CHILD=1`, so it gets neither the
  `delegate` tool nor the nudge. The worker cannot delegate to itself.
- The worker bundles nothing: no prompt swap, no remedies. It implements the
  brief with the plain seven tools and returns its report (the last 4,000
  characters of its headless output).

`scripts/delegate.sh <workspace> "<brief>"` runs the same bridge from a shell
without Pi, for scripted checks.

## The open question — do we still need remedies?

This is a theory under test, not a settled result. The hypothesis: when the
primary does the exploration, the decision and the failing test, the *bare*
worker (no remedy preset) implements a generic brief well enough that the
remedy stack is no longer load-bearing. A remedy exists to fix a gap a lone
worker leaves; a complete brief from a thinking primary may close the same gap.

Measure it the standard way before claiming it — a preregistered ladder run,
bare worker vs. a preset, scored on the hidden grader, recorded in `evals/`.
Until that run, the delegation mechanism is proven; "we no longer need
remedies" is a lead.
