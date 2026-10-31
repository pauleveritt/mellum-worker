# LoRA completeness-probe dataset

Preregistration: [`docs/superpowers/research/2026-10-27-lora-completeness-probe.md`](../../../docs/superpowers/research/2026-10-27-lora-completeness-probe.md).

This directory builds the adapter dataset for the LoRA completeness probe —
independent multi-requirement coding tasks that teach the worker to emit
**every** stated requirement, not just the salient one.

## The agnostic rule (load-bearing)

The dataset must share **no** domain literals with the hard suite or its grader
— no routes, tables, columns, index names, migration names, or exact strings
from the AgentClinic complaints app. The same *stack* (FastAPI, Jinja2, SQLite,
Starlette `TestClient`) is shared on purpose — that is not leakage, that is the
target environment. Only the task's own domain must differ.

`guard.py` enforces this: it rejects any task file that contains a banned
hard-suite literal. Every task passes the guard before it enters the set.

## Layout

```
lora/
  guard.py            # independence guard — bans hard-suite domain literals
  verify.py           # runs a task's checks against its reference (no ghosts)
  export.py           # verified task -> chat-format training example (jsonl)
  tasks/<name>/
    task.md           # the spec the model is trained to satisfy
    meta.json         # {domain, requirements:[...], shapes:[...]}
    reference/        # a working app that satisfies EVERY requirement
    checks.py         # per-requirement checker (pytest + TestClient)
```

## The shapes we over-represent

The requirements the model drops now, baked into every task:

- a second endpoint of a pair (not just the first);
- an exact status code (e.g. a 303 redirect, not 306/307);
- a database migration that is written **and** applied **and** tracked **and**
  idempotent on re-run;
- an exact JSON response shape with integer sums.

## Pipeline

1. Author a task (`task.md` + `reference/` + `checks.py` + `meta.json`).
2. `uv run python learn/code/lora/guard.py <task-dir>` — independence.
3. `uv run python learn/code/lora/verify.py <task-dir>` — every requirement
   passes against the reference (no ghost references).
4. `uv run python learn/code/lora/export.py` — emit `dataset.jsonl`.

A task enters the set only after steps 2 and 3 pass.
