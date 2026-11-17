# Remedy units: one role each, combined by list

Date: 2026-10-29. Status: approved by Andre on 2026-10-29.

**Dated correction 2026-10-29.** `context/keep-thinking` is not a unit:
keeping earlier reasoning is what happens when nothing strips it, so the unit
would install nothing. Thinking retention stays a worker default with its
opt-out (`MELLUM_STRIP_THINKING=1`), and M1 teaches that default. The tables
below read as written otherwise.

## Intent

Every remedy this project has built does one job, but they ship fused. Six
guards live in one file behind one JSON setting; the prompt, the facts, the
tool set and thinking retention live inside the worker's mode. A learner can
switch the whole worker on or off and nothing finer, so:

- a lesson cannot show its own remedy turning a FAIL into a PASS, because the
  remedy cannot be dropped out of the worker on its own;
- a Challenge attempt cannot add, drop or swap one remedy;
- a contributor has no small unit to copy, and no way to load their own
  extension into the Challenge harness.

This cycle splits the remedies into **units**: one role, one file, one
function that installs it, loadable alone or combined by list. The worker
becomes a named list of units. Lessons and The Challenge are rebuilt on top.

## Principles

1. **One unit, one role.** A unit installs exactly one behaviour on Pi's hooks
   and nothing else. Its test proves it installs that behaviour and no other.
2. **Combination is a list.** What runs is the list of units passed in; any
   unit can be added or dropped without touching another.
3. **No duplicated logic.** A unit wraps the existing function (for example
   `createLoopBreaker` in `mellum-guards.ts`); it never re-implements it.
4. **The measured worker does not drift.** Until phase 2's equivalence proof
   passes, `extensions/mellum-worker.ts` and `package.json` are unchanged.
5. **Agnostic.** No unit names a suite, route, table or expected value.

## Names and layout

Verb-first names that say what the unit does, grouped by how it acts. The
folder is the menu.

| Unit | Does | Wraps today |
| --- | --- | --- |
| `guard/block-foreground-server` | Refuses a command that would hang the session | `mellum-guards.ts` |
| `guard/break-repeat-loops` | Blocks the same call made over and over | `createLoopBreaker` |
| `guard/stay-in-workspace` | Keeps searches and writes inside the project | `confineSearch` |
| `guard/refuse-whole-file-rewrite` | Stops a file rewrite that changes a fragment | `newFileOnlyWrite`, `mellum-surgical.ts` |
| `guard/cap-turns` | Ends a runaway session with a reason | `createStepBudget` |
| `nudge/nudge-empty-turn` | One more turn when a turn ends empty mid-task | `createEmptyFinalNudge` |
| `context/add-project-facts` | Adds the project's test commands to the request | `mellum-facts.ts` |
| `context/use-short-prompt` | Replaces Pi's system prompt with `prompts/mellum-worker.md` | `mellum-worker.ts` |
| `context/keep-thinking` | Keeps earlier reasoning in the request | `mellum-worker.ts` (`stripReasoning` off) |
| `context/narrow-tools` | Limits the model to the seven worker tools | `WORKER_TOOLS` |
| `tool/background-long-commands` | Runs a long command threaded, returns its output | `mellum-nonblock.ts` |
| `tool/lookup-library-docs` | Looks up installed package APIs | `mellum-knowledge.ts` |
| `tool/keep-a-plan` | Writes and follows a TODO list | `mellum-plan.ts` |
| `check/check-code-quality` | Lint and type check before finishing | `mellum-quality.ts` |
| `workflow/spec-driven-flow` | Plan, frozen gates and checkpoints per phase | `mellum-flow.ts` |

Units live at `remedies/<kind>/<name>.ts`. Presets live at
`remedies/presets/<name>.json`: a JSON list of unit names. The first preset is
`baseline-worker`: the units today's worker combines. Instruments that are
not remedies (`mellum-record`, `-feed`, `-replay`, `-control`, `-check`,
`-learn`, `-last` and the rest) stay in `extensions/` unchanged.

Each unit file exports one install function and a default Pi extension that
calls it, so a unit is both importable (for presets and tests) and loadable
with `pi -e`.

## The harness

`learn/code/harness.py run` gains:

- `--remedy LIST`: comma-separated unit names or a `preset:<name>`, loaded in
  list order on top of the chosen arm (normally `bare`).
- `--extension PATH`: any Pi extension file, repeatable: a learner's own.

`run.json` records `remedies` (names) and `extensions` (path and SHA-256 of
each file), so a scorecard says exactly what ran. `--arm` keeps working
unchanged; existing lesson commands and records are not touched.

## Phase 1: units beside the worker

All units above exist, each with a test that it installs exactly its own hook
(a fake `pi` records the registrations) and that its behaviour matches the
wrapped function on the wrapped function's existing test cases. The harness
flags exist and are tested. The worker is untouched. Units whose role is only
meaningful inside the worker's mode (`context/keep-thinking` on a Pi that
does not drop reasoning) say so in their header and their test.

## Phase 2: the worker as a preset

**Dated correction 2026-10-29.** The worker is not rewired to call the units.
The units import the worker's own functions (`createLoopBreaker`,
`filterForMellum`'s `withFacts` and `narrowTools`, `factsBlock`), so no logic
is duplicated; rebuilding the mode's span, marker and handoff machinery on
units would risk the shipped product for no learner-visible gain. What phase 2
proves instead is that `preset:baseline-worker` **is** the worker: on a fresh
headless request it sends the same request as the worker's mode, and it makes
the same guard decision on every call (`tests/remedy-units.test.mjs`; both
tests shown red on a preset missing a unit). The text below is the original
plan.


`extensions/mellum-worker.ts` composes its remedies from the units instead of
calling the functions inline. The proof that nothing drifted, all required:

- **Request equivalence:** for the worker's recorded test payloads, the
  composed worker's `before_provider_request` output is byte-identical to the
  current worker's.
- **Decision equivalence:** for the guard test cases, the composed guard set
  returns the same decision for every call.
- **Suites:** `npm test` and the ladder fast suite pass unchanged.

Only then does the inline code go. Phase 2 changes no setting, prompt or
guard, so it needs no ladder run; any later change to a preset's list does.

## Lessons: a visible FAIL → PASS

A lesson teaches; it does not ask the learner to build. Each lesson adds
**one** thing and is short: the problem in a paragraph, **see it fail** (one
command), **add the remedy** (one line), **see it pass** (the same command),
and one key point. Longer evidence goes in a fold at the end.

**Dated correction 2026-10-29: the track.** The first table here bundled the
whole worker into lesson 1 and so taught nothing granular. Extensions fall in
three categories: **tools** (a capability the model calls: Pi's `read`,
`write`, `edit`, `bash`, `ls`, `find`, `grep`; ours `lookup`,
`read_document`, `describe_image`, `context_search`), **remedies** (one unit
that corrects one pathology) and **orchestration** (Hard only).

**Before and after.** Every lesson is self-contained and shows two states of
one command. *Before* is everything the tier has built up to this lesson,
written out as one `--remedy` line so no earlier lesson is needed; *after* is
that line plus this lesson's one unit. A lesson **works** when its challenge
fails with *before* and passes with *after* at a preregistered n; that is the
lesson's test, and it also confirms the pathology on the current host.

| Tier | Lesson | Introduces | The failure | Adds |
| --- | --- | --- | --- | --- |
| Easy (from bare Pi) | E1 Read the failure | the trace | name it, find its row in the remedies list | nothing |
| | E2 Looking around | `read`, `ls` | the same call over and over | `guard/break-repeat-loops` |
| | E3 Searching | `grep`, `find` | searching the whole machine | `guard/stay-in-workspace` |
| | E4 Creating files | `write` | rewriting a whole file for a few lines | `guard/refuse-whole-file-rewrite` |
| | E5 Running commands | `bash` | a foreground server hangs the session | `guard/block-foreground-server` |
| | E6 Too many tools | the tool list | reaching for tools it uses badly | `context/narrow-tools` |
| Medium (from `preset:easy`) | M1 Tell it how to test | project facts | guesses the test command | `context/add-project-facts` |
| | M2 A short prompt | the system prompt | follows a procedure, not the files | `context/use-short-prompt` |
| | M3 Nudge an empty turn | the turn's end | stops mid-task with no reply | `nudge/nudge-empty-turn` |
| | M4 Thinking is working memory | reasoning | loses its reasoning between turns | keeping reasoning |
| | M5 Run long commands safely | background runs | waits on a watcher forever | `tool/background-long-commands` |
| | M6 Look it up | `lookup` | guesses an API it never saw | `tool/lookup-library-docs` |
| | M7 Check before finishing | the finish | ends with lint or type errors | `check/check-code-quality` |
| | M8 One spec per phase | the brief's layout | task shaping | `--specs split` |
| | M9 Steps, not one brief | the brief's delivery | task shaping | against `--single-prompt` |
| Hard (from `preset:medium`) | H1 Who drives | the orchestrator role | a parent hands the task to the worker | the role |
| | H2 The handoff | the intercom block | what the parent sees of the span | the handoff |
| | H3 Plan, examine, code | the flow's tools | one agent does everything at once | the flow roles |
| | H4 Frozen gates and checkpoints | gates | a later phase breaks an earlier one | per-phase gates, revert |
| | H5 Don't trust the self-exit | the exit | exits on its own weak test | an external acceptance test |
| | H6 Best of N | retries | one unlucky sample sinks a phase | parallel attempts |
| | H7 Build a Tool | writing an extension | the challenge needs a capability no tool gives | **the learner's own tool** (`--extension`) |
| | H8 Build a Remedy | writing a unit | the challenge needs a correction no unit makes | **the learner's own remedy** (`--extension`) |

`edit` is introduced in E4 as the tool E4's remedy points to. `read_document`,
`describe_image` and `context_search` join Medium when a challenge needs one.
Writes escaping the workspace (recorded 2026-10-29) wait for a
write-confining guard and its screen. Today's pages move with their evidence:
E3 → M1, E4 → M2, M2 → M3, M1 → M4, M3 → M8, M4 → M9, H1 → H1, H2 → H2; E1
and E2 are rewritten. `preset:easy` and `preset:medium` list each tier's
units in order; `preset:baseline-worker` stays for The Challenge.

`preset:hard` lists the same units as `preset:medium`: Hard's orchestration
(H1 to H6) runs through `learn/code/flow_run.py`, not as harness units, so the
harness line is the remedies and the flow is the orchestration.

**The end of the track is The Challenge's start.** H6's *after* state is
`preset:hard`; H7 and H8 then teach building, and in each the learner's own
file is what gets the pass. `preset:hard` is every tool and remedy the course
ships, in one line, and the learner leaves H8 able to add their own. The
Challenge page opens from it ("Finished Hard? Start from
`--remedy preset:hard`") and asks the learner to beat it by adding, swapping
or writing a remedy. It says honestly that the course gives every tool there
is, not a guaranteed pass: whether they pass Gold is what the Challenge
measures.

The 2026-10-29 lesson run shows the Bronze/Silver/Gold suites cannot do this
on a strong host: without the remedy, bare Pi still passes. So each lesson
gets its own **lesson challenge** under `learn/challenges/<lesson>/`: a small
fixture task, with a hidden grader, that reliably shows the lesson's failure.
A lesson ships only when its check, at a preregistered n, fails every session
without the unit and passes with it. Each lesson challenge is its own plan
task with its own preregistration; this spec fixes the format and the rule,
not the fixtures.

## The remedies list, in both sections

One list of pathologies and their remedies, generated from the units'
headers so it cannot drift, appears in **two** places: the Lessons section
(what each lesson teaches, as a quick reference) and The Challenge (what a
learner can apply to get a pass). Each row: the pathology in plain words, the
unit that remedies it, the lesson that teaches it, how strongly it is
measured, and the one `--remedy` line that applies it. Applying a remedy to a
Challenge attempt is meant to be that easy: copy the line, run the level.

## The Challenge: build and contribute

The Challenge page gains two sections:

- **Remedies you can try:** the remedies list above.
- **Build your own:** copy the smallest unit as a template, load it with
  `--extension`, attempt a level, and submit the extension, its scorecard and
  a note on the problem it fixes by pull request. A submitted remedy that
  measurably helps is the start of a new lesson.

## Out of scope

- Changing any measured setting, prompt or guard default.
- The scorecard format and results board (their own spec).
- Windows process handling (its own session).

## Acceptance

- Every unit in the table exists, is loadable with `pi -e` and has its test.
- `--remedy` and `--extension` work, and `run.json` records both.
- Phase 2's three equivalence proofs pass before the inline code is removed.
- Every lesson page names its unit and its lesson check; a lesson whose check
  is not yet built says so, and none claims a FAIL → PASS it has not shown.
- The Challenge page carries both new sections, and the Lessons section
  carries the same remedies list.
- `npm test`, the learn suite, the ladder fast suite and the docs caps pass.
