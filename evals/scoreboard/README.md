# Scoreboard entries

Every measured run lands here as **one small JSON file** — `entries/<run-id>.json`. One file
per run is the whole trick: two pull requests that each add a run touch different files, so
they never conflict. Nothing appends to a shared log, and nobody hand-edits a combined table.

The published board (`learn/scoreboard.md`) is **generated** from these files, never written by
hand. It carries all of them — a Records section (the fastest pass per configuration and
version, because a shorter run is the better pass) and an All-runs section with turns and
wall-clock for every run.

## Add a run

```bash
# after a harness run lands in runs/<...>/<rep>/
uv run python learn/code/scoreboard.py record runs/<...>/<rep> --model <model-id>
```

That writes `entries/<rep>.json`. Commit **only that file** in your pull request. `--model` is
only needed for a run whose `run.json` predates the model field; new runs carry it.

Do not run `consolidate` in your pull request — the generated page is rebuilt after the merge
(see below), so leaving it out of the diff is what keeps pull requests from colliding on it.

## After a merge (maintainer / CI)

```bash
uv run python learn/code/scoreboard.py consolidate   # rebuilds learn/scoreboard.md from every entry
```

One pass over all the entry files consolidates the scores and republishes the page. A git hook
or CI step can run it on every push to the default branch.

## What an entry holds

`id`, `date`, `suite`, `model`, `arm`, `stack` (the remedy units and `mellum-*` extensions it
used), `version` (a stable hash of the extensions' `sha256`, so an edited extension is a new
version that can *beat* the old one rather than blend into it), `passed`, `turns`, `tool_calls`,
`wall`, `missing`, `machine`. The raw trace, stdout and workspace never come here — only the
scored summary.
