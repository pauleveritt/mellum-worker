# mellum-worker

*Apologies for the slop, I was in a hurry.* 

[JetBrains Mellum 2.1](https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking),
a 12B-A2.5B thinking model, as a local, bounded coding worker for
[Pi](https://pi.dev), with an [OpenCode](https://opencode.ai) port. It takes
a precise brief, edits code, runs the tests until they pass, and reports.
Your main model stays in charge.

- **Mellum Mode** (Pi): `/mellum <task>` runs Mellum inside your session
  with the worker prompt and seven file tools, then hands the session back.
  No extra packages. 15/15 on the ladder with project facts.
- **Mellum Worker**: a [pi-subagents](https://github.com/nicobailon/pi-subagents)
  child. Your model briefs it and runs the tests itself. 15/15. Retired
  once the mediated test below is measured ([M.12](ROADMAP.md#phases)).

Every setting was measured by the ladder (`ladder/`; records in
`docs/ladder/`). The 6-bit MLX weights (for Apple Silicon, served by oMLX)
are on [Hugging Face](https://huggingface.co/pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit).

## Domain engineering

You do domain engineering: specs and tests. Mellum does the bounded work:
edit code until the named test command exits 0. Everything this package adds
is a guardrail that holds that line: a 643-character prompt, seven file
tools, a nudge and a loop breaker, project facts from a `## Mellum` section,
a handoff and a run record you can read, and `learn` to turn records into
facts.

The next guardrail is the **mediated test**: your main model turns a request
or a spec phase into a failing test, shows it to you, confirms it fails, and
hands it to Mellum as "make this pass". Mellum's best measured shape is a
named failing test: rung 4, three files, 3/3 in every arm. Whether that
shape lifts the four-phase build (rungs 6–9, 9/12 with the `## Mellum`
section) is M.11's question and is unmeasured; the lead is phase 4, which
misses its automatic id in most runs because the spec's test line never asks
for it. You can do it by hand today:

```
/mellum Make tests/test_resolve.py pass. Test command: uv run python -m pytest tests
```

Write the test first, run it, and read the failure before you hand it over;
run it again afterwards. The reasoning is in the
[triage note](docs/superpowers/research/2026-10-13-roadmap-triage.md).

## Install

Pi:

```bash
pi install git:github.com/pauleveritt/mellum-worker@v0.1.8
```

Then `/skill:mellum-setup`: weights, oMLX server, provider entry, agent
file, optional rules, smoke test. It checks each step and asks before
writing to your files. Mode works once the model is served; Worker also
needs pi-subagents.

OpenCode, in the `plugin` array of `~/.config/opencode/opencode.json(c)`:

```json
{ "plugin": ["mellum-worker@git+https://github.com/pauleveritt/mellum-worker.git#v0.1.8"] }
```

Then ask "run the mellum-setup skill". The OpenCode port is ported and
unmeasured, and measuring it is a [backlog entry](BACKLOG.md), not a phase.

## Use it

**Mellum Mode (Pi).** Type `/mellum <task>`:

```
/mellum Add hello.py at the repo root with hello() returning "Hello, World!", and tests/test_hello.py that imports it. Test command: uv run --offline python -m pytest -q tests
```

Pi switches to Mellum, runs the task, and switches back. For several tasks,
`/mellum on`, type them as normal prompts, then `/mellum off`; your model
gets one handoff block per span (summary line, files written, commands run,
last output, Mellum's reply) instead of every edit. Run the tests yourself
afterwards. Run `/mellum off` before a long main-model turn: auto-compaction
is refused while Mode is on. `pi -p "/mellum <task>"` runs one task
headlessly.

Each span appends a JSON line to `~/.pi/agent/mellum-mode-runs.jsonl`
(task, times, requests, tokens, files, commands with pass or fail, final
reply; schema 2 adds missing files, file-changing commands, final-turn
shape, guard counts, host and versions, tool calls and errors, time to
first write; `server` records whether the oMLX settings matched).
`MELLUM_MODE_RUNS` sets the path; `0` turns it off.

**Project facts (Mode).** Mode sends Mellum only the worker prompt and
your task, never your conversation, skills or `AGENTS.md`, except one
section. Without the test command Mellum guesses one and bends the project
to fit ([What helped](#what-helped)). Add a `## Mellum` section to the
`AGENTS.md` where you start Pi:

```markdown
## Mellum

- Test command: uv run python -m pytest tests
- Do not: install packages or add dependencies; add __init__.py, conftest.py, pytest.ini or setup.cfg files; weaken tests
```

Both sections are measured. The one above passed 9/12 AgentClinic runs with
none writing outside the layout (A21), the same as A19's section, which
adds `- Write only: app.py, models.py, templates/, tests/`, rerun the same
day ([result](docs/superpowers/research/2026-10-13-a21-result.md)). Add a
`Write only:` line if you want a strict boundary.

Mode appends these bullets to every task as `Project facts:`. Bullets only,
600 characters at most; write the label exactly as `Test command:` in plain
text. Without the section, a pytest project gets `Test command: uv run
--offline python -m pytest -q`. `MELLUM_MODE_FACTS=0` turns both off; the
handoff and run record say which applied. `/skill:mellum-setup` phase 8
writes the section for you. Keep each bullet on one line: Mode drops
continuation lines and flattens nested bullets.

If your tests import a module from the project root, add `pythonpath =
["."]` under `[tool.pytest.ini_options]` in `pyproject.toml`; then bare
`pytest`, `uv run pytest` and `python -m pytest` all find it.

**Mellum as your main Pi model** gets none of this: no worker prompt, facts,
guards or run record (8/15 on the ladder). Use `/mellum` or the Worker. If
you do run it bare, start Pi from the project's environment (`uv run pi`, or
`source .venv/bin/activate` first) so `python` and `pytest` are on PATH, and
leave context files on so it sees `AGENTS.md`.

**Mellum Worker (Pi).** "Use mellum-worker to do this: the cart total
ignores quantity, fix it. Test command: node --test calculator.test.js."
If pi-subagents says the child "produced no output", dispatch it once more
(that recovered ten of eleven in sixty runs).

**OpenCode.** "Delegate to mellum-worker: …" with the same kind of brief.

**Right-sizing the task.** Mellum passes on fact sheets, not plans:

- Name the exact file or a literal string to grep for.
- Name the test command, in the task or the `## Mellum` section.
- One change per task; three files that change together is fine.
- Facts, not numbered steps: steps with "reply with…" stall (11/15).
- Do the exploration with your main model first, then hand over the result.
- Expect 11 to 14 requests and 25 to 120 seconds per task.

**Model settings.** The measured runs used these values:

| setting | value | set by |
| --- | --- | --- |
| model id | Mellum2.1-12B-A2.5B-Thinking-6bit | server |
| max_tokens | 16,384 | provider entry, per request |
| thinking | on | provider entry, per request |
| sampling | 1 / 0.95 / 20 | provider entry, per request |
| context window | 56,000 | server only |
| TurboQuant | off | server only |
| thinking budget | off | server only |
| tool-result cap | none | server only |
| concurrent requests | 1 | server only |
| hot cache | off | server only |

Pi sends the first three from its provider entry per request, and oMLX
honours them over the server's own values; OpenCode's template sets only
the output limit, so for OpenCode the server's thinking and sampling apply.
With `force_sampling` on in oMLX, the server's sampling wins over any
request, so `/mellum check` fails unless it is 1 / 0.95 / 20. The
server-only values bind every client, and other clients of the same oMLX
model can change them.

**Check your setup.** In Pi Mode, `/mellum check`. From the terminal,
`--host pi` checks the setup Pi Mode and Pi Worker share, and
`--host opencode` checks OpenCode's (`--json` for JSON):

```bash
node <package dir>/scripts/mellum.mjs check --host pi
node <package dir>/scripts/mellum.mjs check --host opencode
```

`<package dir>` is `~/.pi/agent/git/github.com/pauleveritt/mellum-worker`
(Pi) or `~/.cache/opencode/packages/*/node_modules/mellum-worker`
(OpenCode). It checks that the server answers and lists the model, that the
settings no request can undo match (the server-only rows above, thinking
not forced off, and forced sampling at 1 / 0.95 / 20), and that your
provider entry matches the template, `maxTokens` and sampling included; a
server value your requests override shows as info. Fails print first, and
the CLI exits 1 on any fail. It only reads: a settings fix prints as the
`PUT` to run yourself. Each `/mellum` activation also reads the settings no
request can undo (one second at most) and warns in one line on drift:

```
Mellum server settings differ: max_context_window 32768 (expected 56000). Run /mellum check.
```

**Learn from your runs.** In Pi Mode, `/mellum learn` (the last 10 runs)
or `/mellum learn 25`. It reads the run records for the current directory,
names what went wrong (a guessed test command, a bent project, success
claimed after a failed command, long runs, servers, settings drift), and
suggests the `## Mellum` lines your `AGENTS.md` lacks. Its output on the
test fixture `tests/fixtures/learn/patterns/bent-project.jsonl`:

```
mellum learn: 4 runs in /home/user/proj (2026-10-01 to 2026-10-04)

- Project bent to fit in 3 runs: conftest.py, pyproject.toml, src/__init__.py; uv add httpx

Suggested for AGENTS.md:

## Mellum
- Do not: install packages or add dependencies; add __init__.py, conftest.py, pytest.ini or setup.cfg files
```

It asks before adding those lines to `AGENTS.md` and never rewrites a line
you have: a different value prints as a conflict, missing `Do not:` values
go in a new bullet, and it never takes the section past 600 characters.
From the terminal, run it from the project directory; it only prints:

```bash
node <package dir>/scripts/mellum.mjs learn [--n 10] [--file <jsonl>] [--json]
```

Records come from `MELLUM_MODE_RUNS` (default
`~/.pi/agent/mellum-mode-runs.jsonl`) and `MELLUM_WORKER_RUNS` (default
`~/.pi/agent/mellum-worker-runs.jsonl`; `0` or empty turns it off); `--file` reads
one file instead. Pi Mode and Pi Worker write records, and `learn` reports
both. The OpenCode port writes no records and measuring it is on the
backlog, so `learn` in an OpenCode project finds 0 runs.

**See the last run.** `/mellum last` shows the newest run at or under the
current directory, Mode or Worker, as a table, with no model call. It goes into the
session, so you can follow up with a short question ("why the slow start?").
While Mode is on it is a notification instead, kept out of Mellum's context.
Abridged:

```
**mellum last**: Mode (one-shot), 2026-10-12 11:21, /home/user/ac-demo

| Metric | Value |
|---|---|
| Time | 62 s; first write at 31 s (50%) |
| Turns | 14; ended with text (stop) |
| Tool calls | 16: read 5, bash 4, write 4, ls 2, edit 1 |
| Commands | 1 run, 0 failed, last ok |
```

From the terminal it prints the same Markdown, or the record with `--json`:

```bash
node <package dir>/scripts/mellum.mjs last [--file <jsonl>] [--json]
```

Mellum as your main Pi model (no `/mellum`) writes no record, so `last` and
`learn` cannot see those runs.

## What you get

Rungs 1–5, five coding tasks, three runs each, on an M5 Max through oMLX
([summary](docs/ladder/ablation-summary.md)):

| Host | Deliverable | Use | Passes | Wall s, mean | Requests per run | Your main model per run |
| --- | --- | --- | --- | --- | --- | --- |
| Pi | Mellum Mode | `/mellum <task>` | 14/15 (15/15 with facts) | 70 | 13.1 | none |
| Pi | Mellum Worker | "Use mellum-worker to ..." | 15/15 | 54 | 11.1 | 6.5 turns, ~3k output and 120k mostly cached input tokens |
| OpenCode | Worker subagent | "Delegate to mellum-worker ..." | ported, unmeasured | | | |

Mellum as the primary agent: 8/15 in bare Pi (51 s), 10/15 in a full
Superpowers profile (72 s). Mode costs your main model nothing; Worker is
faster on multi-file tasks and keeps your session clean.

Rungs 6–9 build a small FastAPI app (AgentClinic) from four loose phase
specs. A run passes when the project's tests and hidden behaviour tests
pass, no existing test was removed or edited, and nothing was written
outside the file list. Mode, 12 runs each
([note](docs/superpowers/research/2026-10-09-m7-project-facts.md)): facts
off ([A18](docs/ladder/ablation-a18-agentclinic-facts-off/README.md)), a
`## Mellum` section ([A19](docs/ladder/ablation-a19-facts-on/README.md)),
and the fallback only
([A20](docs/ladder/ablation-a20-facts-fallback-only/README.md)). Passes,
requests, time and stray writes are in What helped, below; runs cut at the
600 s deadline were 3, 1 and 1 of 12.

A18 is rescored under the added-tests rule (0/12 strict). Time is the
runner's clock; output tokens are not in `run.json`. Mode and Worker
requests sent max_tokens 16,384 (verified in the A10, A17 and A19 traces);
direct-mode research phases used 4,096.

## What helped

One change made most of the difference: telling Mellum the project's test
command. On less-specified tasks Mellum guesses `pytest -q`, which cannot
import a root module from `tests/`, and then bends the project to fit
(`__init__.py`, `pytest.ini`, `uv add`) until it times out or leaves stray
files. The `## Mellum` section fixes that; without it, Mode's `python -m
pytest` fallback gets about three-quarters of the gain.

| AgentClinic, 12 runs each | no facts | fallback only | `## Mellum` section |
| --- | --- | --- | --- |
| passed | 1 | 7 | 9 |
| requests, median | 50 | 28 | 26 |
| seconds, median | 261 | 143 | 106 |
| wrote outside the layout | 8 | 5 | 0 |

Rungs 1–5 did not regress (15/15). Caveats: three runs per task, one
machine, one kind of project; the baseline is Mode without facts, since bare
Pi was not run on these rungs.

## Findings

- [recipe.md §6](docs/recipe.md#6-what-is-settled-and-what-is-not): what is settled and what is not.
- [recipe.md §4](docs/recipe.md#4-using-mellum-worker-delegated): recorded pathologies and the guard for each.
- [Ablation summary](docs/ladder/ablation-summary.md): every setting measured in and out.
- [Where the cost goes](docs/superpowers/research/2026-10-09-worker-cost-options.md): Mode versus Worker.
- [Recovery report](docs/superpowers/research/2026-10-07-mellum-recovery/report.md): why Mellum cannot be the primary agent.

## This session — 2026-10-18

Harness work toward M.11 (the mediated test). Everything here is a ladder
capability and a set of screens, **not** a shipped claim — the runs were on a
plain `mlx_lm.server`, not the measured oMLX backend, so the deciding comparison
is still owed (see the
[preregistration](docs/superpowers/research/2026-10-18-mediated-rungs-6-9-preregistration.md)).

Built in the ladder, test-first:

- **mlx-lm backend** — `--backend mlx-lm --base-url …`, `--model-id`, and
  `--temperature`/`--top-p` run the ladder against any OpenAI-compatible MLX
  server and sweep sampling ([docs/backends/mlx-lm.md](docs/backends/mlx-lm.md)).
- **Mediated-test exit gate** — `--acceptance-test` places and freezes an
  external, complete test; `--redispatch N` re-runs it and hands the failure to a
  fresh worker, including on a timed-out attempt. Retries grow the temperature
  (capped, since high temperature corrupts the worker's JSON tool calls) and move
  the seed; the retry message now carries the real test failure (warnings
  suppressed, short traceback) instead of a blind tail.
- **Effort ramp** — `--effort-ramp` starts quick (Pi thinking off, small token
  budget — sub-second on an easy fix) and escalates thinking and budget only as
  the frozen test keeps failing. "Small deadline slicing": a relay of short,
  fresh-context slices on one cumulative workspace, compute spent in proportion
  to measured difficulty.
- **Dev discipline** — a `mellum-dev` skill and CI that runs the node and ladder
  suites on every PR.

Findings (n = 1 screens, `mlx_lm.server`):

- Freezing the oracle cracked rung 9's long-standing wall: the Phase 4
  auto-`id` requirement that failed every prior run (A21 at 0/3) now passes,
  because an external frozen test forces what a self-authored test let slip.
- A remaining rung-9 failure was a worker framework-confusion bug (Flask route
  syntax in a FastAPI app), not a missed requirement — the tests check behavior,
  not framework.
- Mellum fixes that bug unaided *when it can think*; thinking-off is ~150×
  faster but too shallow for it, which is the whole point of the effort ramp.
- `preserve_thinking` is load-bearing for Qwen-family tool calls (stripping it
  degrades them to empty arguments), so prior reasoning stays; slicing, not
  stripping, is what bounds context.

## Requirements

- Apple Silicon Mac, [oMLX](https://github.com/jundot/omlx) 0.6.4 or newer, 9.9 GB for the weights
- Node 24 or newer; Pi 1.0 or newer (Worker also needs pi-subagents)
- OpenCode port: OpenCode 1.18 or newer (V1 plugin API); 2.x not yet

Other backends: [docs/backends/ollama.md](docs/backends/ollama.md) lists
what a port needs. Only oMLX has been run.

## How it works

A 643-character worker prompt, seven file tools, and in Pi two guards: a
nudge when a turn ends empty (at most three) and a loop breaker. The
prompt's default test commands are `uv run --offline pytest -q` (pytest
pyproject) and `node --test <file>` (package.json); a command in the brief
wins, and Mode supplies one from `## Mellum` or the fallback. Detail:
[docs/recipe.md](docs/recipe.md).

Nothing registers at load time. Pi loads Mode, dormant until `/mellum`;
OpenCode loads a one-hook plugin for the skill. The skill writes provider,
agent and rules into your config from [templates/](templates/). OpenCode
has no Mode or guards: Worker only, step-capped, unmeasured.

## Working on it — the 🍓 skill

Development here runs through the **`mellum-dev` skill**
([`.claude/skills/mellum-dev/SKILL.md`](.claude/skills/mellum-dev/SKILL.md)),
which operationalizes `AGENTS.md` and [`docs/sdd.md`](docs/sdd.md): spec-driven
development, test-first, fail-fast **and** fail-loud, frozen-oracle runs,
recording every run, running them where you can watch, and one small PR per win
or loss.

**Activate it.** In **Claude Code** it loads on its own — `CLAUDE.md` says to
always load and follow it when developing here, so any session in this repo
picks it up. You know it is active because replies open with the **🍓** marker
(and **💥 Bazinga!** on an *earned*, verified win). With **other agents**, point
them at the skill file and have them follow it; its authoritative sources are
`AGENTS.md` and `docs/sdd.md`.

**Why.** The measured claims here only hold if the process holds — tests shown
to fail first, settings frozen without evidence, every run recorded, failures
surfaced loudly instead of swallowed. The skill makes that the default rather
than something to remember, and the 🍓 marker is a visible promise that it is in
force.

## Layout

```
prompts/mellum-worker.md      the prompt, single source
extensions/                   Mellum Mode and the child guards (Pi)
opencode/plugin.js            skills-path hook (OpenCode)
skills/mellum-setup/          the guided installer
templates/                    agent files and provider fragments, per host
scripts/                      merge-json, render-agent (the skill); mellum.mjs check, learn
docs/                         recipe, backend guides, docs/sdd.md
ladder/, docs/ladder/         the measuring ladder and its phase records
ROADMAP.md, BACKLOG.md        phases and deferred work
```

`npm test` runs the suite; `node build.mjs` regenerates the agent templates
after a prompt change. From `ladder/`: `uv run python -m pytest`, and
`uv run python -m ladder.run_ladder --help` for runs.

## Future work

Two phases remain; see [ROADMAP.md](ROADMAP.md). Everything else is a
[backlog entry](BACKLOG.md) with a reopen condition.

- **M.11:** the mediated test, measured: a rung 9 screen first, then a
  preregistered run on rungs 6–9, then the `/mellum` command that writes
  the test with your main model, shows it, runs it red and dispatches.
- **M.12:** one worker: retire the pi-subagents Worker and rename Mellum
  Mode to mellum-worker. `/mellum` stays.
- **Backlog:** measuring the OpenCode port, an Ollama backend, execution
  bounds, versioned assessments.

## Releases

Pin a tag in both install lines; OpenCode treats an unpinned git spec as
"latest" and may refresh it. Tags follow semver and match the package
version (a test checks it).
