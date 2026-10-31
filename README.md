# mellum-worker

*Apologies for the slop, I was in a hurry.* 

[JetBrains Mellum 2.1](https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking),
a 12B-A2.5B thinking model, as a local, bounded coding worker for
[Pi](https://pi.dev). It takes a precise brief, edits code, runs the tests
until they pass, and reports. Your main model stays in charge.

- **Mellum Worker**: `/mellum <task>` temporarily switches your session to
  Mellum, with the worker prompt and seven file tools, then restores your main
  model and hands it a compact report. No extra packages. 15/15 on the ladder with project facts. The pi-subagents
  child and the OpenCode port were retired on 2026-10-20; their ladder
  records remain, and the table below marks them as history.

Every setting was measured by the ladder (`ladder/`; records in
`evals/`). The 6-bit MLX weights (for Apple Silicon, served by oMLX)
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
section) is the mediated test's question and is unmeasured; the lead is phase 4, which
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
pi install git:github.com/andrevanzuydam/mellum-worker@v0.1.8
```

Then `/skill:mellum-setup`: weights, oMLX server, provider entry, optional
rules, smoke test. It checks each step and asks before writing to your
files. Mellum Worker works once the model is served.

## Use it

**Mellum Worker (Pi).** Type `/mellum <task>`:

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
guards or run record (8/15 on the ladder). Use `/mellum`. If
you do run it bare, start Pi from the project's environment (`uv run pi`, or
`source .venv/bin/activate` first) so `python` and `pytest` are on PATH, and
leave context files on so it sees `AGENTS.md`.

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
honours them over the server's own values. With `force_sampling` on in
oMLX, the server's sampling wins over any
request, so `/mellum check` fails unless it is 1 / 0.95 / 20. The
server-only values bind every client, and other clients of the same oMLX
model can change them.

**Check your setup.** In Pi, `/mellum check`. From the terminal
(`--json` for JSON):

```bash
node <package dir>/scripts/mellum.mjs check --host pi
```

`<package dir>` is `~/.pi/agent/git/github.com/andrevanzuydam/mellum-worker`.
It checks that the server answers and lists the model, that the
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
`~/.pi/agent/mellum-mode-runs.jsonl`; `0` or empty turns it off); `--file`
reads one file instead. Mellum Worker writes records, and `learn` reports
them.

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
([summary](evals/ablation-summary.md)):

| Host | Deliverable | Use | Passes | Wall s, mean | Requests per run | Your main model per run |
| --- | --- | --- | --- | --- | --- | --- |
| Pi | Mellum Worker | `/mellum <task>` | 14/15 (15/15 with facts) | 70 | 13.1 | none |

History, retired 2026-10-20: the pi-subagents Worker passed 15/15 at 54 s
(11.1 requests per run, 6.5 parent turns); the OpenCode port was ported and
unmeasured.

Mellum as the primary agent: 8/15 in bare Pi (51 s), 10/15 in a full
Superpowers profile (72 s). Mellum Worker costs your main model nothing.

Rungs 6–9 build a small FastAPI app (AgentClinic) from four loose phase
specs. A run passes when the project's tests and hidden behaviour tests
pass, no existing test was removed or edited, and nothing was written
outside the file list. Mode, 12 runs each
([note](docs/superpowers/research/2026-10-09-m7-project-facts.md)): facts
off ([A18](evals/2026-10-09-ablation-a18-agentclinic-facts-off/README.md)), a
`## Mellum` section ([A19](evals/2026-10-10-ablation-a19-facts-on/README.md)),
and the fallback only
([A20](evals/2026-10-10-ablation-a20-facts-fallback-only/README.md)). Passes,
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

- [Learning Center](learn/index.md): problems, fixes, and evidence for small coding models.
- [recipe.md §6](docs/recipe.md#6-what-is-settled-and-what-is-not): what is settled and what is not.
- [recipe.md §4](docs/recipe.md#4-using-mellum-worker-delegated): recorded pathologies and the guard for each.
- [Ablation summary](evals/ablation-summary.md): every setting measured in and out.
- [Where the cost goes](docs/superpowers/research/2026-10-09-worker-cost-options.md): Mode versus Worker.
- [Recovery report](docs/superpowers/research/2026-10-07-mellum-recovery/report.md): why Mellum cannot be the primary agent.

## Learning Center

`learn/` is a short course from a machine with no Python to a graded eval
harness, with every claim labelled by the evidence behind it:

1. [Base Pi on llama.cpp](learn/getting-started/base-pi-on-llamacpp.md) —
   install `uv`, llama.cpp and the Mellum weights, chat, and get an answer
   from base Pi.
2. [Working with Pi](learn/getting-started/working-with-pi.md) — starting
   Pi, its tools and sessions, project trust, and the course's `/lesson` and
   `/remedy` commands.
3. [Eval suites and the telemetry](learn/getting-started/eval-suites.md) — three
   AgentClinic suites with hidden graders and known-good/broken qualification,
   graded with `ruff`, `pyrefly` and `complexipy`, and read from the trace.
4. [Extensions and Remedy Units](learn/getting-started/extensions.md) — what a
   Pi extension and a remedy unit are, presets, and `/mellum` as one bundle.
5. [Troubleshoot](learn/getting-started/troubleshoot.md).

From there, take the lessons, starting with
[S0 Start Here](learn/lessons/start-here.md), or go straight to
[The Challenge](learn/challenge/index.md).

All findings lessons are in [Lessons](learn/lessons/index.md). The site builds on
pull requests and deploys to GitHub Pages from `main`
(`.github/workflows/docs.yml`). Run the harness with `uv run learn/code/harness.py run --suite all --grade`.

Build and preview the site from the project virtualenv:

```bash
uv sync                 # creates .venv with zensical and zensical-glossary
uv run zensical build   # writes site/
uv run zensical serve   # live preview on http://localhost:8000
```

Run these from the repository root. `uv` puts both packages in `.venv`, so the
glossary extension is importable by every process the build starts — including
the reload worker behind `zensical serve`. A bare `zensical` outside `uv run`
still fails.

## Requirements

- Apple Silicon Mac, [oMLX](https://github.com/jundot/omlx) 0.6.4 or newer, 9.9 GB for the weights
- Node 24 or newer; Pi 1.0 or newer

Other backends: [docs/backends/llamacpp.md](docs/backends/llamacpp.md) is
smoke-tested but not ladder-measured, and
[docs/backends/ollama.md](docs/backends/ollama.md) lists what a port needs.
Only oMLX has been measured.

## How it works

A 643-character worker prompt, seven file tools, and in Pi two guards: a
nudge when a turn ends empty (at most three) and a loop breaker. The
prompt's default test commands are `uv run --offline pytest -q` (pytest
pyproject) and `node --test <file>` (package.json); a command in the brief
wins, and Mode supplies one from `## Mellum` or the fallback. Detail:
[docs/recipe.md](docs/recipe.md).

Nothing registers at load time. Pi loads the worker extension, dormant
until `/mellum`; the skill writes the provider and rules into your config
from [templates/](templates/).

## Getting started (the next engineer)

Start with **[`LESSONS.md`](LESSONS.md)** — a hundred lessons and dated
addenda from building this, gotchas included — and
**[`LEARNING.md`](LEARNING.md)**, which badges each of those findings by the
evidence behind it. Then, to run the ladder yourself:

1. **The ladder lives in `ladder/`, on `uv`.** `cd ladder`; `uv run python -m
   pytest` runs its suite, and `uv run python -m ladder.run_ladder --help` lists
   every flag. The commands below run from `ladder/`.

2. **Serve Mellum on oMLX first.** Follow
   [`docs/backends/omlx.md`](docs/backends/omlx.md): the model answers at
   `http://127.0.0.1:8001/v1`, and the server holds the tuned settings the
   records were measured under. `/mellum check` tells you when it's drifted.

3. **Register the provider before you run the shipped worker.** `--mode mode`
   is Mellum Worker, and it reads `~/.pi/agent/models.json`; without it Pi
   refuses with `Model "omlx/Mellum…" not found`. Copy it once:
   ```bash
   cp ../templates/pi/models.omlx.json ~/.pi/agent/models.json
   ```
   `--mode direct` wires its own provider, so it runs without this step — which
   is exactly why a direct run can pass while Mode won't even start.

4. **Run it where you can watch.** In one terminal start the follower, then
   launch the run in another:
   ```bash
   uv run python scripts/watch_ladder.py
   ```
   It tails the newest per-rung trace and prints each turn — the thinking and
   the tool calls — as they happen, switching rungs on its own.

5. **Know which worker you're measuring.** `--mode direct` is the isolation
   rig: the ladder supplies the provider and the mediation (`--acceptance-test`,
   `--redispatch`, `--effort-ramp`). `--mode mode` is the real product — Mellum
   Worker with its guards and project facts. They aren't the same run, and a
   direct number isn't a Mode number. `scripts/screen.sh` and
   `scripts/product.sh` (from the repo root) are the two standard shapes.

6. **The frozen acceptance tests are committed**, so a mediated run reproduces:
   point `--acceptance-test` at
   [`evals/2026-10-20-v7-ablation/acceptance/`](evals/2026-10-20-v7-ablation/acceptance/)
   (`test_phase1.py`…`test_phase4.py`).

7. **Every run that backs a claim is recorded** under
   `evals/<date-topic>/`; compare any two mechanically with `uv run python
   scripts/compare_runs.py <dirA> <dirB>`.

## Working on it — the mellum-dev skill

Development here runs through the **`mellum-dev` skill**
([`.claude/skills/mellum-dev/SKILL.md`](.claude/skills/mellum-dev/SKILL.md)),
which operationalizes `AGENTS.md` and [`docs/sdd.md`](docs/sdd.md):
spec-driven development, test-first, frozen-oracle runs, recording every run,
running them where you can watch, and one small PR per win or loss.

**Activate it.** In Claude Code it loads on its own: `CLAUDE.md` says to always
load and follow it when developing here. You know it is active because replies
open with its marker. With other agents, point them at the skill file and have
them follow it; its authoritative sources are `AGENTS.md` and `docs/sdd.md`.

**Why.** The measured claims here only hold if the process holds — tests shown
to fail first, settings frozen without evidence, every run recorded, failures
surfaced instead of swallowed. The skill makes that the default rather than
something to remember.

## Layout

```
prompts/mellum-worker.md      the prompt, single source
extensions/                   Mellum Worker and the guards (Pi)
skills/mellum-setup/          the guided installer
templates/                    provider fragments
scripts/                      merge-json (the skill); mellum.mjs check, learn
docs/                         recipe, backend guides, docs/sdd.md
ladder/, evals/         the measuring ladder and its phase records
ROADMAP.md, BACKLOG.md        phases and deferred work
```

`npm test` runs the suite. From `ladder/`: `uv run python -m pytest`, and
`uv run python -m ladder.run_ladder --help` for runs.

## Future work

The M series closed on 2026-10-20 and is [archived](ROADMAP-M.md); the
Learning Center is the active roadmap ([ROADMAP.md](ROADMAP.md)). Everything
deferred is a [backlog entry](BACKLOG.md) with a reopen condition.

- **The mediated test:** a rung 9 screen first, then a preregistered run on
  rungs 6–9, then the `/mellum` command that writes the test with your main
  model, shows it, runs it red and dispatches. PR #1 is a candidate.
- **Also parked:** an Ollama backend, execution bounds, versioned
  assessments.

## Releases

Pin a tag in the install line; an unpinned git spec is treated as
"latest" and may refresh. Tags follow semver and match the package version
(a test checks it).
