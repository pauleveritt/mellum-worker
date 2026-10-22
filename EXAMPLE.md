# Using Mellum — by example

Mellum is a local 12B coding worker. You hand it **one bounded task with a test
command**; it reads the code, edits, and runs the test until it exits 0, then
hands the session back. Your main model stays in charge. See
[`README.md`](README.md) for the full reference; this file is just worked
examples.

## Before you start

Install the Pi CLI, then run the setup skill once:

```
/skill:mellum-setup
```

It walks weights → server → provider → agent → a smoke test, checking each step
and asking before it writes to your files. When it passes, `/mellum` is live.

## Example 1 — a one-shot bounded fix (Mellum Mode)

Type `/mellum <task>`. Name the test command in the task:

```
/mellum Fix totalCents in calculator.js so it multiplies each price by quantity. Test command: node --test calculator.test.js
```

Pi switches to Mellum, which lists files, reads `calculator.js` and the test,
edits the code, runs `node --test` until it exits 0, then switches back with a
handoff (files written, commands run, last output). **Run the test yourself
afterwards** — the handoff is a report, not proof.

Headless (one task, no UI): `pi -p "/mellum <task>"`.

## Example 2 — several tasks in one span

```
/mellum on
Add a balance() to ledger.py that sums the entries, with a test. Test command: uv run --offline python -m pytest -q
Rename fetch_rows to load_rows everywhere. Test command: uv run --offline python -m pytest -q
/mellum off
```

You get one handoff block per span instead of one per edit. Run `/mellum off`
before a long main-model turn (auto-compaction is refused while Mode is on).

## Example 3 — the reliable pattern: hand it a FAILING test

This is the recommended way to use Mellum, and the one this project is building
toward. **Don't rely on Mellum to decide it's done from a prose task** — give it
an executable oracle it cannot weaken:

1. You (or your main model) write a failing test from the spec — including the
   requirement that's easy to leave out.
2. Run it and confirm it is **red**.
3. Hand it over:
   ```
   /mellum Make tests/test_resolve.py pass. Test command: uv run --offline python -m pytest tests/test_resolve.py
   ```
4. Run the test again yourself after the run.

Why it matters: left to write its own tests, a worker can go green on a test
that misses part of the spec and report success anyway. An **external, complete**
test it can't edit is what makes the exit trustworthy. (This is the direction
being measured as phase M.11; see the "Driving the worker" note in
[`AGENTS.md`](AGENTS.md).)

## Example 4 — give the project its facts

Add a `## Mellum` section to your project's `AGENTS.md` (plain bullets, at most
600 characters). Mellum Mode appends it to every task it forwards:

```markdown
## Mellum
- Test command: uv run --offline python -m pytest tests
- Do not: add dependencies; add __init__.py/conftest.py/pytest.ini; weaken tests
```

With no test command named and a pytest `pyproject.toml`, Mellum falls back to
`uv run --offline python -m pytest -q`. `/mellum learn` reads your recent run
records and suggests `## Mellum` lines (written only on a yes).

## Example 5 — check and inspect

```
/mellum check   # compares the served model + provider against the measured profile
/mellum last    # prints the last run record (task, files, commands, final reply)
```

## Measuring Mellum (maintainers)

The ladder (`ladder/`) scores Mellum on fixed tasks. Against a plain
`mlx_lm.server` — no oMLX needed:

```bash
cd ladder
SERVED=$(curl -s http://127.0.0.1:11500/v1/models | python -c \
  "import sys,json;print(json.load(sys.stdin)['data'][0]['id'])")
uv run --offline python -m ladder.run_ladder \
  --mode direct --backend mlx-lm --base-url http://127.0.0.1:11500/v1 \
  --model-id "$SERVED" --profile tuned --rung 1 --out ../docs/ladder/example
```

See [`docs/backends/mlx-lm.md`](docs/backends/mlx-lm.md) for the recipe and the
gotchas (the model-id must match what the server serves).
