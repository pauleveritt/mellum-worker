# Uniform lessons: one concept, see it fail, apply one remedy, see it pass

Date: 2026-10-29. Status: approved by Andre on 2026-10-29.

**Dated correction 2026-10-29.** Andre: lessons do not need n = 3. A lesson
check is **one session per arm**: before must FAIL and after must PASS, which
is exactly what a learner sees when pressing `r`. Run lines use `--repeat 1`.
A lesson check is therefore a demonstration on the reference model, not a
rate, and pages say so; rates stay with the suites and the ladder. The rule,
risk and line-form passages below read as written otherwise.

**Dated correction 2026-10-29, the track is rebuilt from conditions.**
Approved by Andre after the rethink
([note](../research/2026-10-29-lessons-rethink.md)). Two lesson checks and
two screens showed the 6-bit avoiding luck-dependent traps in small clean
challenges (E4 left the track; E1's harder challenge passed bare). From now:

1. **A lesson's pathology is produced on demand by a condition the lesson
   states** (a serving stack, a window, a cap, a task trap, a length). The
   before line sets up the condition; one remedy removes the failure under it.
2. **Screen first.** One bare session under the condition comes before any
   challenge polish, preregistration or page. Only a pathology whose before
   arm fails on its screen becomes a lesson.
3. **FAIL may be read from the record**, not only from hidden tests. The
   harness grades serving and session failures from the trace into
   `run.json` (for example, turns whose reasoning came back as text), and the
   tutor names them on the FAIL screen as it names a missed check.
4. **The track is the rethink's candidates**: Easy is the plumbing (serving
   and context: reasoning as text, overflow from a tool, the output cap,
   runaway turns); Medium the task traps (an API past the cutoff, a decoy, a
   trap row, the test command, lint); Hard orchestration (as before). A
   current lesson with no condition that produces its pathology leaves the
   track the way E4 did; its guard stays in the remedies list for The
   Challenge.
5. **The think-tag adapter becomes a unit** (Easy's first lesson), not a
   harness default: every later lesson's before line lists it, so the
   failure is shown once and then kept fixed, like every other unit.

The contract, the one-session rule, the check and the enforcement below read
as written otherwise; the track table and "leaving the track" table are
superseded by the rethink's candidates as they pass their screens.

## Intent

The remedy-units cycle (LC.27) gave every remedy one role in one file, and
the `/lesson` tutor runs a page's before and after lines inside Pi. The
lessons themselves have not caught up. Of the 26 entries in the track, only
S0 and the ten unit lessons have a before line and an after line that differ
by one unit, and even those run on the shared `easy` suite, where the
preregistered lesson check held for none of them
([note](../research/2026-10-29-lesson-check.md)). The rest have no runnable
lines (E1, H2, H4), a before line only (E2, H1), an arm or flag instead of a
unit (M5, M9, M10, H3–H6), or a remedy the learner writes (H7, H8).

A learner cannot tell which kind of lesson they are in, and pressing `r` does
something different on each. This cycle makes every lesson the same thing.

## The lesson contract

Every lesson in the track is exactly this:

1. **One concept.** It names one failure a small model shows, in one
   sentence: the pathology line of its remedy.
2. **See it fail.** The before line runs the lesson's **own challenge**
   without the remedy, and the result is FAIL.
3. **Understand why.** The FAIL screen says what failed (the hidden checks
   that did not pass) and why (the remedy's pathology line), and the page's
   Evidence step explains it from the record.
4. **Apply one remedy.** The after line is the before line plus **one**
   remedy. A learner can apply it on the command line, by pressing `r` in
   `/lesson`, or, for a unit, with `/remedy on <unit>` in Pi.
5. **See it pass.** The after line's result is PASS.
6. **Proven.** A preregistered lesson check on the reference model shows
   before failing and after passing, recorded under `evals/`.

A lesson that cannot meet the contract **leaves the track**. Its evidence is
kept where it already belongs (the pathologies page, a research note, or a
Getting Started page) and its number is not reused. Nothing is shipped as a
lesson that does not show a FAIL turning into a PASS.

## What a remedy is, per tier

- **Easy and Medium:** one remedy unit from `remedies/<kind>/<name>.ts`. Its
  `meta.lesson` names the lesson, and each unit belongs to at most one lesson.
- **Hard:** one **flow switch** of `learn/code/flow_run.py`: one flag that
  turns one orchestration behaviour on. A flow switch gets the same record as
  a unit (pathology, does, lesson, evidence) in `remedies/flow.json`, and the
  remedies table lists it under the kind `flow`. Flow switches have no
  `/remedy` form: they shape the driver, not a Pi session. The Hard index
  says so.
- **H-build lessons** (build a tool, build a remedy): the remedy is a file
  the learner writes. The after line loads a **reference solution** committed
  with the challenge (`--extension learn/challenges/<slug>/reference/<file>.ts`);
  the page shows how to swap in the learner's own file. The reference is what
  the lesson check proves.

## The track

Easy builds from bare Pi; each lesson's before line is the units of every
lesson before it, **listed by name**, and its after line adds one more.
Medium and Hard carry on the same list. No lesson line uses a preset
(`preset:easy` and the rest are combinations, for The Challenge) or a shared
suite (`easy`, `medium`, `hard` exercise many pathologies at once, so a pass
or a fail cannot be laid at one remedy). Both are refused by the contract
test.

| New | Title | Remedy | Was | Change |
| --- | --- | --- | --- | --- |
| S0 | Start Here | the stand-in (no model) | S0, E2 | takes E2's reading of `run.json` |
| E1 | Looking Around | `guard/break-repeat-loops` | E3 | own challenge |
| E2 | Searching | `guard/stay-in-workspace` | E4 | own challenge |
| E3 | Creating Files | `guard/refuse-whole-file-rewrite` | E5 | own challenge |
| E4 | Running Commands | `guard/block-foreground-server` | E6 | challenge exists |
| E5 | Too Many Tools | `context/narrow-tools` | E7 | own challenge |
| E6 | Know When to Stop | `guard/cap-turns` | new | unit exists, no lesson |
| M1 | Tell It How to Test | `context/add-project-facts` | M2 | own challenge |
| M2 | A Short Prompt | `context/use-short-prompt` | M3 | own challenge |
| M3 | Nudge an Empty Turn | `nudge/nudge-empty-turn` | M4 | own challenge |
| M4 | Run Long Commands Safely | `tool/background-long-commands` | M6 | own challenge |
| M5 | Look It Up | `tool/lookup-library-docs` | M7 | own challenge |
| M6 | Check Before Finishing | `check/check-code-quality` | M8 | own challenge |
| M7 | Keep a Plan | `tool/keep-a-plan` | new | unit exists, no lesson |
| M8 | Build a Suite | the learner's grader; reference committed | new | runs `qualify`, no model |
| H1 | Plan, Examine, Code | `workflow/spec-driven-flow` (the flow itself) | H3 | flow reads `--profile` |
| H2 | Checkpoint and Revert | flow switch: checkpoints | H4 | needs an off switch |
| H3 | Don't Trust the Self-Exit | flow switch: `--flow-mode free` | H5 | own challenge |
| H4 | Best of N | flow switch: `--retry-concurrency` | H6 | own challenge |
| H5 | Build a Tool | the learner's tool; reference committed | H7 | own challenge |
| H6 | Build a Remedy | the learner's unit; reference committed | H8 | own challenge |

**Leaving the track:**

| Was | Why it does not conform | Where its content goes |
| --- | --- | --- |
| E1 The Ditch | No remedy: it shows false success and stops | Its session evidence joins the false-success entry in `learn/pathologies.md` |
| E2 Read the Failure | No remedy: it teaches reading the record | Folded into S0 |
| M1 Build a Harness | No remedy: it builds the instrument | A Getting Started page, "The harness", beside Working with Pi; building the measuring side is M8 |
| M5 Thinking Is Working Memory | Bare Pi keeps thinking already; the failure needs a fault injected, not a remedy applied | Its evidence stays in its research notes and a pathologies entry |
| M9 One Spec per Phase, M10 Steps, Not One Brief | Task shaping by flag, not a remedy | Kept in their research notes; a reopen condition in `BACKLOG.md`: a unit that shapes the task inside a session |
| H1 Who Drives | A framing, not a failure with a remedy | The opening of the Hard index |
| H2 The Handoff | The handoff block is inside the worker, not a unit, and has no challenge | `BACKLOG.md`, reopened when it becomes a unit |

The track becomes S0 plus 20 lessons: Easy 6, Medium 8, Hard 6.

## M8 Build a Suite

The learner builds a challenge in Pi, in `project/M8`, with the model's help.
The concept: **a weak grader passes a wrong build**, so a suite proves
nothing until it fails a known-broken build.

- **Before:** `harness.py qualify --suites-dir learn/challenges --suite
  build-a-suite`, whose committed grader is too weak: it passes the
  known-broken fixture, so `qualify` reports FAIL.
- **After:** the same line with `--grader <dir>`, a new `qualify` option that
  swaps in another grader folder: the committed reference, or the learner's
  own from `project/M8`. It fails known-broken and passes known-good, so
  `qualify` reports PASS.
- No model runs, so the lesson check is deterministic: both lines run once
  and the record holds their output.
- The tutor treats a `qualify` line like a run line: `r` runs it, and the
  result screen shows which fixture passed or failed.

## Each lesson's own challenge

Every lesson has `learn/challenges/<slug>/`, its slug the lesson page's file
name, in the layout `running-commands` already uses: `base/`, `prompts/`,
`grader/`, `expected.json`, `layout.json`, and `fixtures/known-good` and
`fixtures/known-broken`.

- **Forcing.** The task must make the pathology both likely and fatal. A task
  the model can finish while dodging the trap does not separate; that is what
  happened to running-commands on BF16 (3/3 before, 3/3 after,
  [note](../research/2026-10-29-e5-check.md)).
- **Qualified.** `harness.py qualify` passes known-good and fails
  known-broken, and a test runs `qualify` on every challenge.
- **Agnostic.** The hidden grader checks behaviour the prompts ask for. No
  unit, guard or prompt names a challenge, route or expected value.
- **Small.** One session finishes inside the page's deadline on the reference
  model; Easy and Medium challenges aim at 10 minutes, Hard at 45.

## Running inside Pi, the same way for every lesson

- Every lesson's Run it yourself block has **exactly two** run lines, before
  then after, in one form:
  `harness.py run --suites-dir learn/challenges --suite <slug> --remedy <before set> --repeat 3`
  for Easy, Medium and H-build, `harness.py qualify … [--grader <dir>]` for
  M8, and
  `flow_run.py --suite <slug> [<switch>]` for the flow lessons.
- `/lesson` runs both on the model Pi is using (shipped in `2b60915`).
  `flow_run.py` gains `--profile`, read the same way the harness reads it, so
  the tutor's profile reaches flow lessons too.
- `flow_run.py` writes a `run.json` per attempt with the fields the tutor
  reads (`passed`, `checks_ran`, `stalled`, `missing_checks`), so the FAIL and
  PASS screens read the same for both drivers.
- The FAIL screen lists the failing hidden checks by name and the remedy's
  pathology line.
- Manual work stays in `project/<number>`, prepared by `p`.

## The lesson check

- **Reference model:** Mellum 2.1 at 6 bits, served by vLLM on the project's
  LAN host, through the pinned Pi. BF16 dodged the running-commands trap; the
  6-bit falls into it (handover screen: 2/3 before, 3/3 after). The record
  names the host, weights and Pi version.
- **Preregistered** per lesson before its first deciding run: arms, n,
  scoring and rule, in `docs/superpowers/research/`.
- **Rule:** n = 3 per arm; the lesson holds if before passes **0 of 3** and
  after passes **at least 2 of 3**.
- **One revision.** A lesson that misses the rule gets one preregistered
  revision of its challenge. A second miss means it leaves the track, recorded
  as a lesson whose pathology resisted a FAIL → PASS on this model.
- **Recorded** under `evals/<date>-<slug>-check/` with `run.json` and
  `final.md`, raw traces stripped. The page's "Lesson check:" line links the
  record and its badge becomes `measured`.

## Uniform pages

Every lesson page keeps the current template (Overview, Problem, Eval case,
Evidence of the problem, Solution, Validation, Interpretation, Run it
yourself, Key points). Additionally:

- **Remedy unit:** names exactly one unit, one flow switch, or "your file"
  with the reference path. No "none".
- **Lesson check:** links its record, or says "not yet run" until it does.
- **No second terminal.** The Run it yourself block holds the two run lines
  only; anything else a learner types happens inside Pi or in
  `project/<number>`.

## Enforced by a test

`tests/lesson-contract.test.mjs` checks, for every lesson in the track:

- the page parses to a before and an after line;
- both name the lesson's own challenge, and that challenge exists;
- the after line is the before line plus exactly one remedy;
- neither line names a preset or a shared suite (`easy`, `medium`, `hard`);
- the remedy's `meta.lesson` (or its `remedies/flow.json` entry) names this
  lesson, and no remedy names two lessons;
- the Remedy unit line agrees with the after line.

Until the rollout ends, the test carries an explicit list of lessons not yet
conforming. A lesson leaves the list when it conforms, the list may only
shrink, and the cycle closes when the list is empty.

## Rollout

1. **The contract test and the track change:** the contract test with its
   list, lessons leaving the track (content moved as above), renumbering,
   `meta.lesson` updates, presets, the nav, the regenerated remedies table.
2. **Easy, in order:** a challenge per lesson, qualified, then its lesson
   check. E4 first: its challenge exists and was screened.
3. **Medium, in order**, the same way.
4. **M8 Build a Suite:** `qualify --grader`, the weak and reference graders.
5. **Hard:** `--profile` and `run.json` in `flow_run.py`, the checkpoint off
   switch, then a challenge and check per lesson.
6. **Close:** the list is empty, every page is `measured` or has left the
   track, ROADMAP and CHANGELOG are reconciled.

Each lesson is its own commit: challenge, qualify test, preregistration,
record, page. A lesson that leaves the track is its own commit too.

## Out of scope

- New remedy units beyond the two that exist without a lesson
  (`guard/cap-turns`, `tool/keep-a-plan`).
- Changing the measured worker or any default it ships.
- The Challenge (`learn/challenge/`): it keeps its own suites.

## Open questions

- **Build a Harness.** It has no remedy, so this spec moves it to Getting
  Started; M8 Build a Suite carries the hands-on measuring work instead.
- **How far the before line builds up.** This spec keeps the build-up (each
  before lists every earlier unit by name), so earlier failures cannot mask
  this lesson's. The alternative is bare Pi before and one unit after, which
  isolates the concept further but lets an earlier pathology fail the after
  arm.
- **H2's off switch.** Checkpoint-and-revert is always on in `flow_run.py`.
  This spec adds `--no-checkpoint` so the lesson has a before. If a switch
  that only exists for teaching is unwanted, H2 leaves the track.

## What would falsify this

Easy lessons whose before arm passes on the 6-bit even with a forcing
challenge, as running-commands did on BF16. Then the reference model is too
strong for the guard lessons, and the choice is a weaker reference or fewer
lessons, not a looser rule.

## Risks

- n = 3 per arm: one session moves a verdict. The rule's 0-of-3 before arm is
  strict on purpose, because `r` runs one session and must show FAIL.
- The reference host is a LAN server: the record must name its weights and
  serving stack, or a later run cannot be compared with it.
- Twenty challenges is a lot of grader code. Each is small and qualified,
  and they share the `running-commands` layout.
