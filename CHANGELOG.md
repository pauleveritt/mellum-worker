# Changelog

Versions match git tags; pin one in both install lines.

## [Unreleased]

### Fixed

- `mellum-ncm` was silently inert whenever `mellum-acceptance` derived its test:
  ncm read `NCM_TEST` once at extension-load, before acceptance set it at
  `session_start`, so the verify/redispatch gate never fired and a worker could
  self-exit with the work incomplete. ncm now reads its config at settle time,
  and runs the held-out contract with the workspace on `PYTHONPATH` (so
  `from app import app` resolves), mirroring the harness grader's `grade_env`.

### Changed

- `mellum-acceptance` now derives a **redirect-behaviour check** for medium's Phase 4: a POST
  route the spec ties to a redirect status (e.g. "answers 303 with `Location: /complaints`") is
  exercised — the contract finds a real id from the collection page's own action link (the spec
  says each card posts to its route), posts it, and asserts that status and Location. This
  catches the Phase-4 303→307 class the structural contract passed over, so the gate can
  redispatch it. It also normalizes a tagline the spec wrapped across lines, so the page check
  no longer false-fails a correct build whose tagline renders on one line. All spec-derived.
- The easy lesson **E7 · Know When to Stop** is rewritten from the 2026-10-31
  easy screens instead of being an unbuilt conjecture. It no longer presents
  `guard/cap-turns` as the clean answer: the measured causes of a session
  running to its deadline are a foreground server the worker waits on and a
  stop-cap deadlocked against a verify gate, and what stopped cleanly on the
  easy suite was backgrounding the server plus a verify-and-settle gate (1/3 →
  6/6). Its Problem, Eval, Evidence and Solution badges move to `screen`;
  Validation stays `conjecture` (no lesson check has run yet).
- `mellum-acceptance` now scopes its derived contract to the phase the prompt
  names (`Implement Phase 1 …`) and checks the navbar links the spec states by
  name. A phased suite sends one phase per request, so a contract built from the
  whole roadmap used to demand later-phase routes the task never asked for —
  pushing the worker to over-build or sending it a redispatch for the wrong
  thing. It also accepted any `<nav>` or any `<a href>` as "navigation", so a
  page that folded its Home link into the brand passed the gate while the hidden
  grader failed it. The contract now keeps only phases 1..N (N from the prompt;
  a real Pi session that names no phase still gets the whole spec), and asserts
  each spec-named link as a real anchor with that href and that visible text,
  plus the brand — both read from the spec's own navbar sentence, never the
  grader. The harness exports the current prompt so the extension can scope.
- The course now pins **Pi 1.4.0** (was 1.3.0). Guided mode's code panel rides
  on 1.4's fixes: concurrent `custom()` panels and dialogs, extension tools
  staying active on resume, and recovery from a tool call truncated at the
  output limit. Pi 1.4 needs Node ≥ 22.19.0, which the installer's Node 24
  already satisfies. The ladder's measurement rig keeps its own 1.3.0 pin
  (`scripts/baseline/pins.env`), where the recorded baselines were taken, so the
  measured numbers are unchanged.

### Added

- A **Scoreboard** (`learn/scoreboard.md`, the page; `learn/code/scoreboard.py`, the tool):
  every run ever measured, with the fastest pass per configuration on top (fewest turns, then
  least wall — a shorter run is the better pass) and every run below, each with turns and wall.
  Records are keyed by stack *and* a version hash of the extensions' `sha256`, so an improved
  extension shows as a new record that beats the old version rather than blending into it.
  Runs are stored one JSON file per run under `evals/scoreboard/entries/` (merge-friendly — a
  pull request adds its own file and never conflicts); `scoreboard.py consolidate` rebuilds the
  page from every entry after a merge. `run.json` now also records the `model` id.
- An opt-in **improvement loop** (`learn/code/improve.py`, with `learn/code/improve_distill.mjs`):
  it carries what each run teaches (via `mellum-learn`) into a carried `## Mellum` section the
  next run reads as facts, to see whether later runs get faster. It runs against a temp copy of
  the suite and its own records file, so it never touches a measurement, and it records each rep
  to the scoreboard.
- A developer write-up, `docs/developing-with-extensions.md`: how a change moves from the file
  you edit to the number it earns, test-first and mutation-proven, with the two rules that never
  bend (the hidden grader is the oracle; a measured setting is frozen without evidence).
- A lesson now shows the code the run produced. After a before or after run, the
  Eval case and Solution steps print the `.py` the session wrote — S0's `add.py`
  going from `return a - b` to `return a + b` — so you see the fix itself, not
  just PASS/FAIL. First step of guided mode (GM.3): making the code visible in
  the lesson.
- Optional full GPU offload. Set `MELLUM_NGL` (e.g. `999`) and
  `scripts/backend.py` starts llama-server with `-ngl <value>`, offloading that
  many layers to the GPU. Unset — the default — keeps llama.cpp's `--fit`, which
  splits the model across GPU and CPU to fit free memory and stays portable to a
  small machine. `999` forces *every* layer onto the GPU, so use it only where
  the GPU holds the whole model (roomy unified memory, say); on a smaller GPU it
  can run out of memory and fail, so set a partial layer count there or leave it
  unset.
- A friendlier, robust first run. `run.sh` shows a download progress bar for the
  ~8 GB model, waits long enough that the first download does not time out,
  clears stray llama-servers and anything squatting on port 8002 before starting
  (the cause of the old "server did not start"), and silences the Pi update nag
  (pinned 1.4.0). Pi greets the learner with a welcome banner — "type `/start` to
  begin" — and a new `/start` command opens the next lesson. `run.sh` launches
  Pi with `--no-skills` so the learner's run uses the repo's own extensions
  (lessons, remedies, think-tags) alone, and no global `~/.agents/skills` on the
  author's machine leak into the course. The profile sets `quietStartup`, so the
  first screen is the welcome banner rather than Pi's loaded-resources list
  (`[Context]`, `[Extensions]`); `ctrl+o` still shows them.
- A root installer and a one-command runner. `install.sh` / `install.bat` move
  to the repo root, so a learner clones and runs `./install.sh`: it installs the
  tools, pins Pi 1.4.0, installs the mellum-worker harness from the clone (so Pi
  has `/mellum`, not bare), then hands off to the new `run.sh`, which starts the
  server (the first run downloads the model) and launches Pi. Next time, just
  `bash run.sh`. The Home page gains a "For the impatient" block with the
  clone-and-install commands.
- E2 Reading More Than Fits holds: without `context/trim-tool-output` the
  session compacted 13 times and wrote a wrong list; with it, none, in 13
  requests. Recorded under `evals/2026-10-30-context-overflow-check/`.
- New lesson E2 · Reading More Than Fits: eight long notes read whole fill a
  64k context and Pi compacts it (6 compactions and a wrong answer on the
  screen); `context/trim-tool-output` keeps it at none. The `easy`, `medium`
  and `hard` presets list the unit after the E1 repair; the later Easy
  lessons move up one (Looking Around is E3 through Know When to Stop E7).
- New remedy unit `context/trim-tool-output`: a read, bash, grep, find or ls
  result over 8,000 characters is trimmed, with a note saying how much was
  cut and how to search for the part needed, so a model that reads everything
  whole does not fill the context and set off Pi's compaction.
- `run.json` records `compactions`: how many times Pi compacted a context that
  neared its window, summarising away detail the model had read.
- E1 Reasoning Returned as Text is the first lesson whose check held: on the
  LAN host, without the unit the session failed on its record
  (`reasoning_as_text` 7, tests passing), and with `context/repair-think-tags`
  it passed. Recorded under `evals/2026-10-30-reasoning-as-text-check/`.
  The `reference-run` badge now also covers a preregistered lesson check.
- New lesson E1 · Reasoning Returned as Text: on a host whose reasoning
  parser misses, the session fails on its record (`reasoning_as_text`), and
  `context/repair-think-tags` puts the reasoning back. It is the first lesson
  built from a condition that produces its failure every time; screened twice
  on the LAN host (6 and 8 turns without the unit, 0 with it). The other Easy
  lessons move up one: Looking Around is E2 through Know When to Stop E6.
- The think-tag repair is now a remedy unit, `context/repair-think-tags`,
  instead of something every harness session loaded. A lesson can then show
  the serving failure without it, and the `easy`, `medium` and `hard` presets
  and E1's lines list it so later runs stay repaired. The flow still loads it
  in every session, and Pi in this checkout still loads it from
  `.pi/extensions/`; in a lesson's project folder, `/remedy on
  context/repair-think-tags` switches it on.
- A challenge can fail on its record, not only its hidden tests: an optional
  `record.json` caps `run.json` fields (for example `{"reasoning_as_text": 0}`),
  a run over a cap does not pass, `run.json` lists `record_failures`, and the
  `/lesson` FAIL screen names them.
- `run.json` records `reasoning_as_text`: how many assistant turns the model
  was sent back with its reasoning as `<think>` text, a serving fault. It is
  counted from the history the model actually received, so a repaired turn
  counts 0 (35 and 10 on a confounded LAN run, 0 on a clean one).
- E1 Looking Around runs its own challenge, `learn/challenges/looking-around/`:
  readings spread over 200 site files in 8 region folders; find one reading
  and a region's highest sensor, then write a lookup module with tests. Before is bare Pi, after adds
  `guard/break-repeat-loops`, one session each.
- The `/lesson` widget is styled with Pi's theme: the lesson as a title,
  numbered steps, commands in the code colour, and the footer dimmed under a
  rule, wrapped to the terminal's width.
- `/lesson` always shows a widget above Pi's editor: the command legend in
  the checkout, the lesson's steps in a project folder. In a project folder,
  `/lesson` (or `/lesson back`) returns to the repository and reopens the
  lesson at the step you left it, and `/lesson clear` resets the folder to
  its starting files in a fresh session, so a lesson can be run again from
  scratch.
- In a lesson's `project/<number>` folder, `/lesson` shows a guide above
  Pi's editor: what to ask, which failure to watch for, how to try again with
  the remedy, and how to get back. It is shown to you only, never sent to the
  model, and it comes back when Pi restarts in that folder.
- A lesson check is now one session per arm: the before line must FAIL and
  the after line PASS, the same thing a learner sees pressing `r` in
  `/lesson`. Lesson run lines use `--repeat 1`; rates stay with the suites.
- E4 Running Commands now runs its own challenge,
  `learn/challenges/running-commands/`, instead of the shared `easy` suite,
  and the challenge's step 2 gives the project's own run command
  (`python app.py`), the way a README would. Revision 3 of its lesson check
  is preregistered on the 6-bit reference model.
- The lesson track is renumbered to the lessons that remain: Easy E1–E6,
  Medium M1–M8, Hard H1–H6. Three stub lessons name their remedy and wait for
  their challenge: E6 Know When to Stop (`guard/cap-turns`), M7 Keep a Plan
  (`tool/keep-a-plan`) and M8 Build a Suite (your own grader). Each remedy
  unit's `meta.lesson` and the remedies table follow the new numbers.
- In `/lesson`, `p` now moves the Pi you are in into `project/<number>`, with
  the lesson's starting files and task, and `/lesson home` moves it back. Trying
  a lesson by hand no longer means opening a second terminal and starting
  another Pi; `/remedy` and `/lesson` work in the project folder too.
- `/lesson`'s FAIL screen now says why: it names each hidden check a session
  missed, and adds the lesson remedy's pathology line under the verdict, so
  a learner sees what failed and what the remedy is for before applying it.
- `scripts/lesson-check.sh <lesson number>` runs a lesson's before line then
  its after line at the page's n and prints both verdicts, so a lesson check
  is one command. The lines come from the lesson page; arms run one at a time
  with port 8000 checked free; it detaches, so a closed terminal tab cannot
  kill it. The default profile, `scripts/baseline/lan-profile/`, is the 6-bit
  Mellum on the LAN vLLM host the uniform-lessons cycle checks against.
- `/lesson` runs a lesson's before and after lines on the model Pi is using
  (its provider and model from the profile's `models.json`), and shows which
  model on the run line. Before, `r` always used the pinned llama.cpp profile,
  so a learner on any other server got "no model answered". A line that names
  its own `--profile` keeps it.
- Four lessons and the server pathology now cite the 2026-10-29 local 6-bit
  MLX runs: the foreground-server stall reproduced on a second host and
  quantization (two of three bare `build-a-harness` sessions stalled on
  `uvicorn`), from the lessons smoke
  (`evals/2026-10-29-local-lessons-smoke/`, 32/36 graded) and the 6-bit
  ladder baseline (`evals/baseline/2026-10-29-local-mellum-baseline/`, 21/36 vs the
  pinned BF16 26/36). M6, E6, E2, M1 and `pathologies.md` updated; badges held
  at `screen`/`conjecture` (the runs are n = 1/n = 3 screens).

- The Running Commands lesson check, revision 2, recorded with revision 1
  (`evals/2026-10-29-running-commands-check/`): a challenge that makes
  every session start a server. Without the guard the model backgrounded it
  itself and passed; with it, six foreground starts were refused and those
  sessions passed. The lesson says so: no FAIL → PASS on a short task. Two
  new failures were seen: `killall -f uvicorn`, and tests run through this
  repository's `.venv` from outside the workspace. The challenge folder is
  now `learn/challenges/running-commands/`.

- Manual lesson work has its own folder: in `/lesson`, `p` on a run step
  sets up `project/<lesson number>` with the lesson's starting files, its
  task as `TASK.md`, and `/remedy` ready, so the model never builds in the
  repository. `/lesson clean` removes `project/`, which git ignores.

- E5's lesson check, run on its own challenge and recorded
  (`evals/2026-10-29-e5-check/`): before and after both passed 3 of 3,
  because the challenge rarely provoked a foreground server. When one session
  did start one, the guard refused it and the session went on to pass. E5
  says so; a revised challenge comes next. S0 now says how to open Pi and
  start the lesson.

- The lesson check's record (`evals/2026-10-29-lesson-check/`) and its
  result: every lesson run with and without its remedy at the page's n on
  the vLLM host. No lesson fails every session without its remedy; the short
  prompt and project facts show direction only, and the thinking and nudge
  lessons point the other way. Each tested lesson now states its result.

- S0 · Start Here, the first lesson: it teaches how every lesson works by
  being one, with a before run that fails and an after run that passes. A
  stand-in plays the model, so it needs no model or GPU and both runs finish
  in seconds. `/lesson` opens it first.

- `/lesson` in Pi: take the course inside the harness it teaches. It lists
  the 23 lessons in track order (finished ones ticked), shows each lesson's
  picture, and walks through the opening, Paul's six steps and the key
  points one screen at a time. On the Eval case and Solution steps, `r` runs
  the page's before and after lines (one session; `R` runs the page's n) and
  summarises each session from its `run.json`: PASS or FAIL, and why (a
  stall, checks that never ran, missed checks, or no model answering). The
  lesson page is its only source.

- `/remedy` in Pi: switch remedy units on and off in a live session
  (`/remedy` picks from a list, `/remedy on guard/break-repeat-loops`,
  `/remedy off …`, `/remedy preset:easy`), with a status line saying how many
  are on. Everything starts off. It loads automatically when Pi runs in this
  repository once you have run `/trust`.

- Remedy units under `remedies/`: each remedy as one file with one role,
  loadable alone with `pi -e`. First the five guards
  (`guard/block-foreground-server`, `break-repeat-loops`, `stay-in-workspace`,
  `refuse-whole-file-rewrite`, `cap-turns`) and `nudge/nudge-empty-turn`, each
  wrapping the worker's existing function. The worker itself is unchanged.
- Context remedy units: `context/use-short-prompt`, `context/add-project-facts`
  and `context/narrow-tools`, each changing one part of the request exactly as
  the worker does (the worker now exports `withFacts` and `narrowTools` so the
  units share its code; its behaviour is unchanged).
- Opt-in remedy units for the experimental extensions:
  `tool/background-long-commands`, `tool/lookup-library-docs`,
  `tool/keep-a-plan`, `check/check-code-quality` and
  `workflow/spec-driven-flow`. Each loads its extension unchanged; none is
  installed by default or measured as a remedy yet.
- `harness.py run --remedy LIST` loads remedy units on top of the arm (names
  such as `guard/break-repeat-loops`, or `preset:baseline-worker`), and
  `--extension PATH` (repeatable) loads your own Pi extension. Each session's
  `run.json` records the remedies and every loaded file with its SHA-256, so a
  Challenge attempt says exactly what it ran.

- `scripts/baseline/baseline.py lessons --full` runs every lesson's commands at
  the page's own n and deadline (the default stays one session per arm, capped
  at 900 s), so a lesson's claim can be checked, not only smoke-tested.

- A record of the full spec-driven flow on the vLLM baseline host
  (`evals/2026-10-29-vllm-flow/`), with its research note: one run per
  level, Bronze 4/4 hidden checks (a pass), Silver 13/18, Gold 30/34. It also
  documents three gate faults in the flow harness that the next fixes address.

- The replicable vLLM baseline's record, `evals/baseline/2026-10-28-vllm-baseline/`:
  vanilla Pi with Mellum 2.1 BF16 on vLLM passed 26/36 ladder rungs (12/12 on
  rungs 1–4, 4/12 on the web-app rungs 6–9, 8/9 on 10–12) and 1/3 Bronze, 1/3
  Silver, 0/3 Gold. It is the score to beat on The Challenge page and the
  reference later changes are measured against (a screen at n = 3, not a rate).

- **The Challenge**: the three eval suites are presented on the site as
  Bronze, Silver and Gold, a challenge learners can attempt to test what they
  have learnt, with the baseline as the score to beat. The CLI keeps
  `--suite easy|medium|hard`, so existing commands and records still work.

- `harness.py run --stall SECONDS` ends a session as **stalled** when one tool
  call has run that long with no result (a foreground server the model
  started), instead of waiting out the whole deadline. The record carries
  `stalled` with the command; Pi is untouched. The vLLM baseline pins it at
  120 s for the suites and the lesson runs, and `baseline.py run --suites-only`
  reruns just the suites into the latest baseline, keeping its ladder.

- `uv run scripts/baseline/baseline.py lessons` runs every lesson's "Run it
  yourself" commands once per arm against the baseline's vLLM box, with the
  pinned Pi, and writes a summary, so each lesson's command is proven to run
  and grade end to end It runs three commands at once and caps each
  smoke session at 900 s (both pinned), so the whole set takes about an hour.

- Every page of the Learning Center has an illustration in one shared flat
  style, generated from `learn/assets/illustrations/prompts.toml` by
  `uv run scripts/illustrate.py` (fixed seed per image, so they regenerate the
  same), and evidence badges render as icon pills that link to their
  definitions.

- A replicable vLLM baseline, `scripts/baseline/`: Pi and the model with no
  plugins or extensions, on every ladder rung and eval suite. vLLM runs on a
  rented GPU (pinned: RTX A6000 48 GB, about $0.45/h on vast.ai); Pi and the
  harness run on your machine through an SSH tunnel. `uv run
  scripts/baseline/baseline.py all` installs a pinned, checksummed Node and Pi
  under `.baseline/`, rents the GPU, serves, runs, fetches and destroys the box,
  on macOS, Linux and Windows (WSL2 for the run). Everything that defines the
  baseline is pinned in one file, and the vast.ai token lives in a git-ignored
  `vast.env`. `--screen` runs screen 1 (two rungs and the easy suite, n = 1)
  before the full baseline.

- The vLLM baseline's screen 1 record, `evals/2026-10-28-vllm-screen1/`:
  vanilla Pi passed ladder rung 1, hung on its own foreground server at rung 6,
  and wrote the easy suite's app under the wrong name. The pinned stack works
  end to end; the numbers are n = 1 leads, not rates.

- `harness.py run --profile <dir>` runs the eval suites against another Pi
  profile (provider, model, sampling), so the bare arm can point at the
  baseline's vLLM server.

- `run_ladder --pi-agent-dir <dir>` gives primary mode a pinned Pi profile to
  mirror instead of `~/.pi/agent`, so a plain baseline does not pick up the
  operator's own Pi configuration.

- `scripts/screen.sh` reads `MELLUM_PROVIDER` and `MELLUM_BASE_URL`, so the
  standard screen can point at a vLLM (or any OpenAI-compatible) server without
  hand-assembled flags. oMLX stays the default.

- A ladder run against a server other than oMLX now records that server's
  version and served models (`/version`, `/v1/models`) and every GPU's name,
  VRAM and driver (`nvidia-smi`) in `run.json`, so a record proves what it ran on.

- The flow harness can now drive a model whose server templates reasoning itself, not only the
  default worker. `MELLUM_FLOW_THINKING` overrides the per-phase sub-agent thinking level for every
  phase in one place; set it to `off` (together with `flow_run --thinking off --thinking-format
  openai`) to call such a model as plain OpenAI, with no client-managed reasoning channel to
  mis-template. Left unset, each phase keeps its own thinking budget, so the default worker's calls
  are byte-identical. This is the cascadable knob that lets a different model be swapped in and
  measured against the same flow.
- The read-only flow phases (plan, review_plan, examine, review_code) now carry a dedicated
  `mellum-loopguard` extension with two guards: the loop-breaker (an unbroken run of identical no-op
  calls, e.g. the same `ls .`, is capped) and an arg-agnostic step budget (after a generous number
  of tool calls the phase is told it has enough context and must produce its answer). The budget
  catches the runaway the loop-breaker misses — a model that re-issues the same read with a slightly
  different arg each time, so no two calls are identical. Previously only the coder had the
  loop-breaker, and a non-converging model could spin a read phase past a thousand events. Both trip
  only on a genuine runaway, so a model that converges — including the default worker — is unaffected.
- `MELLUM_FLOW_MAXTOKENS` caps the per-phase output budget from one place — a ceiling, never a
  raise. examine's budget is a deliberately large 32000 so a reasoning worker can think then emit;
  a model that instead pours out content without stopping needs a tighter ceiling so the phase
  terminates and its answer is salvaged. Unset, every phase keeps its own budget (the default worker
  is byte-identical). Cascadable, like `MELLUM_FLOW_THINKING`.
- The flow harness now enforces a SPEC-COVERAGE guarantee when the examiner writes a phase's
  acceptance test: the harness extracts the contract tokens the spec itself NAMES (the routes it
  declares, the migrations/indexes/views/columns it names, the status codes it pins) and, if the
  authored gate does not even reference one of them, re-dispatches the examiner naming the exact gaps
  until the gate covers them or a small retry budget is spent. This closes the measured proxy→oracle
  gap where a run passed every self-authored phase gate and the visible suite yet scored 26/34 on the
  hidden grader, because the gates were a subset of the spec (no `/visits` route, no `note`-column
  migration, a redirect asserted loosely so a wrong 306 slipped through). Agnostic: every token is
  read from the phase's own spec, never from the hidden grader. See
  `docs/superpowers/research/2026-10-27-proxy-oracle-gap.md`.
- `flow_run` records the GRANULAR hidden grade in `result.json` — `hidden_passed`/`hidden_total`
  (e.g. 31/34), not just the full-pass bool — plus a `coder_feedback` flag, so a run's real score is
  visible and arms of a comparison can be told apart (the full-pass bool is almost always False on
  hard, so it discriminates nothing).
- `content-tool-call-assist` now normalises a small model's loose tool call into a valid named-args
  JSON object: a POSITIONAL list of arguments (`{"tool":"write","args":["a.py","hi"]}` — a tiny
  model's common mistake) is mapped onto the tool's declared parameter order, and Hermes/Qwen XML
  (`<function=…><parameter=…>`) is converted to the same shape. The pure parser moved to a
  dependency-free `parse.ts` with a unit-test suite (`tests/content-tool-call-assist.test.mjs`).
- `flow_run --flow-mode free`: an agent-decided flow alongside the default forced pipeline. Forced
  mode drives a fixed six-step order (plan → review → examine → code → review → test) as ordered
  tools; free mode enforces only two invariants and lets the agent decide every step between them —
  (1) a frozen external acceptance test exists BEFORE any build (one examine pass writes it, the
  harness freezes it, the agent cannot weaken it), and (2) the exit is verified by the harness, not
  self-declared: it re-runs the frozen gate and, on a fail, re-dispatches the agent with the failure
  text ("didn't pass — here's what failed, try again"), bounded by `--attempts`. Each phase records
  whether the fixed model was EVER able to solve it and how many rounds it took (`phase_rounds` in
  `result.json`). The default is unchanged (`forced`).
- `flow_run --flow-mode free --memory memory.jsonl`: a portable, learned grounding store — almost a
  skill, but grown from the agent's own mistakes. Lessons whose situation matches a phase are
  injected into the build (like a skill), and a GENERAL, agnostic lesson is distilled from every
  gate failure and appended, so the run learns from its mistakes and the file carries forward to
  later runs, other machines, or a fine-tune. An agnostic guard refuses any lesson carrying a
  concrete route, quoted literal or multi-digit value — the memory stores general discipline, never
  the suite's answers. The with-vs-without comparison is preregistered as the deciding experiment;
  grounding is off unless `--memory` is given.
- The flow harness now puts the workspace under git and checkpoints it after each PASSING phase, so
  a later breaking change can be reverted to the last known-good phase and redone instead of
  poisoning the accumulated work. If a round leaves the app uncompilable (e.g. a phase-7 attempt
  that left `app.py` with an unterminated string — the clean-run failure that sank a whole grade to
  zero), the harness reverts to the last checkpoint and redoes from there; and it never grades a
  broken app — it reverts first. The venv, caches and traces are git-ignored so only the app and
  gates are tracked.

### Fixed

- Reasoning that a serving host returns as `<think>` text is turned back into
  a thinking block, by a new adapter, `extensions/mellum-think-tags.ts`. Some
  vLLM builds' streaming reasoning parser misses every turn after the first;
  Pi then showed the reasoning as the reply and sent it back as things the
  model said. The adapter loads in every harness and flow session, in Pi in
  this checkout, and in each lesson's project folder; on a correctly served
  reply it does nothing.

- A harness run that is stopped part-way (as `/lesson` does when you leave
  a lesson while `r` is running) now still ends the Pi session and any
  server it started. Before, `SIGTERM` ended the harness before its sweep and
  the server kept port 8000.

- No Pi session the harness or the flow starts reads stdin any more. Pi run
  with `-p` appends piped stdin to its prompt, so a script that fed the
  harness on stdin (`scripts/lesson-check.sh`, 2026-10-29) handed its next
  command to the model as part of the task; the session ran it, and the
  check was void. `lesson-check.sh` also closes stdin for each run line.

- The harness now ends a server the model started, even after the session
  stalls. Pi starts each bash command in a process group of its own, so the
  old group sweep never reached it: on 2026-10-29 a stalled session's
  `uvicorn` kept port 8000 and blocked the next arm. Every process still
  running inside the run's workspace is ended and listed in `leaked.json`.

- `harness.py run` makes `--runs-dir`, `--profile` and `--suites-dir` absolute
  before Pi starts. Pi runs inside the workspace, so relative paths sent the
  recorder and profile lookups there and every session ended at once with
  "Unknown provider".
- `harness.py run --pi-binary path/to/pi` works with a relative path. Pi runs
  inside the workspace, so the path used to be looked up from there and the
  run failed with "pi not found".
- `baseline.py lessons` checks the model answers before every command and
  reopens the tunnel if it does not, stopping if it still does not. A dropped
  tunnel used to record whole arms of empty, zero-token sessions as fails.
- The flow examiner's gate always builds its `TestClient` with
  `follow_redirects=False`. A client that followed redirects turned the
  spec's 303 into a 200, so the gate failed a correct app on every round.
- The flow harness keeps a phase's frozen gate when it reverts a broken
  round. The revert used to delete it, and the next round froze a weaker gate
  for the same phase: Silver's phase 4 then "passed" with no resolve or
  reopen code.
- `scripts/baseline/baseline.py serve` starts and tracks vLLM by the PID
  `serve.sh` keeps. Its process-name check matched its own command line (so
  vLLM was never started), and vLLM 0.32 renames its process, so a live
  server read as dead.
- `learn/code/flow_run.py` runs again. A relative `--runs-dir` sent Pi's
  recorder and profile paths into the workspace, so every round failed with
  "Unknown provider" before the model was called; the runs dir is now made
  absolute. The final hidden grade also crashed after `score_workspace_details`
  gained a fourth return value; it now reports checks passed out of expected.

- Lesson text that contradicted its own evidence is corrected: H1's pass
  counts are identical on Bronze and Silver (not "one session apart"); E4's
  are identical in one sample and one apart in the other, and its worker had
  two passing sessions; E2 had one failing session, not two; E3's facts-on
  peak input is the valid sessions' 13,813, not the excluded session's 19,721;
  M2's eval case says five sessions per arm, as its table and preregistration
  do; M3's `models.py` sentence now says what happened; M1 says the
  strip-thinking arm exists but has not run, and gives its command; How to
  read a lesson counts five Getting Started steps.

- The ladder's workspace preflight no longer refuses every Python rung on
  macOS with Python 3.15: `/var` is a link to `/private/var` there, and 3.15
  reports the venv's interpreter by its real path, which the preflight compared
  literally.

- `run_ladder --mode primary` now asks Pi for the model the run names
  (`--model`) instead of the hard-coded oMLX 6-bit id, so a plain baseline on
  another server reaches its model rather than failing before the first request.

- The flow coder never saw WHY the acceptance test failed on a retry: `code()` reads `REVIEW.md`
  (the reviewer's prose) but `test()` wrote nothing there, so after a failed gate the coder rebuilt
  from the plan blind and repeated the same miss — e.g. a required route it never implemented,
  failing with a 404 every round, with best-of-N making the identical omission both times. `test()`
  now writes the failing checks to `REVIEW.md`, which `code()` reads, so the coder sees the gap and
  can fix it (the "didn't pass — here's what failed, try again" loop the free arm already had). The
  feedback is **labelled for the app, not the test**: it says the application failed these checks,
  to fix `app.py`/`models.py`/`templates/`, and never to edit a test (the harness restores the
  frozen gate before grading anyway) — and it strips the gate test-file paths, so a small model is
  not pointed at a test file to edit instead of fixing the code. Toggle with
  `MELLUM_CODER_FEEDBACK=0` (default on), so the feedback-vs-no-feedback comparison runs from one
  binary.
- The flow harness never logged a sub-agent's tool calls to the live feed: the streaming keyed on
  an event type (`tool_call`) that pi's `--mode json` does not emit for a sub-agent, so a hung phase
  showed only a frozen event count with no command. It now reads the schema pi actually emits
  (`message_end` toolCall content, `tool_execution_start`), so every sub-agent command — including
  the one a stuck phase is waiting on — appears in the feed and a hang is diagnosable.
- `content-tool-call-assist` promoted a tool call whose `arguments` were a JSON list (arrays are
  `typeof "object"` in JS), which the inference server then rejected with `422 … arguments must be a
  JSON object, got list`, crashing the run instead of re-prompting. A list is now mapped to named
  arguments when it fits the tool's parameters, and an unmappable list or bare scalar is rejected so
  the loop re-prompts rather than sending an invalid call.
- The flow examiner's report gates destructively reseeded the fixture database (`DELETE FROM
  tickets` / `DELETE FROM visits` then inserting their own rows), which persisted in the
  workspace's `data.db` — so the hidden grader read the examiner's invented data, not the fixture,
  and hard phases 6-7 failed the hidden grade while passing their own gates. The examiner is now
  told, generally, to compute a report's expected value from the data ALREADY in the store and
  never delete/overwrite/reseed a persistent store (roll back any row it must add). Derived from the
  spec's "a report from the database", not from the hidden grader.

### Added

- `run_ladder --acceptance-test <file>` (direct or `--mode mode`): places a
  hand-written failing test, named `test_*.py` so pytest collects it, in the
  workspace's `tests/` before the baseline and makes the task "make tests/<name>
  pass" (verify with that test, don't start servers). Because the test is in the
  baseline, the existing-tests scorer freezes it, so the worker cannot weaken it —
  the mediated-test screen. `--redispatch N` (direct) adds the verify-and-re-hand
  loop: re-run the frozen test after a run and, on failure, hand the failure to a
  fresh worker on the same workspace, up to N times; the record names the number
  of re-dispatches. Screens only so far (rungs 6–9 12/12 mediated, Mode rung 9
  0/3 → 3/3).
- `run_ladder --effort-ramp` (with `--redispatch`, opt-in): the first attempt runs
  quick (Pi thinking off, 2k `max_tokens`) and re-dispatches escalate to medium/8k
  and high/16k only while the frozen test keeps failing; the record names each
  attempt's level and budget. On a known-hard rung a fixed high budget was faster
  (v7 ablation), so it is not a default.
- `run_ladder --pi-extension <path>` (direct or `--mode mode`, repeatable) loads an
  extra Pi extension with `-e`, so an extension such as `extensions/mellum-ncm.ts`
  can be measured without shipping it.
- `run_ladder --temperature` / `--top-p` (direct) override the greedy request
  values for sampling screens, not measured claims. A server other than oMLX is
  reached through `--provider`, `--base-url` and `--model provider/id`;
  `docs/backends/mlx-lm.md` is the recipe for a plain `mlx_lm.server`.
- **The run standard**: `scripts/screen.sh <rung> <model-id>` (the measurement
  rig — direct, mediated, `tuned`, repeat 3, redispatch 5, effort-ramp, thinking
  off, guards on) and `scripts/product.sh <rung>` (the shipped worker, `--mode
  mode`). Two fixed shapes so runs compare like-for-like instead of
  hand-assembled flags; both write to `runs/` (git-ignored). The dashboard's rung
  picker starts a run through them.

- An Introduction page, `learn/introduction/index.md`, ahead of the Getting started track: what a
  language model, a prompt, context, tools, a harness, an agent and a feedback loop are, so a
  newcomer has the vocabulary before the first lesson.

- Getting started gains `learn/getting-started/install.sh` and `install.bat`, which install the
  pinned tool versions the lessons need on macOS, Linux and Windows, and a `troubleshoot.md` for
  the install and backend failures met while checking the track on each platform.
  `scripts/backend.py` was reworked alongside so it starts and stops the server on all three.
- `flow_run.py` can resume a run partway through: `--start-phase N --seed-from <a prior run's
  workspace>` seeds the built app and the frozen per-phase gates (`plan/gate/phase_1..N-1.py`) from
  that earlier run and runs only phases N..end. This makes iterating on a late phase cheap — no need
  to re-run the earlier phases each time. It validates that every earlier gate exists in the seed,
  and does not copy the seed's venv or traces (the venv is recreated by `uv sync`).

- The flow examiner is given a general completeness rule for computed/report endpoints: seed
  representative rows and assert the EXACT computed/grouped/sorted/filtered result, with a row
  included AND one excluded by each filter or definition the spec states (including a definition
  keyed off a specific column rather than the obvious field) — never accept a bare 200 or a
  non-empty body, which a stub also returns. The schema rule now also asserts named migrations are
  actually recorded/applied, not merely defined. These target the hard phase 6-7 hidden-oracle gap,
  stated generally and derived from the spec, never from the hidden grader's values.

- The examiner is told to write SELF-CONTAINED tests (create the records they need, never assume a
  seed record at a given id or state), to READ the earlier frozen gates and reuse their proven
  conventions (client setup, whether a record is created with form `data=` or `json=`, field
  names) rather than reinvent them, and to assert a before/after DELTA for any count or total the
  app reports rather than an absolute equality. Measured against a known-correct implementation,
  these took a regenerated phase-5 gate from 5 brittle failures to 1 (then the delta rule for the
  remaining aggregate-count case). All stated generally; the examiner still derives specifics from
  the spec and the earlier gates, not from the hidden grader.

- A `flow` mode for the ladder (`run_ladder --mode flow`): runs the spec-driven flow
  orchestrator (mellum-flow.ts — plan/review/examine/code/test, the examiner writing the
  acceptance test from the spec) on a rung's fixture and scores it with the rung's own hidden
  grader, so the spec-driven paradigm is measured on the same rungs as the direct baseline.
  It cleared rung 6 (AgentClinic phase 1), which both models fail in direct mode because the
  fixture ships no visible test — the examiner supplies the missing target.

- The flow harness now keeps its bookkeeping (`TASK.md`, `TODO.md`, `REVIEW.md`, the frozen
  gate) under a single `plan/` folder instead of the workspace root, so it never mixes with
  the solution tree; the ladder's flow mode moves `plan/` out of the workspace before grading
  so it cannot trip the AgentClinic write-list (`app.py, models.py, templates/, tests/`).

- A workspace-confinement guard in `mellum-guards.ts` (`confineToWorkspace`, on by default):
  it blocks a `bash` tree-walk (`grep -r`/`-R`, `find`, `rg`, `ls -R`) that targets an
  absolute path outside the worker's working folder, while allowing relative searches and
  paths under it. A worker had run `grep -rl pattern /Users /var /tmp …`, which crawls the
  whole machine and hangs the run for minutes; the guard stops that and tells the worker to
  search within its workspace.

- Fix the orchestrator "stall": the phase task and reviewer feedback now flow
  through files (`TASK.md`, `TODO.md`, `REVIEW.md`) and every phase tool is called
  with NO arguments. oMLX's tool-call parser drops a tool call whose JSON arguments
  are a large multi-line string, so passing the whole task as `plan(task=…)` was
  silently dropped and the agent emitted nothing — the cause of every stall on a
  non-trivial task (easy, with a 33-char task, always parsed; larger phases did
  not). Argument-free tool calls always parse.

- `flow_run` best-of-N concurrency (`--concurrency N`): run N attempts per phase
  in parallel on the batched oMLX server (sampling temperatures spread 0.3→1.2 for
  diverse tries), forking the workspace per attempt and promoting the first that
  passes. Turns the server's concurrent throughput into wall-clock speed and beats
  the per-phase variance of a single sequential try.

- A `mellum-knowledge` extension (`extensions/mellum-knowledge.ts`) and
  `learn/code/docs_lookup.py`: a `lookup` tool grounded in the INSTALLED venv
  packages. `docs_lookup.py` builds a BM25 index over the venv's package source
  — every class and function with its signature (default values included) and
  docstring — and returns the top matches for a query; the extension exposes it
  as a tool the coder calls when unsure of an exact API, or when a failure is
  API-shaped (`TooManyRedirects` -> FastAPI's `RedirectResponse` defaults to
  307, so a POST redirect needs `status_code=303`). It reflects the exact
  installed versions — the only way past the model's training cutoff, since the
  ladder runs on Python 3.15. The harness builds the index on the initial run
  and caches it; it grounds on library docs a developer would have, never the
  task solution or the hidden grader. The index auto-rebuilds when the installed
  packages change (a newly-installed dependency becomes searchable), and the
  tool takes a `rebuild` flag to force a re-index on demand. Offline,
  dependency-free (pure-Python BM25). Loaded on the coder.

- Smart decomposition in `flow_run`: split a task on Phase/Step headers at ANY
  level, then any markdown header, so a multi-level spec (the hard suite's
  `# Phase 5`–`7` under `## Phase 1`–`4`) breaks into its real phases instead of
  one wall. Each phase carries a small, constant forward context — a
  model-determined **north star** (a one-line orient call over the phase
  titles), a running summary of what is already built, and the last phase's
  context — so a decomposed step stays grounded without the model ever seeing
  the whole task.

- A `mellum-flow` extension (`extensions/mellum-flow.ts`) and its runner
  (`learn/code/flow_run.py`): the **workflow as tools the model calls**, not an
  external loop. It registers the phases as tools — `plan`, `review_plan`,
  `code`, `review_code`, `test` — and the top agent orchestrates them from a
  workflow prompt, iterating on REDO / test failure. Each phase (except `test`)
  runs as an isolated `pi` sub-agent with its own system prompt and tool
  allowlist over one shared workspace: only the coder writes or runs commands,
  the reviewers are read-only, and the planner's reply is saved as `TODO.md` by
  the tool, so a plan is always persisted. Light prerequisite guards require a
  `TODO.md` before `review_plan`/`code`. For a multi-phase task the runner
  drives one phase at a time — this model cannot bound its own reasoning
  (`supportsReasoningEffort: false`), so a small per-phase task keeps each call
  finishing — with a retry wrapper that re-invokes a stalled orchestrator from
  the shared workspace, and a live feed of each sub-agent's steps. It reuses the
  feed and scoring helpers from `learn/code/loop_run.py`, the external-loop
  runner. Measured: the easy and medium suites pass (visible and hidden grader),
  fully model-driven.

- A `mellum-nonblock` extension (`extensions/mellum-nonblock.ts`): a bash
  command that starts a server (uvicorn, `app.py`, `flask run`, a dev server …)
  blocks forever and would hang a workflow stage until its timeout. The
  extension rewrites such a command to run threaded in the background, captures
  its output and feeds it back, so the stage keeps moving. Loaded only on the
  coder — the one phase that runs commands.

- A `mellum-loop` orchestration core (`extensions/mellum-loop.ts`): the state
  machine for a variable-extension **workflow** loop with two review gates —
  **planning → plan_review → coding → code_review → testing**. A too-complicated
  plan routes back to planning (stabilise the plan early); a failing code review
  or a broken test routes back to **coding** (iterate the code, don't re-plan
  every failure); a repeated broken test runs a **rubber-duck** step (reason it
  out, amend `TODO.md`) before coding again; all bounded by a round budget.
  Each workflow is a separate Pi invocation (`pi -p --no-extensions -e … --thinking
  <level>`) with its own minimal extension set and thinking budget — only coding
  carries the guards, planning/review think light — so the orchestrator replaces
  the plan and verify gates (fewer extensions, order enforced by the runner, not
  a block the model can wait out). Pure core; the Pi-invoking runner builds on it.

- A `mellum-acceptance` extension (`extensions/mellum-acceptance.ts`): Tier-1
  dynamic mediation. It derives a structural acceptance test straight from the
  task spec — the app module and every route the spec names — and writes a
  pytest the `mellum-ncm` gate can enforce (`NCM_TEST`), with no per-task
  authoring. It checks the app boots and that each named route is registered
  (path params normalised). For a GET route the spec describes as a rendered
  page it also checks the response — 200, HTML, and the page-layout hygiene the
  spec states in the open (HTML5 doctype, `lang`, a navbar/links) plus any
  tagline the spec quotes — so it catches the home-page miss, not just a missing
  route. It catches the early failures (nothing built, a missing route, the
  wrong module); deep contracts (exact aggregation keys, a migration schema)
  are Tier-2 (an examiner model), not structurally inferable.

- A `mellum-surgical` extension (`extensions/mellum-surgical.ts`): block a
  `write` that would clobber an existing file. On a write onto a file that
  already exists it measures churn (the fraction of lines changed — the clobber
  signal) and growth (a duplicated copy) against the current content and blocks
  a regeneration, steering the worker to `edit` the targeted change; a write to
  a new file is always allowed. Churn is the detector; growth stays generous so
  a legitimate addition (a new route or field) is never mistaken for a rewrite.
  Caps tune with `MELLUM_SURGICAL`; load with `-e extensions/mellum-surgical.ts`.
  Measured incidence on the current model is low (Pi's `edit` anchors reliably),
  so this is a cheap safety net, not a hot path.

- A `mellum-plan` extension (`extensions/mellum-plan.ts`): plan before you code —
  gather information, write a `TODO.md` of every step to satisfy the whole spec,
  follow it checking each step off, and on a test failure amend the `TODO.md` and
  go round again until green ("fail to plan, plan to fail"). It gates on the
  concrete `TODO.md` **artifact**, not a flaky text turn: the first source
  `edit`/`write` is blocked until a non-empty `TODO.md` exists (writing the
  `TODO.md` itself is always allowed; reads/greps/shell never gated); once it
  exists, the worker is free to implement and follow it. Applies even to simple
  tasks — a plan curbs flailing. BOUNDED: it fails open after `max` blocks
  (default 2) so it can never deadlock the build. Pairs with `mellum-ncm` for the
  re-run-until-green pressure. Load with `-e extensions/mellum-plan.ts`; tune with
  `MELLUM_PLAN` (e.g. `{"max":1}`, or `{"max":0}` to disable).

- A `mellum-quality` extension (`extensions/mellum-quality.ts`): at
  `agent_before_settle` it runs `ruff --select F,E9` over the worker's own
  changes and, when a real error remains — a shadowed redefinition (F811), an
  undefined name (F821), an unused import (F401) or a syntax error — hands it
  back with one bounded nudge to fix before finishing. Real-error classes only,
  never style, so a working solution is never failed on cosmetics; it degrades
  to silence when ruff cannot run. Load it with `-e extensions/mellum-quality.ts`
  and tune it with `MELLUM_QUALITY` (JSON, e.g. `{"max":1,"select":"F"}`).

- A **strip-thinking seam** in the worker, so lesson 3's claim can be measured at
  all: `MELLUM_STRIP_THINKING=1` drops earlier assistant reasoning from the
  payload, the harness runs it as `--arm strip-thinking`, and `run.json` carries
  `strip_thinking`. It replaces only `reasoning_content`/`reasoning` and leaves
  content, tool calls and tool messages untouched, which a test pins both ways —
  the default stays as shipped, because A12 found stripping made runs 60% slower.

- The **Pathologies page**, `learn/pathologies.md`: thirteen named failure
  modes in four sections, each with a plain one-sentence statement of the
  problem, the record that shows it, and the shape that answers it. Harvested
  for form from the sibling `swiftstar` and `ds4-engine` catalogues — an entry
  needs an observation, and the list is a reference, not a rate — and it carries
  two entries that are harness faults rather than model faults, because a
  harness fault that reads as a model fault is the misfiling worth avoiding. The
  ditch's placeholder link now points at it.

- Lesson 9, **The intercom block is a prefill tax**, as a rationale: the
  delegated mechanism it measured was removed in LC.8, so the page argues from
  the removal and from the handoff block that replaced it — one summary per
  finished span, never a transcript per turn — with `conjecture` badges and no
  restated percentage.

- The **foreground-server guard** is on `main` but dormant upstream (this fork
  enables it by default): it refuses a `bash`
  call that starts a server in the foreground and points at the in-process
  `TestClient` form or a detached `nohup … &`. Its pattern now covers
  `python app.py` and `uv run python scripts/serve.py`, the shapes LC.19's first
  attempt actually hung on, and read-only or backgrounded commands still pass.
  It stays off until an arm measures it: `--arm server-guard` and
  `--arm no-facts-guard` run it with or without the facts bullet, and a run
  record now counts `guard_blocks` — a blocked call never reaches the recorder,
  so the count is taken from the refusal the model was told about.

- Lesson 10, **One spec file per phase**. Written from a preregistered
  `joined`-against-`split` arm on the medium suite: the spec's acceptance
  criteria took a worker from a workspace no check could import to 1 of 18
  checks missing, and the layout of the spec did not separate the arms at n = 3
  — a null, stated as one, with the old ladder claim retired.

- A run whose hidden checks never executed now says so. When pytest stops on a
  collection error — usually a module the workspace lacks — `run.json` carries
  `checks_ran: false` beside the count, because "18 checks failed" and "the
  checks never ran" are different findings. It is still a failure; the record
  just stops hiding why.

- The harness records more than a count when a session fails its hidden checks:
  `run.json` now carries `missing_checks`, the expected test IDs that did not
  pass, and `check_groups`, the same tally per grader module. A suite whose
  graders are one file per phase can now be read phase by phase, where passes
  alone floors.

- `--specs joined|split` runs a suite with one of its spec variants: the same
  project and requirements, laid out as one joined `specs/roadmap.md` or as one
  file per phase, with thin briefs that point at whichever applies. The run
  record carries `specs`, and without the flag a suite runs exactly as shipped.
  `medium` ships `joined` and `split`; the Getting Started pages and the
  glossary describe both.

### Removed

- Lesson E4 Running Commands left the lesson track: its lesson check did not
  hold twice on the 6-bit reference model, which backgrounded its own server
  starts without the guard. Too Many Tools is now E4 and Know When to Stop E5.
  `guard/block-foreground-server` stays in the remedies list, and its
  challenge, `learn/challenges/running-commands/`, stays and still qualifies.

- Lessons H1 Who Drives and H2 The Handoff left the lesson track: who drives
  is a role, not a unit, and the handoff block ships inside the worker with
  no arm. Who drives now opens the Hard index; the handoff block is a backlog
  entry; both pages' evidence is in the same dated research note.

- Lessons M5 Thinking Is Working Memory, M9 One Spec per Phase and M10 Steps,
  Not One Brief left the lesson track: their remedies were harness arms or
  flags, not units a learner can apply. Their evidence is in a dated research
  note; the pathologies page gains "Thinking spends the answer budget", and
  the backlog gains "A unit that shapes the task in a session".

- Lesson M1 Build a Harness moved to Getting Started as "The Harness", step
  4: it builds the instrument every lesson measures with, rather than
  applying a remedy, so it is setup, not a lesson.

- Lesson E2 Read the Failure folded into S0 Start Here, as its "Reading a
  real failure" section with the same reading order and the nine-session
  evidence: it taught a habit, not a remedy, so it could not show a FAIL
  turning into a PASS of its own.

- Lesson E1 The Ditch left the lesson track: it shows a failure but applies
  no remedy, so it has no FAIL turning into a PASS, which every lesson now
  must. Its session evidence is kept in a dated research note that the
  pathologies page cites for false success and fabricated evidence.

- The ladder's dead **delegated** reporting: `parse_parent_json` analysed a
  `subagent` tool call that no shipped worker can make, the run record carried
  a `parent` that was always `None`, and the results table had two columns
  (`deleg`, `brief_chars`) that were therefore always empty. Left over from
  LC.8's retirement of the delegated child.

- Lesson 7, **Who holds the loop**, from the Lessons track. It compared worker,
  Mode and a delegated child; LC.8 renamed Mode to Worker and removed the
  delegated child, so there is no second policy left to compare. The index keeps
  the number so the other entries and the roadmap rows stay stable.

### Fixed

- Two Getting Started pages still called the ladder the measuring instrument a
  cycle after `reference-run` moved to the suites, and the suite page told the
  learner that findings lessons cite `evals/`, which lesson pages may not
  link. The harness and suite pages now name the suites as the instrument and a
  preregistered record in `docs/superpowers/research/` as the citation.

- `learn/project/index.md` named `extensions/mellum-mode.ts` and the retired
  `templates/` agent files, two cycles after LC.8 renamed the former and
  removed the latter.

### Changed

- Getting Started is setup only: Base Pi on llama.cpp, a new Working With Pi
  step (tools, sessions, slash commands, project trust, `/lesson` and
  `/remedy`), the suites, Extensions and Remedy Units, and Troubleshoot. It
  ends with two paths: take the lessons from S0, or go straight to The
  Challenge, which now shows how to start from bare Pi or from a preset. The
  Ditch is now lesson E1 and runs in an empty folder outside the repository;
  the mini harness is lesson M1. Easy lessons are E1 to E7 and Medium M1 to
  M10. Lesson commands no longer carry `--arm bare`, the harness default.

- The project now lives at `andrevanzuydam/mellum-worker`. Install with
  `pi install git:github.com/andrevanzuydam/mellum-worker@v0.1.8`; the
  package's `repository`, the setup skill's install path, the site's GitHub
  link and its links to the README, AGENTS and research notes point there, and
  new raw-evidence releases are published there. Earlier `research-*`
  releases stay on `pauleveritt/mellum-worker`, where their files are.

- The lessons are a tiered track, one remedy per lesson. Easy (E1 to E6)
  introduces Pi's tools from bare Pi, one failure and one remedy unit each;
  Medium (M1 to M9) starts from `preset:easy`; Hard (H1 to H8) is the
  orchestration paradigm from `preset:medium` and ends with building your own
  tool and remedy. Every lesson shows a before and an after `--remedy` line,
  has a new illustration, and says its lesson check is not built yet until
  its own challenge has shown FAIL then PASS. The remedies list now appears
  on the Lessons index and The Challenge. Old lesson URLs changed.

- The Learning Center is ready to read: every page was proofread and has no
  em dashes; page titles and menus are Title Case and section headings sentence case; Getting started is five numbered
  steps (not "lessons"); the glossary is grouped into sections; Home, the
  Introduction and Pathologies have side menus; About sits last with Project,
  the lesson template and Credits under it; Paul is credited first; and the
  Tina4 link goes to tina4.com.

- The Lessons section is now three tiers that rise in level — Easy, Medium and
  Hard (orchestration and advanced concepts) — each in its own folder with a
  landing page of lesson cards. Every lesson keeps Paul's six evidence steps
  and gains a standard frame: a number (E1, M2, H1…), reading and run time, an
  Overview box with questions and objectives, a Run it yourself command, and a
  Key points box. Old lesson URLs redirect, the overview maps old numbers to
  new, and the site gains top tabs, instant navigation, a light/dark toggle
  and copy buttons on code.

- Lesson 8, **A prose brief stops at its first reply**, now rests on six
  sessions at n = 3 per arm instead of one each — and the finding flipped again:
  all three joined-brief sessions finished faster and cheaper and left a project
  the checks could not import, while all three stepped sessions produced a
  runnable project. The one-session screen that had the joined arm passing is
  retired with the original claim.

- Closing a feature cycle now names two habits: a glossary entry for any concept
  the cycle introduced, and a Pathologies entry for any failure shape its
  evidence showed — or nothing, if it showed none, because an entry without an
  observation is a hypothesis. Both are in `docs/sdd.md`'s closing list and
  `AGENTS.md`.

- The medium suite's specs now carry the acceptance criteria its hidden checks
  read — the file layout (`app.py`, `models.py`, `templates/`, `tests/`), the
  markup conventions, and each phase's criteria — so a brief that points at the
  spec asks for what is graded. Two LC.19 attempts hung, then a third completed
  every phase and scored 18/18 for a reason the spec never mentioned: nothing
  had asked for `models.py`.

- The medium suite no longer leaves verification to chance. Its roadmap asks for
  the home page to be exercised in process with `TestClient` as well as for a
  runnable `app.py`, the base project ships `tests/test_home.py` so the promised
  test command has something to run on the first turn, and both spec variants'
  briefs end by naming the loop: check with `uv run --frozen python -m pytest
  tests`, not by starting a server. Two LC.19 attempts hung on a foreground
  server before these were in place. The visible test is the worker's loop, not
  a gate — `known-broken` passes it, and the hidden grader still fails it.

- All seven older lessons now open the way Lesson 1 does: two sentences
  between the title and the first heading, the problem then the answer, 45
  words or fewer. The rule is in `learn/lesson-template.md` and is now held by
  `tests/learn-site.test.mjs` for every lesson page. Wording only — no page's
  evidence, badges or numbers changed.

- Lesson 1, "The primary agent is the wrong worker", now opens with a
  two-sentence summary, names the pathology before the measurement, says
  which three decisions leave the model's hands instead of advising against
  a role, and stops claiming every medium session was killed at 600 s. Its
  preregistered easy and medium run came back null on both suites — 1/3
  against 1/3 and 0/3 against 0/3 — so the page argues from the cost of
  failing, not from a pass rate, and the baseline's medium 2/3 against 0/3 is
  recorded as not reproduced.

- `reference-run` is earned on the suites now, not on `ladder/`: the badge
  names a preregistration, a record in `docs/superpowers/research/` and a
  `research-*` release. `ladder/` and `evals/` stay as the internal
  instrument and the A0–A21 archive.

- The Learning Center builds from the project virtualenv: `zensical` and
  `zensical-glossary` are `dev` dependencies in `pyproject.toml`, and the
  README, the toolchain page and CI all use `uv run zensical build` instead of
  `uvx --with zensical-glossary zensical build`. `uvx` supplied the extension
  only to the process it launched, so `zensical serve` — which re-launches a
  reload worker with the same interpreter — died with `No module named
  'zensical_glossary'`. `uv run zensical serve` now previews the site.

- The Lessons track is re-based on llama.cpp. `primary-agent`, `short-prompt`,
  `thinking-working-memory` and `guards-for-empty-turns` no longer cite oMLX
  ladder records: lesson 1 retires its 8/15 because an unbounded Pi passed a
  session, lesson 2 is a null at n=3, lesson 4 is a void arm (the nudge never
  fired), and lesson 3 states that the strip-thinking arm has no instrument
  on this backend.

- The suites harness counts a **nudge** only when an empty assistant turn is
  continued inside the same Pi process. Medium and hard start one process per
  prompt, and the old rule counted the empty final that ended one prompt as
  continued by the next prompt's request, inflating the column on exactly the
  suites where it matters.

- The roadmap's vocabulary now separates the two things it used to call a
  "phase": **`LC` is the phase**, and **each row is a feature cycle** that runs
  brainstorm → spec → plan → execute → close. A feature cycle delivers one
  lesson, or says in its Ships cell that it is housekeeping or infrastructure.
  Plan front matter gains `feature_cycle:` beside `phase:` and `cycle:`;
  archived plans are unchanged.

### Added

- The suites harness records **which machine and which deadline** produced a
  run (`machine`, `deadline` in `run.json`). Peak token counts transfer between
  machines and walls do not, so a record that names neither invites a
  comparison nobody can make.

- `--single-prompt` sends a suite's own prompts as one brief instead of steps,
  so "one prose brief" and "the same brief as steps" differ by exactly one
  thing: the base, the grader and the brief text stay identical.

- Lesson 8, **[A prose brief stops at its first reply](learn/lessons/prose-brief.md)**:
  a screen at n = 1 where both shapes passed the hidden tests and the
  one-brief arm used a third of the context — against the claim the lesson used
  to make, which is retired.

- The suites harness **sweeps what a run leaves running**. A child that
  backgrounds `python app.py &` and then settles used to leave its server
  holding a port — five such processes were still listening hours later. The
  sweep ends the run's process group, falls back to per-pid signals when the
  group refuses, and records what it found as `leaked` in `run.json`.

- A **file-set check** in the suites harness: each suite declares `allow` and
  `ignore` globs in `layout.json`, the run's workspace is hashed before and
  after the child, and anything created or modified outside the layout is
  reported as `out_of_layout` in `run.json`. A run can pass every hidden test
  and still leave the project as it did not ask.

- Lesson 6, **[Write only the files you list](learn/lessons/write-only-listed.md)**:
  the check on three easy sessions, where no session wrote outside the layout.

- Lesson 5, **[Project facts](learn/lessons/project-facts.md)**: the facts arm
  measured on llama.cpp, where the block reaches the model on every request
  and did not move the easy suite at n=3. The page states the null with the
  injection count beside it, and carries the foreground-server observation as
  a lead attributed to the Pathologies page.

- The suites harness records **attempted compaction** as a `before_compact`
  trace row, and a `no-facts` arm sets `MELLUM_MODE_FACTS=0`; the harness now
  clears all four arm knobs from the inherited environment first, so an
  exported value cannot quietly make two arms the same policy. A refused
  compaction is only visible with the recorder loaded before the worker,
  which costs payload fidelity — that split is backlogged.

- The preregistration and record for the **context-budget** arm:
  [`2026-10-24-context-budget-preregistration.md`](docs/superpowers/research/2026-10-24-context-budget-preregistration.md)
  and its [record](docs/superpowers/research/2026-10-24-context-budget-screen.md).
  The arm is void — peak demand of 857–4,699 tokens never approached either
  window — but it fixes the shipped 50,000 wherever a lesson quotes easy.

- The preregistration and record for the **project facts** arm:
  [`2026-10-24-project-facts-preregistration.md`](docs/superpowers/research/2026-10-24-project-facts-preregistration.md)
  and its [record](docs/superpowers/research/2026-10-24-project-facts-screen.md).
  Passes are null at n=3, the block injects in every `worker` request, and the
  record carries the lead that all three `no-facts` sessions hung on a
  foreground server once the `Do not: start servers` bullet was gone.

- The suites harness now reports **nudge fires** beside the passes: it counts
  an empty assistant turn that was followed by another request as a nudge and
  one that ended the run as an empty final, printing them on the score line and
  as a `Nudges` column in the evidence table. The lesson template requires the
  fire count in Quality and budget, because a guard whose fires are invisible
  cannot be told from a guard with nothing to do.

- The preregistration for the first arm of the Lessons re-base:
  [`2026-10-24-nudge-llamacpp-preregistration.md`](docs/superpowers/research/2026-10-24-nudge-llamacpp-preregistration.md)
  fixes the arms (worker against no-nudge), n = 5, the easy→medium→hard
  staircase and four decision rules before any run.

- Paul's finding **Guards for empty turns and loops**: with the guard
  extension loaded A0 passed 15/15, and without it A1 passed 13/15 on the
  same oMLX rungs, where both failures are an empty final the bounded nudge
  answers. The lesson quotes the shipped nudge, keeps the claim to one
  benchmark, and names the open llama.cpp arm.

- Paul's finding **Thinking is working memory**: stripping earlier turns'
  `reasoning_content` cut prefill 57% and made the runs slower, on the cited
  oMLX A3/A12 records. The lesson keeps the thinking in history, names the
  open llama.cpp re-run, and adds `working memory` to the glossary.

- Three prospective Pathologies lessons: **The runaway search**, with links to
  the confinement guard and tests in PR #1; **The server that never returns**,
  from prompt v10 and the dormant foreground-server guard; and **The rule it
  knew and skipped**, from prompt v11's clause-by-clause self-check. The
  worker-extension lesson now warns against machine-wide searches and points at
  the confinement proposal.

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

- The Lessons index is one recommended list of twenty-three, each with a one-line
  description and an italic author tag, *(Paul)* or *(Andre)*. It now follows
  the roadmap order, so "Guards for empty turns and loops" is lesson 4 rather
  than 11, and says which entries are scheduled and which are deferred
  candidates.
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

- A **foreground-server guard** in `extensions/mellum-guards.ts` (on with
  `--guards`): blocks a bash command that would start a server in the foreground
  (`uvicorn`, `gunicorn`, `flask run`, `python -m http.server`, `manage.py
  runserver`, `npm start`, …) and tells the worker to use `TestClient` in
  process, or to start it detached (`nohup … & echo $!`) so it returns at once
  with a pid to kill later. Reads/searches that merely mention a server
  (`grep uvicorn`, `cat app.py`) and already-backgrounded commands are allowed.
  The enforcement behind prompt v10.

- Ladder rungs 10–12 (AgentClinic phases 5–7): rung 10 Archive & Audit (with a
  destructive-archive decoy off the write-list), rung 11 reporting over a
  pre-filled database (with an archived-but-open trap row), rung 12 summing two
  columns of a file far larger than the context window (must be streamed). Each
  is scored by the hidden cumulative oracle plus a committed frozen acceptance
  test. The 6-bit clears all three 3/3 mediated — recorded in
  `evals/2026-10-21-rungs-10-12-6bit/`.

- `extensions/mellum-override.ts` — edit the system prompt the worker is fed,
  live, from a file (`$MELLUM_PROMPT_OVERRIDE`): `system` replaces it, `append`
  adds to it, applied at the next turn boundary. The dashboard writes the file,
  so you can change the prompt while a run is in flight. Self-contained; pure
  core unit-tested.

- Dashboard upgrades (`dashboard/`): click a rung to drill into its **past runs
  and summaries** (verdict, the task sentence, the diff, wall time); an
  **intelligence centre** panel that shows the told-vs-truth contradictions
  `mellum-rethink` finds; a **system-prompt editor** that saves an override the
  worker picks up next turn (via `mellum-override`); the prompt panel now shows
  the **full context** being fed, not a teaser; and the rung grid is
  data-driven over rungs 1–12, so a rung is shown as idle rather than hidden
  when it has no result. `serve.py` gains `/rung`, `/override` (GET + POST)
  endpoints and an `intel` feed, all dependency-free stdlib.

- `extensions/mellum-vision.ts` — let the worker see: describe images and
  screenshots, or read the text out of them, with a small local vision model
  (JetBrains ships none — Mellum is code and text only). Default
  `empero-ai/Qwen3.8-2B-Distill` (~2 B, a Qwen3.5 VLM) served through MLX; the
  model id is a Hugging Face repo id, so `mlx_vlm` downloads it automatically on
  first use when missing (set `MELLUM_VISION_MODEL` to a local 4-bit copy for a
  smaller, faster load). Its partner is `mellum-files`: a
  scanned/image-only page routes here. Descriptions are indexed into
  `mellum-context`. Command `/see <image> [question]` and a `describe_image`
  tool. Config: `MELLUM_VISION_MODEL`, `MELLUM_VISION_PYTHON`. Pure core
  unit-tested; verified end-to-end against the local model.

- `extensions/mellum-files.ts` — document understanding for PDF, Word (.docx)
  and Excel (.xlsx), plus plain text. Office files are read with a small
  pure-Node zip reader (the central directory, so Office's streamed files work)
  and `node:zlib`; PDF text is pulled best-effort from the page content streams
  (FlateDecode inflated, text operators read). No npm dependency and no external
  tool. Extracted text is indexed into the `mellum-context` store so a large
  document becomes searchable context. A scanned, image-only PDF has no text to
  pull — that routes to `mellum-vision`. Command `/read-file <path>` and a
  model-callable `read_document` tool. Self-contained; pure core unit-tested.

- `extensions/mellum-rethink.ts` — a skeptical "stop and pause, rethink" gate.
  It parses the claims a human makes in the task (the tests already pass, a file
  was already changed), checks the cheap, checkable ones against ground truth
  (does the acceptance test actually pass, did the file actually change), and
  when a claim contradicts reality it pushes the worker back at settle — a note
  naming the contradiction, asking it to re-examine rather than encode a false
  premise. Each contradiction is also written to the feed (kind `rethink`) for
  the dashboard. Config: `RETHINK_TEST`, `RETHINK_PYTEST`. Self-contained
  (Node + Pi hooks); pure core unit-tested.

- `extensions/mellum-context.ts` — context intelligence over a local SQLite
  FTS5 index (built-in `node:sqlite`, no npm dep). It chunks files into
  overlapping line windows, ranks passages by BM25 with a recency boost
  (temporal ranking), and can return them in chronological order (temporal
  sequencing) so the worker applies context in the order it happened. Large
  code and large data are leaned on through the index — the worker searches for
  the few relevant lines instead of loading the whole file into the prompt.
  Commands `/index <path>` and `/context <query>`, plus a model-callable
  `context_search` tool where Pi supports it. Config: `MELLUM_CONTEXT_DB`,
  `MELLUM_CONTEXT_HALFLIFE_MS`. Self-contained (Node + Pi hooks); pure core unit-tested.

- A live worker observability + control set (agnostic Pi extensions, loaded with
  Pi's `-e`, each self-contained — Node + Pi hooks, no framework coupling):
  `extensions/mellum-feed.ts` emits an NDJSON feed of the worker's turns, tool
  calls and the prompts it was sent; `extensions/mellum-replay.ts` adds a
  `/replay <adjustment>` that re-sends the last captured prompt to the model
  with a slight system-prompt tweak; `extensions/mellum-control.ts` holds the
  worker at the turn boundary while paused and resumes on play. A local
  `dashboard/` (a dependency-free `serve.py` relay over SSE + a reactive page)
  shows the rung grid, the prompts fed to the model, and the live feed. Pure
  cores are unit-tested; the live Pi-driving is verified separately.

- `extensions/mellum-ncm.ts` — a next-concept-modelling verify gate, loaded
  with Pi's `-e` (not shipped by default). At settle it re-runs the named
  acceptance test and, while it is red, sends the worker back naming the **unmet
  concepts** (the failing test functions), up to `NCM_MAX`. It brings the
  ladder's direct-only verify/re-dispatch into any Pi session — Mellum Mode
  included — at the concept grain, reusing the `agent_before_settle -> continue`
  pattern from the empty-final nudge; self-contained (Node + Pi hooks, no
  Pi-internal imports). Config: `NCM_TEST`, `NCM_MAX` (default 5), `NCM_PYTEST`.

- `evals/2026-10-20-mediated-6-9-v7/` records the measured pass: Mellum on
  AgentClinic rungs 6–9, n=3, mediated (frozen phase tests) with the v7 prompt +
  focused command + trimmed tools + fail-fast ramp — **12/12**, rung 9 (the
  phase-4 wall, best-ever 2/3) now **3/3**, clearing the historical 9/12 ceiling.
  Note:
  [`research/2026-10-20-mediated-6-9-v7.md`](docs/superpowers/research/2026-10-20-mediated-6-9-v7.md).

- `extensions/content-tool-call-assist/` — a Pi extension that lets a small open
  model drive the loop when it emits its tool call in the message content (a
  fenced JSON `{"tool","args"}`/`{"name","arguments"}` block, or a Hermes/Qwen
  `<function=…>` XML block) instead of the structured `tool_calls` field. It
  promotes the content call into a real one, gated on the real tool names and a
  present arguments key so model data (e.g. a cart item `{"name":"Widget A"}`)
  is never mistaken for a call. `ASSIST_FORCE_TOOLS=1` adds a nudge and a
  seed/temperature retry; `ASSIST_BASE_URL`/`ASSIST_MODEL_ID` point it at any
  OpenAI-compatible server. `scripts/patch-pi.sh [PI_DIR]` installs it into a Pi
  checkout (its imports resolve only there); load it with Pi's `-e`.

- `EXAMPLE.md`: a worked, example-driven guide to using Mellum — one-shot
  `/mellum`, multi-task spans, handing it a failing test (the reliable pattern),
  project facts, `/mellum check`/`last`, and measuring via the ladder's mlx-lm
  backend.

- `LESSONS.md`: 100 lessons from the small-model-as-worker effort (plus a dated
  addendum), and
  `docs/superpowers/research/2026-10-19-small-model-tool-presentation.md`
  recording a negative result — stripping a model's native tool field regresses
  tool-calling (fix the chat template's line feeds instead).

### Changed

- A mediated direct run (`--acceptance-test`) gives the worker five tools,
  `read, ls, bash, edit, write`, and verifies with a focused `pytest
  tests/<the-test>`: offline, `grep`/`find` shell out to the missing `fd`/`rg`,
  and under v6 the whole-directory command sent the worker chasing unrelated
  tests (a 93-turn spin on rung 6). An unmediated direct run keeps the measured
  seven tools.
- `--redispatch` varies the sampling on each retry instead of re-running the same
  greedy decode: the temperature grows by `--redispatch-temperature-step`
  (default 0.25) up to `--redispatch-temperature-cap` (default 0.5) and the seed
  moves with the attempt, so retries diverge without going hot (a 0→1.0 ramp ran
  44 tool errors in 121 requests). A timed-out attempt also re-dispatches. The
  ramp is unmeasured; nothing yet shows a retry passing because of it.

- The five flow role prompts are rewritten as one plan → examine → code → test pipeline: each
  names its step and hand-off, file paths are consistent (`plan/TASK.md`, `plan/TODO.md`,
  `plan/REVIEW.md`, `tests/test_gate_phase_*.py`), and reviewers share one PASS/REDO shape. It
  removes a contradiction left from before the examiner: the planner had told the coder to write
  the pytest file, which is now the examiner's job.

- The Learning Center's terminology lives in the glossary: the short-lived
  `learn/introduction/terminology.md` page was folded into `learn/glossary.md`, so every term
  links to one definition.

- The flow harness's self-written acceptance tests now **accumulate across phases**
  instead of being overwritten each phase. The examiner freezes each phase's test
  under `.mellum_gate/phase_<n>.py`, and both the `test` tool and the runner restore
  the WHOLE frozen set into `tests/` (as `test_gate_phase_*.py`) before scoring — so
  every earlier phase is re-run and a later phase can no longer pass by silently
  regressing an earlier one. The examiner prompt is stricter too: it enumerates every
  requirement for its phase and must assert the negative and edge cases (missing or
  invalid input, empty, unauthorized, not-found, duplicates, exact error status and
  message), not only the happy path; the coder is pointed at the cumulative gate and
  told earlier phases must keep passing. This closes the visible-pass / hidden-grader
  gap that came from each phase only being checked while it was the current one. The
  worker still writes its own tests from the spec — nothing is injected or hand-authored.

- The eval harness runs suites easiest-first (`easy`, `medium`, `hard`) rather
  than alphabetical, so a slow hard suite never blocks the quicker ones;
  unknown suites keep alphabetical order after the known tiers.

- `mellum-ncm` gains a whole-suite verify mode: set `NCM_ALL=1` to run the
  entire visible test suite at settle and refuse "done" until it is green — the
  agnostic developer-loop gate (the worker isn't done until it has run the whole
  thing and seen it pass), beside the existing named acceptance test (`NCM_TEST`,
  mediation). Adds a `verifyCommand` helper; the gate is inert unless `NCM_TEST`
  or `NCM_ALL` is set.

### Changed

- The Lessons index now marks the context/input workflows as INT.3
  Intermediate candidates, and every scheduled lesson row links to the new
  PR harvest index. The index joins the PR digests, prompt triage and source
  map; it adds no run.

- The lesson template now separates quality from budget in Validation and
  asks what to try next in Interpretation: a lesson must say which passes
  moved, which budget column paid for them, and which screen would improve
  the weaker side. The Thinking lesson carries both analyses.

- Lesson tests moved out of the shared suite into
  `tests/lesson-<slug>.test.mjs`, and the site-wide test now discovers lesson
  pages automatically, so parallel lesson branches no longer collide in
  `tests/learn-site.test.mjs`. The lesson template records the convention,
  including pinned code links and no copied production source.

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

- Worker prompt v7 → v11, hardenings against "self-certifying against a subset".
  Each was found by reading what the worker actually ran; the passes cited are ladder
  screens (n = 1 to 3) with no `evals/` record yet:
  - **v8 (run the whole test file):** the "how to check" step now tells the
    worker to run the whole named test file (e.g. `pytest -v test_export.py`) and
    pass every test in it, never a single `::test_function`, and not to stop after
    one test passes. Fixes the self-narrowing that failed rungs 4/5 (bare
    un-mediated ladder 6/12 → 11/12).
  - **v9 (implement the whole spec):** the "what to build" step now says the spec
    is the full contract — implement every requirement, such as automatically
    assigned unique ids, defaults and status rules, even when no visible test
    checks it. Fixes rung 9's Phase-4 id miss (the worker passed every visible
    test but left `id = 0`, which only the hidden oracle caught).
  - **v10 (never start a server):** the check step now says never start a server
    (`uvicorn`, `flask run`, `http.server`, the app) — it blocks forever and
    burns the time budget — and to exercise an endpoint in process with
    `TestClient` the way the tests do. Fixes a rung-9 deadline failure where the
    worker ran `uvicorn app:app` and hung until the deadline.
  - **v11 (verify against the spec before finishing):** a final self-check step —
    re-read the spec clause by clause and confirm the code meets each one, above
    all a data-model rule the visible tests do not exercise ("assigned
    automatically" means the constructor sets the id from a counter, never
    `None`/`0`). This closed rung 9's probabilistic id miss: with v11 (plus the
    server guard) the bare 6-bit reached **rung 9 = 3/3** un-mediated.
  - The run recorder's prompt-version marker tracks v11.

- Worker prompt **v7** specializes to the "make one failing test pass" shape:
  read the named test *and* any spec it references, create the module the test
  imports if missing, run *only* the named test, never edit that test or add
  other test files. This is Mellum's best-measured usage (see the 2026-10-20
  record) — narrower than v6's general guidance. The v6 keep-every-test guardrail folds in.

- Worker prompt v6 adds a keep-every-existing-test guardrail (add new tests
  alongside the existing ones; change only what the task requires). It is
  spec-aligned guidance; on a 2B model it showed no measured lift (the model
  ignores it) and no regression — see the 2026-10-19 research note — so it is
  kept as guidance for more capable workers, not as a measured improvement.

### Fixed

- `scripts/screen.sh`, `scripts/product.sh` and the dashboard's Start button work
  again: the 2026-10-22 upstream merge had dropped the ladder flags they call
  (`--acceptance-test`, `--redispatch`, `--effort-ramp`, `--pi-extension`). The
  flags are restored on the current runner, with oMLX selected by `--model
  omlx/<id>` in place of the earlier `--model-id`.
- `--effort-ramp` no longer crashes with `ProfileMismatch`: the effective-params
  check is skipped while the ramp owns `max_tokens`.
- The re-dispatch retry message carries the real test failure: it runs `pytest -q
  -p no:warnings --tb=short` and sends the FAILURES section instead of a tail of
  deprecation warnings.

- `flow_run` no longer crashes when an early phase fails: the forward-context line read the
  last passed phase as `done[-1]`, which raised `IndexError` when phase 1 had failed and ended
  the whole run. It now says no phase has passed yet and moves on to the next phase.

- The flow orchestrator no longer loops plan → review_plan → REDO forever. Review gating was
  fail-closed (pass only on an exact `REVIEW: PASS`), and a thinking-model reviewer rambles or
  truncates before writing it, so every review read as REDO and no gate was ever written.
  Reviews now fail open: only an explicit `REVIEW: REDO` loops back. They are advisory; the
  examiner's frozen gate and the hidden grader are the real checks.

- The flow examiner prompt was compressed (~4650 to ~2560 chars) without dropping any rule. Each
  anti-brittleness rule added earlier had lengthened it, and because this thinking model's reasoning
  cannot be capped, the longer prompt made it over-reason and emit NOTHING even at 32000 tokens on
  the harder phases (hard phase 4's gate stopped freezing). Measured: with the leaner prompt the
  phase-5 examine finishes thinking and emits a valid 7-test file that compiles. The rewrite also
  re-states, tightly, that the client is imported from `starlette.testclient` (a first compression
  pass dropped that and the model guessed `flask.testing`).

- The flow examiner is now told to disable redirect-following ONCE on the test client
  (`TestClient(app, follow_redirects=False)`) rather than per request. The per-request rule kept
  slipping — the examiner applied it to some POSTs but forgot it on a setup POST and then asserted a
  3xx that TestClient had already followed to 200, failing a correct handler on hard phases 4 and 5.
  Setting it on the client eliminates the whole class (verified: the frozen phase-4 gate goes from 2
  failures to all-pass against the correct app). Still general — no suite-specific routes or values.

- The flow examiner is taught two more general testing-discipline rules, after a correct
  implementation failed brittle gates: (1) every request whose redirect is asserted needs
  `follow_redirects=False` (the examiner had applied it to some POSTs but not others, so TestClient
  followed the redirect and a correct handler failed), and (2) assert RELATIVE deltas, not absolute
  totals, because the tests share one in-memory store that earlier tests have already mutated. Both
  rules are stated generally, with no suite-specific routes, fields or values — the examiner still
  derives every assertion from the spec. The examiner prompt's remaining illustrative examples were
  scrubbed of suite-specific names for the same reason.

- The flow examiner is a thinking model whose reasoning cannot be capped, and on a complex phase it
  needs more than 16384 tokens just to finish thinking — so at that cap it emitted an EMPTY test
  (`finish_reason=length`, no content) and no gate froze. The hard "Archive & Audit" phase stalled
  on exactly this. The examiner's `max_tokens` is raised to 32000 (measured: it then finishes
  thinking and emits the full test), and `bestPytest` now salvages the test from any assistant
  block when the examiner ends on verifying chatter rather than the test itself.

- The flow now judges a phase on the frozen acceptance gate (`tests/test_gate_phase_*.py`) alone,
  not on the coder's own scratch tests. A brittle coder test — the hard "Resolve and Reopen"
  phase's list-equality order check, polluted by shared in-memory state — was failing a build that
  passed the authoritative gate. The gate is the definition of DONE; the coder's extra tests no
  longer gate a correct, gate-passing solution.

- The examiner could freeze a self-contradictory absence check: `assert "Resolve" not in html`
  while the same test required the status "Resolved" present ("Resolve" is a substring of
  "Resolved"), so no correct app could pass — the hard "Resolve and Reopen" phase looped on it.
  The examiner is now told to target the specific control (its form `action=` URL or the exact
  button) when checking an action is gone, never a bare substring of a word the page shows.

- A dangling markdown fence in the examiner's reply (a trailing ` ``` ` with no opening fence, or
  an opening ` ```python ` with no close) survived into the frozen Python gate, so
  `phase_gate_ok`'s `compile()` rejected an otherwise-correct gate and the phase looped to
  exhaustion. The hard suite's "Resolve and Reopen" phase died this way — a lone fence on the gate's
  last line. `asCode` now strips any lone fence line as a safety net, so a fence can never reach the
  gate file.

- The flow examiner wrote redirect acceptance tests that a correct handler could never pass:
  `starlette`'s `TestClient` follows redirects by default, so a plain `client.post(...)` returns
  the final `200` page and `assert status_code == 303` fails a correct `303` handler. The medium
  suite's "Add Complaint" phase looped to exhaustion on this — the app was right, the frozen gate
  was unpassable. The examiner is now told to pass `follow_redirects=False` on the redirecting
  request before asserting the status and `Location` header.

- Removing Pi's base prompt (the `--system-prompt` fix) also removed the structure that kept the
  planner concise, so it rambled ~635s on a trivial plan and timed the fork out. Two fixes, since
  the model's reasoning can't be toggled off (neither `reasoning_effort` nor `enable_thinking` is
  honored — verified): (1) a project operating guide (`BASE_GUIDE`) is prepended to every role —
  focus, brevity ("be decisive, do not deliberate"), tool-use, output-only — replacing Pi's
  structure in our own voice, generic so it contradicts no role; (2) per-phase `max_tokens` — the
  planner and reviewers capped below examine/code (8192) — small enough to bound a runaway, large enough not to truncate a thinking model (2048 emptied the plan),
  examine and code kept generous (16384; examine later raised to 32000, below). `max_tokens` is the only lever that bounds reasoning here.
  The base prompt itself was later restored (next entry), so `BASE_GUIDE` now sits between
  Pi's base prompt and the role.

- Flow phase sub-agents keep Pi's base coding-agent prompt and append `BASE_GUIDE` and their
  role (`--append-system-prompt`). Replacing it (`--system-prompt`) was tried, because Pi's
  generic "thorough coding agent" framing diluted the tightly-scoped roles and pushed the
  examiner to over-assert; but without Pi's base prompt the planner thought without bound and
  never wrote a plan (an empty `TODO.md` even at 16384 tokens, failing every medium run), so it
  was reverted. Pi's base prompt is what keeps this model producing a final answer; the
  de-brittled examiner rules stay to offset its "be thorough" nudge.

- The flow examiner invented exact strings the spec never gave (e.g. a viewport
  `initial-scale=1.0`, exact nav markup), producing brittle gates that a correct
  implementation can't match — even the home page failed. It now asserts exact values ONLY
  where the spec is verbatim, and asserts the requirement (a viewport meta exists, a link to
  the named route is present) — not an invented string — for loosely-described requirements.

- The flow examiner under-specified identity, so a multi-phase run could pass its own gate
  while the hidden grader failed. Medium went visible=PASS / hidden=FAIL because the worker
  gave `Complaint` no stable `id` field (resolve/reopen worked by list index), and the
  examiner never asserted identity. `examine` now requires, for any phase that acts on a
  specific record (resolve/reopen/update/delete/fetch by id), a stable explicit id FIELD on
  the model — distinct per record, addressed by id, unchanged across the mutation, no
  reordering — closing the visible/hidden gap on that class of phase.

- The flow orchestrator could loop a phase to the deadline: a rung-6 run re-ran the
  (expensive) `examine` tool 5×, `review_code` 3×, and never called `test`, burning the whole
  1200s budget on a solution it already had. `examine` now runs **once per phase** — once its
  gate is frozen, re-calls are blocked with a pointer to `code()`/`test()` — and a per-phase
  tool-call cap (`PHASE_CALL_CAP`, 16) stops the orchestrator thrashing, while always leaving
  `test` (the only exit) callable.

- The flow harness counted a phase as passed whenever pytest passed — even when the
  examiner had produced no acceptance test for that phase. A fork whose examiner output
  was dropped or malformed then inherited only the earlier phases' gate and passed
  trivially, and best-of-N (promote the first fork to pass) actively selected that
  weakest fork. On a hard run this meant phases 3–7 reported PASS while only phases 1–2
  were built. A fork now counts as passing phase N only when it froze a real acceptance
  test for N: `.mellum_gate/phase_<n>.py` must exist, compile as Python (an examiner that
  emitted an HTML/template blob is rejected) and define at least one test. The examiner
  also validates its own output, retries once on a non-pytest reply, and refuses to
  freeze a junk gate; `asCode` now prefers a ```python block over any other fenced block.

- `run_top` crashed a whole best-of-N run when reaping a child process group raised
  `PermissionError` (EPERM) — a pid recycled into a group the process no longer owns. The
  reap now ignores both `ProcessLookupError` and `PermissionError`.

- The lesson-suite grader (`learn/code/harness.py`) no longer lints the
  workspace's `.venv`. ruff's `--exclude` REPLACES its built-in excludes (which
  include `.venv`), so `grade()` was linting installed packages and failing
  every working solution on `F403` inside PyYAML. It now uses `--extend-exclude`,
  keeping ruff's default `.venv`/`__pycache__` exclusions and linting only the
  worker's own code.

### Fixed

- Getting Started now has continuous lesson-1 steps 1–7, including
  `complexipy` in the tool fetch; the troubleshooting page is in the nav,
  linked from the track index and no longer has a self-prerequisite; the home
  page links the Introduction and says five lessons; and the ditch drops its
  author notes while explaining why its recorded run is Python.

- The lesson harness uses one `F,E9` grade, excludes the workspace `.venv`,
  and runs `--suite all` easiest-first (easy, medium, hard).

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
- `evals/`: the phase records (A0 to A17 and the earlier phases:
  READMEs, tables, run records, final answers and briefs), moved in from
  the research repo. Raw traces, stdout and diffs are archived per phase
  as `research-2026-10-09` release assets, with their hashes in
  `evals/PROVENANCE.md`; they are not tracked.
  `uv run python -m ladder.archive_raw` (in `ladder/`) builds those
  tarballs. The first run from this checkout is the `smoke-m6-one-repo`
  record.
- `evals/2026-10-09-ablation-a18-agentclinic-facts-off/`: the A18 record, the
  baseline for the project-facts work. Mellum Mode on the AgentClinic
  rungs 6 to 9 with facts off, three repeats each: 1 of 12 passes under the
  added-tests-allowed rule (0 of 12 under the strict one), median 50
  requests. Its raw files are archived under the same release tag.
- `evals/2026-10-10-ablation-a19-facts-on/` and
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

- `evals/2026-10-09-ablation-a17-mode-v012/README.md`: the nudge and tool-error
  rows gave runs-with-one counts labelled as totals (A17 2 and 8); they
  now give both, totals first (A17 3 and 12, A14 7 and 13), matching each
  phase's `table.md`.
- Links to the research and the phase records now point inside this repo
  (`evals/`, `docs/superpowers/research/`) instead of the research
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
