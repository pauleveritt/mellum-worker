# Changelog

Versions match git tags; pin one in both install lines.

## [Unreleased]

### Added

- A workspace-confinement guard blocks recursive `find`, `rg`, `grep -r` and
  `ls -R` calls whose absolute paths leave the worker’s workspace. It targets
  the machine-wide search that hung a run, and is on by default.

- A `zensical-glossary` build for `learn/glossary.md`: the page now has
  `###` entries for `screen`, `nudge`, `empty-final nudge`, `no-nudge`,
  `Baseline Worker`, `Baseline Pi`, `arm`, `ablation`, the telemetry columns
  and the extension terms. The extension links each term on its first prose occurrence and
  supplies hover definitions; the build uses `uvx --with zensical-glossary
  zensical build` in CI and in the project checks.

- The suite baseline lesson, `learn/lessons/baseline.md`: Baseline Pi versus
  the Baseline Worker on easy, medium and hard, n = 3, from the 45-session
  llama.cpp run, with the same telemetry as the template.

- Added `learn/code/clinic` and `learn/code/clinic.ps1` wrappers for the
  worker-extension lesson. Each sets the profile, session, model, isolation
  flags and extension, and takes the task as its only argument, so the Bash
  and PowerShell examples are one line.

- The hard eval suite, `learn/code/suites/hard`: the whole AgentClinic build
  from phase 1, with a user-story roadmap, seven phases (archive/audit, a
  database report, and a visits report with filtering, grouping and sorting)
  and four schema migrations generated with `sqlite-utils`. Hidden graders
  cover phases 1–7 and the migrations; `qualify --suite hard` passes.

- The medium eval suite, `learn/code/suites/medium`: AgentClinic's four phases
  as four requests, with a user-story roadmap, hidden phase graders 1–4,
  expected test IDs, a canary, and known-good/known-broken fixtures.
  `qualify --suite medium` passes.

- The first eval suite, `learn/code/suites/easy`: AgentClinic's mission, tech
  stack and hinted four-phase roadmap, one prompt for phase 1, a hidden
  per-phase grader with expected test IDs, and known-good/known-broken
  fixtures. `harness.py qualify --suite easy` proves the grader both ways.

- A follow-up digest for Andre's PRs #3 and #4: ten potential lessons
  (goalposts, the mediated test, v9, mediation as a completeness gate, rungs
  10–12, context, rethink, documents and images, live control, next-concept
  verify), each badged, with support items listed separately.
- The Lessons index is one recommended list of twenty, each with a one-line
  description and an italic author tag, *(Paul)* or *(Andre)*.
- A GitHub Actions workflow builds the Zensical site on pull requests and
  deploys it to Pages from `main`.

- Paul's finding "A short prompt, not a procedure": prompt v5 at 643
  characters, with the A2/A3 removals and the A4 line that came back after a
  14/15, on cited oMLX records.

- The first findings lesson, "The primary agent is the wrong worker": the
  primary-agent baselines (8/15 bare, 10/15 with the operator profile) against
  the bounded worker (15/15), with the prefill and wall costs, on cited oMLX
  records and an Interpretation that says so.

- Getting started lesson 5, "The worker extension": what a Pi extension is,
  `/mellum` as the vehicle, and a live session on the ditch's prompts. The
  worker produces a package whose tests include `assert True` and a CLI of
  seeded demo data, so the vehicle is not yet the remedy. The extension also
  falls back to the session's Mellum model when the oMLX one is absent, which
  is what makes it usable on llama.cpp.
- Getting started lesson 2, "The ditch": one open-ended AgentClinic session
  whose final report claims a working app and a passing test run; checking
  both shows four failing tests and a missing date filter. The harness gains
  `--deadline` so a session like it cannot run the host out of memory.

- The lesson harness runs a session: a task may hold one prompt or several
  (`prompts/`), all sent in one Pi session in one workspace and scored once at
  the finish. `--repeat N` repeats the session, every score line states its n,
  and summaries count sessions rather than rates.

- Paul's findings track is planned as ten lessons, each its own phase, from a
  digest of M.1–M.7 and the A-series; the track index lists them in a
  recommended order, from the primary-agent baseline to the one-file roadmap
  screen, and each lesson stands alone.

- A llama.cpp reference record for ladder rungs 1–5, preregistered first:
  14/15 passed, with the one failure (rung 4, repeat 3 hit the token cap with
  no final reply) reported as it happened. It is what lessons cite as a
  `reference-run`; rungs 6–9 are unrun.

- The ladder takes `--provider`, `--base-url`, `--model` and
  `--context-window`, records the backend it measured, and skips oMLX's admin
  profile when the provider is not `omlx`; a rung-1 smoke drives llama.cpp
  end to end. No reference run yet.

- Getting started lesson 3, "A suite and the telemetry": `suite all --grade`
  runs the easy, medium and hard fixtures, prints each run's turns, tool calls
  and tool errors, and grades the model's files with `ruff`, `pyrefly` and
  `complexipy` beside the score.

- Getting started lesson 2, "Make a mini harness": `learn/code/harness.py`
  runs a task in a fresh directory through a child Pi with a private profile,
  copies the task's tests in only after it exits, and prints one score line;
  `learn/code/record-pi.mjs` records each run's requests, tool calls and
  errors for the next lesson.

- A Project section in `learn/` for maintainers: what the repository
  contains, where its records live, the `uv`/`pyproject.toml` toolchain, the
  backend commands, the checks and the release steps.

- Getting started lesson 1 walks a machine with no Python from `uv` to a
  first base-Pi answer on llama.cpp: the root `pyproject.toml` fetches the
  interpreter, `scripts/backend.py` starts the server and chats, and a
  private profile keeps the learner's own `~/.pi` out of the run.

- A Learning Center site skeleton in `learn/` (Zensical): what the center is, how to read a lesson, the evidence badges and how to contribute; no lessons yet. Build it with `uvx zensical build`.

- `uv run scripts/backend.py serve|start|status|stop|chat` runs Mellum 2.1
  through llama.cpp on Apple Silicon without a daemon: Q4_K_M at 50k context,
  with the settings read from `[tool.mellum]` in the root `pyproject.toml`.
  It is a second backend beside oMLX, and nothing is ladder-measured on it
  yet; the Justfile it replaces never reached a release.

- [docs/backends/llamacpp.md](docs/backends/llamacpp.md) records that backend:
  the flags, the measured numbers (8.38 GB peak and 207 tok/s generation at
  50k context on Q4_K_M), why this model's sliding-window layers make 50k
  context nearly free, and what is still untested, so a 16 GB claim is not
  mistaken for a measurement.

- Ladder records for a rung 9 screen that ran A21's two changes alone: the
  AgentClinic phase 4 id miss follows the one-file roadmap (5 of 6 runs,
  against 1 of 6 with one spec file per phase). Exploratory, n = 3 per arm.

### Changed

- The suite baseline now shows the actual TypeScript that activates the
  Baseline Worker: `setActiveTools`, `createGuardSet`, the request hook and the
  guard hooks, with a link to the full extension.

- The README builds the site with `uvx --with zensical-glossary zensical
  build`; a bare `zensical build` now fails because the glossary extension is
  required.

- Basic Remedies is dropped as a lesson module after its 45-session screen:
  the prompt and loop were null, the nudge was a lead, and hard floored every
  arm. The shipped full worker is now the **Baseline Worker**, with **Baseline
  Pi** as its comparison; the baseline lesson and research record carry the
  result.

- The harness lesson states the settings a run sends to llama.cpp: server
  context 50000, and Pi’s sampled `temperature 1.0`, `top_p 0.95`, `top_k 20`,
  `max_tokens 16384`. These are the out-of-the-box values, not the greedy
  reference block.

- The lesson template now asks for a short “What the telemetry shows” narrative
  under the before/after table and a minimal in-page code sample of the
  remedy under Solution; a link alone is not enough.

- Lesson 1 now points to The ditch as the next lesson, gives Linux and Windows
  install and PowerShell profile guidance instead of treating the macOS
  commands as universal, and drops the internal phase id from its ending.

- The harness lesson now explains `n=1` and how to run more sessions with
  `--repeat`, including the `3/3 sessions passed` summary. It also points at
  `learn/code/suites/easy/` instead of the retired task directory.

- The worker-extension lesson now states the model split plainly: the main
  agent is the larger model Pi started with, and `/mellum` temporarily
  switches the session to Mellum, then restores the main model with a
  handoff. The README says the same.

- Hard's schema changes are now generated migrations: a `migrations.py` in
  the `agentclinic` set, applied with `sqlite-utils migrate data.db` and
  recorded in `_sqlite_migrations`, so a re-run is a no-op. The ad-hoc
  `schema_version` prompt is gone.

- Lesson 4 is rewritten for eval suites: what a suite is (base docs,
  prompts, hidden grader, expected IDs, fixtures, canary), how easy, medium
  and hard differ, how qualification works, the grading and static gates,
  out-of-repo runs and the canary, and how to read the trace. It now spells
  out what hard adds after medium's four phases: archive/audit, the tickets
  report, the visits report, and the four migrations.

- The harness runs **eval suites**, not tasks: `learn/code/suites/`, `run --suite`,
  with per-suite prompts, hidden graders and expected test IDs. Runs live under
  the system temp directory, outside the repo, and a canary in a suite's grader
  marks a session `CONTAMINATED` if the model touches it. Static analysis is
  ruff `F,E9` and complexipy as gates, pyrefly as an advisory.

- The site has two tracks instead of three: **Getting started** and
  **Lessons**. Paul's findings and Andre's findings are one Lessons track
  under `learn/lessons/`, each lesson still standalone with its own authors
  and prerequisites; the old `paul/` and `andre/` index pages are gone.

- The suite lesson says plainly that one session is one observation: the
  harness runs a task once by default, and a rate comes from the ladder, not
  from a handful of sessions.

- The README now links all three Getting started lessons and the harness
  command, and the track index and "How to read a lesson" say what each
  lesson produces, so a reader can tell a lesson worked.

- The M series is closed and archived in `ROADMAP-M.md`. The mediated test and
  the one-worker rename are backlog entries now, the README's future work
  points at them instead of at phases, and the Learning Center is the only
  active programme.

- The Learning Center teaches llama.cpp rather than Ollama, because that is
  what runs here; Ollama stays the backlogged port for a machine without
  Apple Silicon, and the skeleton's pages and badge definitions say so.

- The six-step lesson template's fifth step is Validation — the test suite
  plus `ruff`, `pyrefly` and one complexity tool — rather than a prose claim
  that the change worked, and the phase series is `LC`, not `L`.

- The README's backend line now names llama.cpp as smoke-tested rather than
  measured, alongside the Ollama port's requirements.

- The README now opens with the idea the package serves, domain engineering
  (you write specs and tests, Mellum makes the test command exit 0), names
  the mediated test as the next guardrail and how to do it by hand today,
  unmeasured, and says the OpenCode port is ported and unmeasured with its
  measurement on the backlog. Future work points at the backlog — the mediated
  test and one worker, in place of M.8–M.10, M.3 and M.4.

- A bare `--mode direct` ladder run now sends the worker prompt in place of
  Pi's (`--prompt-mode replace`), which is what the shipped agent file does;
  `--prompt-mode append` is still there for comparing with phases 0–2.

### Fixed

- The Lessons sidebar now lists the two completed findings lessons instead of
  only the index; a test requires every published lesson page to be in the
  nav.

### Fixed

- Fenced code blocks render again: adding the glossary extension had replaced
  Zensical’s default `pymdownx.superfences`; it is now enabled explicitly.

- `scripts/backend.py start` no longer waits silently for up to 15 minutes.
  It says what it launched and where the log is, warns that the first start
  downloads about 7.7 GB, prints the download percentage (or the log's last
  line) every 10 s, and shows the end of the log if llama-server exits.
  `status` on a down server says how to start it.
- `scripts/backend.py` works on Windows as well as Linux and macOS: Ctrl+C or
  closing the terminal no longer kills a server started with `start`, and
  `stop` no longer kills the server during its liveness check. On Windows,
  `stop` uses `taskkill` to end the server and anything it started.

### Removed

- The OpenCode port: `opencode/plugin.js`, the OpenCode templates and provider
  fragment, the setup skill's OpenCode provider phase, the `--host opencode`
  check, the package's `main` and OpenCode keyword, and their tests and
  fixtures. The package is Pi-only; the measured OpenCode rows stay as
  history.
- The pi-subagents Worker: its agent template, the setup skill's worker
  phase, the intercom option, the `kind: "worker"` run-record writer and the
  `learn`/`last` readers, their fixtures and tests, and the ladder's
  `delegated` mode. Old record files on disk are untouched; the code stops
  writing and reading them.
- The ladder's rejected research modes and hooks: `--mode chunked` and
  `--mode brief` with `ladder/ladder/briefs/` (A15/A16, not adopted),
  `--strip-thinking` (A12, reverted) and `--budget-hook` (A13, inert), and
  the `--harness` flag, which had one value and was never read. The records
  that used them keep their launch lines with a dated note; the code last
  exists at `44e1b0b`. `rescore` no longer backfills `baseline_lines` or
  `thinking_reentries`, which no record lacks.

- Mellum Mode's undocumented `MELLUM_MODE_PROVIDER` and `MELLUM_MODE_MODEL`
  overrides, and the `MELLUM_MODE_DEBUG` file writer. Mode runs the one
  measured model entry; `/mellum check` says when the provider entry differs.

## [0.1.8] - 2026-10-13

### Added

- The ladder's AgentClinic rungs take `--facts-section light` (the README's
  `## Mellum` bullets, no `Write only:` list) and `--roadmap one-file` (the
  four phase specs as one `specs/roadmap.md`, asked for as "Implement Phase
  N of specs/roadmap.md"), recorded in `run.json`, for measuring A21.

### Changed

- The README's lighter `## Mellum` section (`Test command:` plus `Do not:`
  naming the bends, no `Write only:`) is now measured: ladder phase A21
  passed 9/12 AgentClinic runs with no writes outside the layout, the same
  as A19's section rerun the same day. Ladder records A21 and A21 control.

### Fixed

- Ladder runs now stop any process still running in the run's workspace
  (a server Mellum started with `&` outlives Pi at the deadline) before the
  workspace is staged, and record them as `leftover_processes` in `run.json`.
  In M.7 such servers held ports 8000–8003 for later runs.

- Back-to-back `/mellum` one-shots recorded an empty task from the second
  run on: the previous run's off-marker lands after the next prompt, and
  the record looked only just before the on-marker. Mellum always got the
  task; only the run record (and `/mellum last`'s Task row) lost it.

## [0.1.7] - 2026-10-12

### Added

- `/mellum last` shows the newest Mellum run at or under the current
  directory, Mode or Worker, as a Markdown table: time and time to first write, turns, tool
  calls and errors, commands, files, tokens, facts, server match, guards and
  the final reply. It reads the run records with no model call, so a short
  follow-up question to your main model replaces a long telemetry prompt.
  `node scripts/mellum.mjs last [--file <jsonl>] [--json]` prints the same
  from a terminal.

- Mode and Worker run records now count tool calls by tool name
  (`toolCalls`), tool results that errored from any tool (`toolErrors`), and
  the seconds before the first edit or write (`firstWriteSeconds`), so a run
  shows how long Mellum explored before writing. Older records lack them.

### Changed

- Published two Pi 1.1.0 ladder telemetry smoke records with reconstruction
  notes and hashed raw evidence: Mode and Worker passed the existing rung-1
  checks. These validate instrumentation, without changing measured defaults.

- Ladder traces now correlate agent instances, requests and tool executions,
  retaining provider chunks and settlement/abort evidence. Runner records
  distinguish exit, signal and deadline; partial traces are flagged without
  changing task scores or everyday Mode/Worker run records.

- The ladder accepts `--pi-executable` for isolated Pi research and records
  the selected runtime and fixture environment. Failed fixture preparation
  now stops before a model request; delegated children use that runtime too.

- Aligned the SDD and roadmap rules with ds4-engine: short current-work
  pointers, dated corrections, explicit phase closure, and exploratory
  screens followed by preregistered runs when deciding a change or claim.
  Phase closure no longer requires a release tag.

### Fixed

- Chunked ladder runs now report exit and settlement for the last launched
  process, so a later timeout cannot inherit an earlier step's success.
  Launch argv also describes a process that actually started.

## [0.1.6] - 2026-10-11

### Added

- Pi Worker runs now write run records to `~/.pi/agent/mellum-worker-runs.jsonl`
  (`MELLUM_WORKER_RUNS` sets the path, `0` or empty turns it off, like
  `MELLUM_MODE_RUNS`), which `/mellum learn`
  reads. The guards extension records one line per finished run; no guard
  decision changes. The README, recipe and setup skill describe both
  record files; OpenCode runs are recorded with M.3.

### Changed

- README and setup phase 8: keep each `## Mellum` bullet on one line (Mode
  drops continuation lines and flattens nested bullets); add `pythonpath =
  ["."]` under `[tool.pytest.ini_options]` when tests import root modules,
  which phase 8 now offers; and a note that Mellum as your main Pi model
  gets none of the package's help, with how to start Pi so `python` and
  `pytest` are on PATH if you do.

## [0.1.5] - 2026-10-11

### Fixed

- The suggested `## Mellum` line no longer says "add files at the project
  root", which contradicts projects that keep `app.py` at the root. The
  README, the setup skill and `/mellum learn` now name the bends instead:
  `Do not: install packages or add dependencies; add __init__.py,
  conftest.py, pytest.ini or setup.cfg files`.

## [0.1.4] - 2026-10-11

### Added

- `/mellum check` in Pi Mode: checks that oMLX answers and lists the
  model, that the server settings no request can undo match the measured
  profile (context window, TurboQuant, thinking budget off, no tool-result
  cap, thinking not forced off, and sampling 1 / 0.95 / 20 when the server
  forces its own), and that your provider entry matches the template,
  failing on a different `maxTokens` or sampling value since those are what
  each request sends. Server values a request overrides (`max_tokens`,
  thinking, penalties) show as info. It only reads; a settings fix is
  printed as the `PUT` to run yourself.
- `node <package dir>/scripts/mellum.mjs check --host pi|opencode [--json]`:
  the same check from the terminal, for OpenCode and Pi Worker; exits 1 on
  any fail.
- Each `/mellum` activation reads the server's model settings (one second
  at most) and warns in one line when one of those binding values differs
  from the measured profile, since other clients of the
  same model can change them. Silent when the server cannot be read.
- `/mellum learn [n]` in Pi Mode: reads the last n run records (default
  10) for the current directory, names what went wrong (guessed test
  command, bent project, false success, long runs, servers, settings
  drift, announced-but-not-taken steps) and suggests `## Mellum` lines. It
  adds only the missing lines to `AGENTS.md`, and only after you answer
  yes; an existing line with another value is shown as a conflict, never
  rewritten, and the section never goes past the 600-character facts cap.
- `node <package dir>/scripts/mellum.mjs learn [--n 10] [--file <jsonl>] [--json]`:
  the same report from the terminal (run it from the project), for OpenCode
  and Pi Worker; it only prints.
- The setup skill's last step runs `scripts/mellum.mjs check` for your host
  and shows its output, so a wrong server setting shows up before the first
  task. `docs/recipe.md` gains a section on the run record, the seven
  `learn` patterns and the check.
- README: a What helped section after the results: telling Mellum the
  test command made most of the difference on the AgentClinic rungs, with
  the A18–A20 numbers in one table and their caveats.
- The run record gains `server` (`match`, and the differing settings), so
  a run on drifted settings can be told apart later; `match` is null when
  the settings could not be read.

### Changed

- The suggested `## Mellum` section no longer leads with a `Write only:` file
  list, which few projects keep: the README and the setup skill show a
  `Test command:` and a `Do not:` line (install packages, add files at the
  project root, weaken tests), and `/mellum learn` turns the bends it sees
  into `Do not:` values instead of a `Write only:` list. `Write only:` still
  works for a strict boundary. The lighter section is not yet measured.
- The expected oMLX values live in `templates/omlx-model-settings.json`,
  split into server-only values (context window, TurboQuant; a test ties
  the context window to the ladder's baseline profile) and the values each
  request overrides (`max_tokens` 16,384, forced thinking, penalties), which
  the setup skill's step 3 still writes for clients that send none. The
  README's Model settings table says which values your provider entry sends
  per request and which only the server sets.
- README: Use it explains Model settings, Check your setup, Learn from your
  runs (with an example report) and Project facts as one flow, with the
  commands for Pi Mode, the terminal, OpenCode and Pi Worker.
- README: a Future work section lists what is on the roadmap, in order,
  with links to ROADMAP.md and BACKLOG.md.
- README: about 40% shorter; same install lines, numbers and links.
- README: says the 6-bit weights are MLX weights, for Apple Silicon and
  served by oMLX, so nobody downloads them for another runtime.
- README: says `check --host pi` covers Pi Mode and Pi Worker and
  `--host opencode` covers OpenCode, and that Pi Worker and OpenCode runs
  write no records until M.7B (`learn` finds 0 runs there today). Its
  `learn` example is now real output on a test fixture.
- `learn` treats `Do not:` as a list: values your `AGENTS.md` already has
  (split on `;`, any case) are left out and the rest go in one new bullet,
  instead of printing a conflict for a line that only needed adding to.
- `learn` shows only the lines it would add to `AGENTS.md` (text and
  `--json` `suggestion`), and no Suggested block when it would add none, so
  the report no longer suggests a line it then reports as kept. A conflict
  on a label other than `Test command:` reads "runs suggest:", not "runs
  passed with:".

### Fixed

- Setup step 3 now also sets `enable_thinking` true, the thinking budget
  off and no tool-result cap. With `forced_ct_kwargs` forcing
  `enable_thinking`, a false value would turn thinking off for every client,
  and a server thinking budget or tool-result cap binds every client too.
- The README now states the cap the measured Mode and Worker runs used:
  `max_tokens` 16,384 with thinking on, verified in the A10, A17 and A19
  traces, which oMLX honours over the server profile's 4,096; only the
  direct-mode research phases ran at 4,096. The recipe and oMLX guide say
  the same, and note the two server settings that beat a request
  (`forced_ct_kwargs`, `force_sampling`). The planned "test 16,384 against
  4,096" run is withdrawn: 16,384 is what was measured.
- `learn` no longer stops on a hand-edited run record of the wrong shape
  (a `null` command, a numeric `endedAt`, `server.diffs` not a list): the
  bad entries or fields are dropped and the rest of the record still counts.
- `/mellum learn` reads `AGENTS.md` again after you answer yes and writes
  nothing if it changed in a way that alters the lines to add, so an edit
  made while it asked is never overwritten.
- `learn`'s `Write only:` no longer lists `/` or `../` for files written
  outside the project, and the report says "1 run", not "1 runs".
- `scripts/mellum.mjs learn --file` with no path exits 2 with the usage
  line instead of quietly reading the default records.

## [0.1.3] - 2026-10-10

### Fixed

- `/mellum <task>` under `pi -p` (and `pi --mode json`) returned at once,
  Pi disposed the runtime mid-run ("This extension ctx is stale"), and no
  run record was written. It now waits for the run, switches back, and
  writes the record before Pi exits. When the host has no UI, warnings and
  errors (the model is missing, Mode did not start in time) go to stderr
  instead of vanishing.

### Added

- `ladder/`: rungs 6 to 9, the four AgentClinic phases, to measure
  whether Mellum can build a small project from its specs (looser phase
  specs with a `## Mellum` section in each fixture's `AGENTS.md`, hidden
  behaviour tests, and reference solutions for the earlier phases). A rung passes
  only when the project's own tests, hidden behaviour tests and the
  existing-tests check all pass (no existing test is removed or edited;
  added tests are allowed, in old or new files) and nothing was written
  outside the `AGENTS.md` write-list; the write-list result is reported on its own as
  `outside_write_list`, and a workspace whose `git status` fails does not
  pass. The runner gains `--mode-facts {on,off}`
  (`off` sets `MELLUM_MODE_FACTS=0`) and `--strip-facts-section`, and
  `run.json` records both. `python -m ladder.rescore --existing-tests-kept
  <phase dir>` rescores a recorded phase under that rule from its retained
  workspaces, as `check_rescored` beside the original `check`.
- Run record schema 2: `schema`, `version`, `promptVersion`, `host`
  (`tui`, `rpc`, `print`, `json`), `activation` (`one-shot`, `on`,
  `headless`), `taskNamesTestCommand`, `edits`, `filesMissingAtEnd`,
  `commands[].mutates`, `finalTurn` (`stopReason`, `hadText`,
  `hadToolCall`), `nudges` and `guardBlocks`. All schema 1 fields are
  kept; lines written before this change have no `schema` field (schema
  1), so one run file can mix both. `commands[].mutates` comes from `commandMutatesFiles`, a heuristic
  for shell commands that change files (`rm`, `mv`, redirects, `sed -i`,
  `git checkout`, `pip install`, virtualenvs).
- `ladder/`: the five-rung ladder that measures this checkout (runner,
  scorer, fixtures and ablation prompts), moved in from the research
  repo. `npm test` also runs its two JS hook tests; its Python tests run
  with `cd ladder && uv run python -m pytest`. It measures what ships: it
  renders the Worker agent from this checkout's own template, loads Mode
  once, and each `run.json` records which checkout ran (`worker_version`,
  `worker_git`). The Mode RPC probe (`ladder/ladder/probe_mode_rpc.py`)
  writes its run records under its scratch directory, not to your
  `~/.pi/agent/mellum-mode-runs.jsonl`.
- `docs/ladder/`: the phase records (A0 to A17 and the earlier phases:
  READMEs, tables, run records, final answers and briefs), moved in from
  the research repo. Raw traces, stdout and diffs are archived per phase
  as `research-2026-10-09` release assets, with their hashes in
  `docs/ladder/PROVENANCE.md`; they are not tracked.
  `uv run python -m ladder.archive_raw` (in `ladder/`) builds those
  tarballs. The first run from this checkout is the `smoke-m6-one-repo`
  record.
- `docs/ladder/ablation-a18-agentclinic-facts-off/`: the A18 record, the
  baseline for the project-facts work. Mellum Mode on the AgentClinic
  rungs 6 to 9 with facts off, three repeats each: 1 of 12 passes under the
  added-tests-allowed rule (0 of 12 under the strict one), median 50
  requests. Its raw files are archived under the same release tag.
- `docs/ladder/ablation-a19-facts-on/` and
  `ablation-a20-facts-fallback-only/`: the records that decide the
  project-facts work. With the `## Mellum` section forwarded, Mode passes
  9 of 12 AgentClinic runs (A18: 1) at a median of 26 requests (A18: 50)
  and 15 of 15 on rungs 1 to 5, so the ship rule holds; with only the
  `python -m pytest` fallback it passes 7 of 12. Write-up in
  `docs/superpowers/research/2026-10-09-m7-project-facts.md`.
- Mellum Mode forwards project facts: the bullets of a `## Mellum` section
  in the project's `AGENTS.md` (600 characters at most; over that Mode
  warns and ignores the section), and, when no test command is given and
  `pyproject.toml` mentions pytest, `Test command: uv run --offline python
  -m pytest -q`. They are appended to every user message Mode sends,
  interactive or headless, so the prompt's "a command named in the task is
  the command" rule sees the project's own test command; the session's
  stored messages are unchanged. `MELLUM_MODE_FACTS=0` turns it off. The
  run record gains `facts` (`source`, `testCommand`, `chars`), the
  handoff summary line names the source, and the session shows
  `[mellum-mode on] facts: <source>` when a span starts. Shipped on the
  ladder's verdict: on the four AgentClinic rungs (12 runs each), 9 of 12
  pass with the section against 1 of 12 with facts off (rescored under
  the added-tests rule) and 7 of 12 with the fallback alone; median
  requests 26 against 50; no run writes outside the write-list (facts off:
  8 of 12); rungs 1 to 5 pass 15 of 15.
- README and `docs/recipe.md` §4b: how to write the `## Mellum` section,
  what it fixes (the prompt's `uv run --offline pytest -q` cannot import a
  root `app.py`; facts off, 11 of 12 AgentClinic runs hit that error), the
  fallback and the switch (write the label as plain `Test command:`; a
  bold or backticked label is not recognised), the caveat that facts were
  measured headless only, and the rungs 6–9 numbers per condition
  (passes, median requests and wall seconds, write-list and deadline
  counts; output tokens are not in the ladder's `run.json`).
- `mellum-setup` phase 8 (optional, Pi): offers to add a `## Mellum`
  section to the current project's `AGENTS.md`, asking for the test
  command and the optional write-only and do-not lines, and shows the
  section before asking to write it.
- Mellum's prompt (v5), tools, sampling and guards are unchanged.

### Changed

- `docs/ladder/ablation-a17-mode-v012/README.md`: the nudge and tool-error
  rows gave runs-with-one counts labelled as totals (A17 2 and 8); they
  now give both, totals first (A17 3 and 12, A14 7 and 13), matching each
  phase's `table.md`.
- Links to the research and the phase records now point inside this repo
  (`docs/ladder/`, `docs/superpowers/research/`) instead of the research
  repo, so they keep working if that repo goes private. The research notes
  and the recovery bundle moved in with a "Moved from" line; the weights
  link names the Hugging Face model card. README and AGENTS.md say how to
  run the ladder (`cd ladder && uv run python -m pytest`) and that raw
  files are never committed.

## [0.1.2] - 2026-10-09

### Changed

- Mellum Mode's handoff block now opens with a one-line summary (requests,
  output tokens, wall seconds, whether the last command finished and
  passed), lists the last fifteen shell commands Mellum ran with failed or
  unfinished ones marked, and flags a written file that is missing when
  the handoff is built. Found by a run where `mv` made the file list wrong.
- `/mellum off` shows a one-line count of requests, tool calls, output
  tokens and seconds.

### Added

- A run record: each Mellum Mode span appends one JSON line to
  `~/.pi/agent/mellum-mode-runs.jsonl` (task, model, cwd, times, requests,
  token usage, files, commands with pass or fail, final reply) for analysis
  outside the session. `MELLUM_MODE_RUNS` sets the path; `0` disables it.
- README: Mode does not send the project's AGENTS.md, so the task line must
  carry the project's test command and layout rules; the test-command tip
  explains why `pytest` and `python -m pytest` differ on `sys.path`.

## [0.1.1] - 2026-10-09

### Fixed

- Removed the `build` npm script. OpenCode installs Git plugins through
  npm's pacote, which runs a nested `npm install` inside the clone when a
  `build`, `prepare`, `prepack`, or `install` script exists, and that step
  fails inside OpenCode with "git dep preparation failed". A manifest test
  now forbids those script names. `node build.mjs` still regenerates the
  templates.

## [0.1.0] - 2026-10-09

First release.

### Added

- Mellum Mode for Pi: `/mellum <task>`, `/mellum on`, `/mellum off`. Runs
  Mellum inside the current session with the worker prompt and seven file
  tools, rewrites each request to hide the earlier conversation, and hands
  one block per task back to the main model. Runs the child guards (empty
  final-turn nudge, loop breaker) itself while on.
- Mellum Worker for Pi as a pi-subagents child agent, and for OpenCode as a
  subagent, both from one prompt source.
- `mellum-setup` skill: a seven-phase guided installer (preflight, weights,
  oMLX server, provider, agent file, optional delegation rules, smoke test).
- Templates for both hosts, an id-aware JSON merge helper for Pi's
  `models.json`, and a render script for the agent files.
- Recipe and backend docs. oMLX on Apple Silicon is the only backend run;
  Ollama is a documented stub.

[Unreleased]: https://github.com/pauleveritt/mellum-worker/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/pauleveritt/mellum-worker/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/pauleveritt/mellum-worker/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/pauleveritt/mellum-worker/releases/tag/v0.1.0
