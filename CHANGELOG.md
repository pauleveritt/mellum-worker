# Changelog

Versions match git tags; pin one in both install lines.

## [Unreleased]

### Added

- `docs/ladder/2026-10-20-mediated-6-9-v7/` records the measured pass: Mellum on
  AgentClinic rungs 6–9, n=3, mediated (frozen phase tests) with the v7 prompt +
  focused command + trimmed tools + fail-fast ramp — **12/12**, rung 9 (the
  phase-4 wall, best-ever 2/3) now **3/3**, clearing the historical 9/12 ceiling.
  Note:
  [`research/2026-10-20-mediated-6-9-v7.md`](docs/superpowers/research/2026-10-20-mediated-6-9-v7.md).

- `README.md` gains a "Working on it — the 🍓 skill" section: how to activate
  the `mellum-dev` skill (auto-loaded by `CLAUDE.md` in Claude Code; the 🍓
  marker shows it is active) and why — the measured claims hold only if the
  process does.

- `README.md` gains a "This session — 2026-10-18" summary of the M.11 harness
  work and its screens, flagged as ladder capability and findings (on
  `mlx_lm.server`), not a measured claim.

- Ladder records for a rung 9 screen that ran A21's two changes alone: the
  AgentClinic phase 4 id miss follows the one-file roadmap (5 of 6 runs,
  against 1 of 6 with one spec file per phase). Exploratory, n = 3 per arm.

- The ladder can point a direct-mode run at a second backend and sweep
  sampling for screens: `--backend mlx-lm --base-url <url>` targets a plain
  OpenAI-compatible MLX server (no oMLX admin API, so the server's own launch
  flags, not the ladder, set the server-only values), and `--temperature` /
  `--top-p` override the greedy request defaults. `--backend omlx` stays the
  default and applies/restores the server profile as before, so existing
  records stand; the run record and `versions` now name the backend, base URL
  and any sampling overrides. `--model-id` (direct mode) sets the id the request
  carries so it matches what a plain mlx_lm.server serves (often the weights'
  absolute path); it defaults to the Mellum id, so oMLX runs are unchanged.
  `docs/backends/mlx-lm.md` documents the recipe and the issues hit proving it.

- `run_ladder --acceptance-test <file>` (direct mode): places a hand-written
  failing test (named `test_*.py` so pytest collects it) in the workspace's
  `tests/` before the baseline and makes the task "make tests/<name> pass". Because the test is in the baseline, the
  existing-tests scorer freezes it (the worker cannot weaken it) — the
  mediated-test screen for M.11, run on real Pi and scored by the hidden tests.
  `--redispatch N` adds the verify-and-re-hand loop: after a run it re-runs the
  frozen test and, on failure, hands the failure to a fresh worker on the same
  workspace, up to N times (needs `--acceptance-test`; the run record names the
  number of re-dispatches).

- `EXAMPLE.md`: a worked, example-driven guide to using Mellum — one-shot
  `/mellum`, multi-task spans, handing it a failing test (the reliable pattern),
  project facts, `/mellum check`/`last`, and measuring via the ladder's mlx-lm
  backend.

- `run_ladder --model-spec <spec>` and `--pi-extension <path>` (direct mode,
  `--pi-extension` repeatable): drive a small OpenAI-compatible model as the
  worker for fast iteration. `--model-spec` overrides Pi's `--model` (e.g.
  `content-assist/<id>`) in place of the default `omlx/<id>`, and
  `--pi-extension` loads an extra Pi extension with `-e` alongside
  `--no-extensions` — together they let a content-tool-call-assist plugin turn a
  small model's content tool-calls into real ones. Defaults unchanged; tests
  cover the arg builder and the parser.

- `LESSONS.md`: 100 lessons from the small-model-as-worker effort (plus a dated
  addendum), and
  `docs/superpowers/research/2026-10-19-small-model-tool-presentation.md`
  recording a negative result — stripping a model's native tool field regresses
  tool-calling (fix the chat template's line feeds instead).

- The `mellum-dev` skill gains §10: land each verified win or learning as its
  own small PR, with a changelog entry or a dated research note and the evidence
  inline.

- `extensions/content-tool-call-assist/` vendors the Pi extension that lets a
  small model drive the loop from content tool-calls (JSON `{"tool","args"}` /
  `{"name","arguments"}` or Hermes-XML), gated on the real tool names so model
  data is not mistaken for a call. `scripts/patch-pi.sh [PI_DIR]` installs it
  into a Pi checkout (its imports resolve only there); the ladder's
  `--pi-extension` then loads it for small-model runs. Also mirrored to our Pi
  fork.

### Fixed

- `--effort-ramp` no longer crashes with `ProfileMismatch`. The guard that
  checks effective params against the server profile fired when the ramp
  escalated `max_tokens` past the profile's fixed value; it now skips that
  check while `--effort-ramp` is set (the ramp owns the budget by design). The
  crash was caught by the run's own fail-loud path.

- The re-dispatch retry message now carries the real test failure. It ran
  `pytest -q` (whose output is dominated by deprecation warnings) and sent the
  last 1200 chars — which were all warnings plus the terse summary, omitting the
  assertion. Re-dispatches now run `pytest -q -p no:warnings --tb=short` and the
  message carries the FAILURES section, so the worker sees what actually failed
  instead of retrying blind.

### Changed

- Worker prompt **v7** specializes to the "make one failing test pass" shape:
  read the named test *and* any spec it references, create the module the test
  imports if missing, run *only* the named test, never edit that test or add
  other test files. This is Mellum's best-measured usage (see the 2026-10-20
  record) — narrower than v6's general guidance, and the shipped templates
  regenerate to it. The v6 keep-every-test guardrail folds in.

- Mediated ladder runs verify with a **focused** command,
  `pytest tests/<the-test>`, instead of the whole `tests/` directory, and the
  worker's **tools are trimmed** to `read, ls, bash, edit, write` (`grep`/`find`
  shell out to `fd`/`rg`, which are unavailable offline and wasted turns). Under
  v6 the whole-dir command sent the worker chasing unrelated tests — a 93-turn
  spin on rung 6; the focused command plus trimmed tools removed it.

- `--effort-ramp` (with `--redispatch`): an effort ladder across attempts. The
  initial try and early re-dispatches run **quick** — Pi thinking `off` and a
  small `max_tokens` (2k), which on an easy fix is sub-second — then escalate to
  `medium`/8k and finally `high`/16k only as the frozen test keeps failing. The
  frozen test gates it, so compute is spent in proportion to measured difficulty
  (a quick slice that passes stops the ladder). `qwen-chat-template` maps Pi's
  thinking level into `chat_template_kwargs.enable_thinking`, and `max_tokens`
  is now an overridable request param; the run record names the per-attempt
  thinking level and budget. Default off — existing runs are unchanged.

- Worker prompt v6 adds a keep-every-existing-test guardrail (add new tests
  alongside the existing ones; change only what the task requires). It is
  spec-aligned guidance; on a 2B model it showed no measured lift (the model
  ignores it) and no regression — see the 2026-10-19 research note — so it is
  kept as guidance for more capable workers, not as a measured improvement.

- `--redispatch` now varies the sampling on each retry instead of re-running
  the same greedy decode: the request temperature grows by
  `--redispatch-temperature-step` (default 0.25) per attempt up to
  `--redispatch-temperature-cap` (default 0.5), and the seed moves with the
  attempt number. Past the cap the temperature holds and only the seed keeps
  moving, so retries keep diverging (reproducibly) without going hot — high
  temperature corrupts the worker's JSON tool calls (observed: a 0→1.0 ramp ran
  44 tool errors in 121 requests and thrashed a working app into a broken one).
  Set the step to 0 to keep every retry greedy. The run record names the step,
  the cap and the per-attempt temperature/seed schedule. `seed` is now an
  overridable request param. A re-dispatch now also fires when an attempt hits
  the deadline (a timeout is still a failing frozen test), so a fresh worker
  continues on the same workspace instead of the loop giving up — keep the
  per-attempt `--deadline` small to bound the total.

- The README now opens with the idea the package serves, domain engineering
  (you write specs and tests, Mellum makes the test command exit 0), names
  the mediated test as the next guardrail and how to do it by hand today,
  unmeasured, and says the OpenCode port is ported and unmeasured with its
  measurement on the backlog. Future work lists M.11 (the mediated test) and
  M.12 (one worker, Mellum Mode renamed mellum-worker) in place of M.8–M.10,
  M.3 and M.4.

- A bare `--mode direct` ladder run now sends the worker prompt in place of
  Pi's (`--prompt-mode replace`), which is what the shipped agent file does;
  `--prompt-mode append` is still there for comparing with phases 0–2.

### Removed

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
