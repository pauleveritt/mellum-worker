# How This Project Works

`mellum-worker` ships Mellum 2.1 as a bounded coding worker for Pi
and keeps the ladder that measures it and the Learning Center that
teaches it. This section is for people working on the repository. Learners
start at [Getting started](../getting-started/index.md).

![A small robot in a tidy workshop with a pegboard of tools and a checklist](../assets/illustrations/project.webp){ .illustration }

## What ships

- **The Pi package**: `extensions/mellum-worker.ts` (the `/mellum` command and
  its guards), `skills/mellum-setup/` and the prompt under `prompts/`. The
  subagent worker, its templates and the intercom phases were retired in
  LC.8; `/mellum` and the run-record path stayed.
- **The harness**: `learn/code/harness.py` and the Bronze, Silver and Gold suites,
  the instrument the lessons measure with. `ladder/` reruns rungs 1–9
  internally and is no longer the lessons' instrument.

## Repo map

| Path | What it is |
| --- | --- |
| `extensions/` | Pi extension: `/mellum`, `/mellum check`, `/mellum learn`, `/mellum last`, the guards |
| `prompts/` | `mellum-worker.md`, the single source for the agent templates |
| `templates/` | Pi model fragments |
| `skills/` | The `mellum-setup` skill and its phases |
| `scripts/` | Command-line counterparts: `scripts/mellum.mjs` for the worker, `scripts/backend.py` for the local model |
| `ladder/` | The harness, fixtures and scoring that produce `evals/` |
| `learn/` | The Learning Center site (`zensical.toml`, `docs_dir = "learn"`) |
| `docs/` | SDD records, backend notes, the recipe, and the measured `ladder/` records |
| `tests/` | The Node suite that guards all of the above |

## Where the records live

- `evals/` holds one directory per phase or ablation, with its score
  and links; raw traces, stdout and patches stay out of Git and ship as
  `research-*` release assets.
- `docs/superpowers/specs/`, `plans/` and `research/` hold the SDD cycle. The
  roadmap and backlog sit at the repository root; the closed M series is
  archived in `ROADMAP-M.md`.
- The Learning Center's lessons cite those records through GitHub URLs, so
  the SDD documents stay unpublished while the site still links them.

## Read next

- [`README.md`](https://github.com/andrevanzuydam/mellum-worker/blob/main/README.md)
  for what ships and how to install it.
- [`AGENTS.md`](https://github.com/andrevanzuydam/mellum-worker/blob/main/AGENTS.md)
  for the working rules, including the ladder's and the changelog's.
- [`docs/sdd.md`](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/sdd.md)
  for the cycle and its document caps.
- [Toolchain and checks](toolchain.md) for the commands.
