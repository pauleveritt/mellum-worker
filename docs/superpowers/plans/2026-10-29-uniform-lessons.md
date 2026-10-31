---
phase: LC
feature_cycle: LC.28
cycle: 1
lifecycle: active
---

# LC.28: uniform lessons, one concept from FAIL to PASS

Spec: [`2026-10-29-uniform-lessons-design.md`](../specs/2026-10-29-uniform-lessons-design.md).

**Dated correction 2026-10-29.** Lesson checks are one session per arm
(spec correction of the same date): before FAIL, after PASS. Lines use
`--repeat 1`; `lesson-check.sh`'s dry-run test checks `--repeat 1`.

**Dated correction 2026-10-29, after E4.** E4 missed twice on the 6-bit and
left the track (`8b99e8c`). Its before arm passing was this plan's stop
condition; Andre chose to continue on the same reference model rather than
reopen it. Too Many Tools is now E4 and Know When to Stop E5. A first screen
of E1's new challenge (`runs/E1-screen-20261029T212553Z-00cae9e`, one bare
session, a lead) also passed: the model read the 12,000-line file once, then
used `grep`, in 10 requests, without looping.

**Dated correction 2026-10-29, screen first.** The spec's correction of the
same date rebuilds the track from condition-produced pathologies. The order
of the remaining tasks changes: for each candidate in the rethink
([note](../research/2026-10-29-lessons-rethink.md)), a one-session bare
screen under its condition comes first; only a failing screen leads to its
challenge, preregistration, check and page. First, the harness records the
plumbing failures in `run.json` and the think-tag adapter becomes a unit.
The per-lesson tasks 8–27 below are superseded where a candidate replaces
them; the infrastructure tasks stand.

## Why

The lessons are not one kind of thing: some run, some do not, some run a
shared suite with a preset, and none has shown its own FAIL turning into a
PASS. This cycle gives every lesson the same contract and proves each one, or
takes it out of the track.

## Decisions taken before this plan

- **Reference model:** Mellum at 6 bits, served by vLLM on the LAN host
  (`http://192.168.88.99:11485/v1`, model id `mellum`, 65,536 context),
  through the pinned Pi 1.3.0 under `.baseline/`. Every record names this.
  BF16 on vast.ai is not used for lesson checks.
- **The spec's open questions, defaulted:** the before line keeps the
  build-up (every earlier unit, listed by name), and `flow_run.py` gains
  `--no-checkpoint` for H2. Either can be reversed by a dated correction to
  the spec before its lesson is built.
- **E4 goes first.** Its challenge exists and a 6-bit screen is running on the
  LAN host now (started 19:55 UTC; the first, interrupted attempt's one
  finished before session stalled on a foreground `uvicorn`).
- **Checks run detached.** A lesson check survives a closed terminal tab
  (`nohup`, `HUP` ignored), with its log followed in a tab of its own; the
  2026-10-29 tab close killed a run part-way.
- **Known failing test, not this cycle's:** "the page states what it is not"
  in `tests/pathologies.test.mjs` fails since `0471a35`. Fixed in task 5,
  which edits that page anyway.

## Tasks

Every task: test shown failing first, atomic pushed commit, changelog entry
when a learner-facing surface changes.

### Infrastructure

1. **The contract test.** `tests/lesson-contract.test.mjs` per the spec's
   "Enforced by a test": before and after lines, the lesson's own challenge
   under `learn/challenges/`, after = before + one remedy, no preset and no
   shared suite, the remedy's `meta.lesson` names this lesson, the Remedy
   unit line agrees. A `PENDING` list names every lesson that does not
   conform yet. The test also fails when a listed lesson already conforms, so
   the list can only shrink. First commit: the list is every lesson but S0.
2. **Every challenge qualifies.** A ladder-side test,
   `learn/code/tests/test_challenges.py`, runs `harness.qualify` on each
   folder under `learn/challenges/`. Marked `slow` (it installs each base).
3. **`scripts/lesson-check.sh <number>`.** Reads the lesson page's two
   lines through the tutor's parser (one small `node` entry point, no new
   npm script), runs before then after at the page's n, one arm at a time with
   port 8000 checked free, on a profile given by `--profile` (default: the
   LAN profile from `scripts/baseline/lan-profile/`, committed, no secrets).
   Detached, writes `runs/<slug>-check-<ts>-<sha>/`, prints the two verdict
   lines. Test: `--dry-run` prints both argv with `--repeat 3` and the
   profile.
4. **The FAIL screen says why.** `summariseRuns` lists the failing hidden
   checks by test name and the tutor adds the unit's `meta.pathology` under
   a FAIL. Tests in `tests/lesson-tutor.test.mjs` from a recorded `run.json`.

### The track change

5. **Lessons leave the track**, one commit each, content moved as the spec's
   table says:
   - E1 The Ditch → its session evidence into the false-success entry of
     `learn/pathologies.md` (and the page's failing test fixed there);
   - E2 Read the Failure → folded into S0's Evidence and Validation steps;
   - M1 Build a Harness → `learn/getting-started/the-harness.md`, linked from
     Working with Pi;
   - M5 Thinking Is Working Memory → a pathologies entry linking its notes;
   - M9 and M10 → one `BACKLOG.md` entry, "A unit that shapes the task in a
     session", with its reopen condition;
   - H1 Who Drives → the Hard index's opening;
   - H2 The Handoff → a `BACKLOG.md` entry, reopened when the handoff block
     is a unit.
6. **Renumber and add.** New numbers per the spec's track table, `position`
   in front matter, the nav in `zensical.toml`, `meta.lesson` on every unit,
   the regenerated remedies table, cross-links between lessons. Stub pages
   for E6 Know When to Stop, M7 Keep a Plan and M8 Build a Suite in the
   template, each in `PENDING`. Tutor test: the track is S0 plus 20.

### Easy, in order

Each Easy lesson task: the challenge (layout of `running-commands`), its
fixtures and qualify, a preregistration note, the check through
`lesson-check.sh`, the record under `evals/<date>-<slug>-check/`, then
the page (two lines, Remedy unit, Lesson check, badge) and removal from
`PENDING`. The forcing idea for each is a starting point; the preregistration
fixes it.

7. **E4 Running Commands** (`guard/block-foreground-server`). Challenge
   exists. Record the running screen as a screen; preregister the deciding
   run on the LAN 6-bit (revision 3 of the e5-check notes, renamed to the
   lesson's slug); point the page's lines at `learn/challenges`.
8. **E1 Looking Around** (`guard/break-repeat-loops`). A deep generated
   tree of near-identical folders with one value to find and use; a looping
   listing never gets to the build step.
9. **E2 Searching** (`guard/stay-in-workspace`). The task names a setting
   "already in the project" that is not where the model looks first; a
   machine-wide `grep` stalls.
10. **E3 Creating Files** (`guard/refuse-whole-file-rewrite`). A long
    existing module that needs a three-line change; the grader checks the
    untouched functions still behave.
11. **E5 Too Many Tools** (`context/narrow-tools`). A task where the offered
    extra tools fail in this setup; a session that reaches for them burns its
    turns. Risk: the 6-bit may not reach for them; then E5 takes its one
    revision.
12. **E6 Know When to Stop** (`guard/cap-turns`). A task with one
    requirement that cannot be met; the grader checks the possible parts and
    a `SUMMARY.md` naming the impossible one. Without the cap the session
    runs to its deadline with no summary.

### Medium, in order

The same per-lesson steps; the before set is every Easy unit plus the
earlier Medium units, listed by name.

13. **M1 Tell It How to Test** (`context/add-project-facts`). A project
    whose tests run only through its own command, given in `AGENTS.md`
    `## Mellum`.
14. **M2 A Short Prompt** (`context/use-short-prompt`). Project files whose
    conventions conflict with the long system prompt's procedure.
15. **M3 Nudge an Empty Turn** (`nudge/nudge-empty-turn`). A multi-step task
    the 6-bit tends to stop part-way through with an empty turn.
16. **M4 Run Long Commands Safely** (`tool/background-long-commands`). A
    long-running command the E4 guard does not catch (a watcher, a log
    follow) whose startup output the task needs. Risk: overlap with E4; the
    preregistration must show the before arm fails with E4's guard on.
17. **M5 Look It Up** (`tool/lookup-library-docs`). A small package
    installed in `base/` whose API the model cannot know.
18. **M6 Check Before Finishing** (`check/check-code-quality`). Graded with
    `--grade`; a task that invites unused imports and type slips.
19. **M7 Keep a Plan** (`tool/keep-a-plan`). A long task of many small,
    separately graded parts.
20. **M8 Build a Suite.** `harness.py qualify --grader DIR` (swap the
    grader folder), a weak committed grader that passes known-broken, a
    reference grader that does not, the tutor running `qualify` lines and
    showing which fixture passed. Deterministic: the record is one run of
    each line.

### Hard

21. **Flow infrastructure.** `flow_run.py --profile` (base URL and model from
    `models.json`, as the harness reads them), a `run.json` per attempt with
    the tutor's fields, `--no-checkpoint`, and `remedies/flow.json` with the
    three switches in the remedies table under kind `flow`. The tutor
    passes its profile to `flow_run.py` lines.
22. **H1 Plan, Examine, Code** (`workflow/spec-driven-flow`). A
    multi-phase challenge where one session breaks an earlier phase.
23. **H2 Checkpoint and Revert** (`--no-checkpoint` before). A phase that
    tends to break the one before it.
24. **H3 Don't Trust the Self-Exit** (`--flow-mode free`). A phase whose
    natural self-written tests miss a spec requirement the grader checks.
25. **H4 Best of N** (`--retry-concurrency 3`). A task with a low
    per-attempt pass rate on the 6-bit.
26. **H5 Build a Tool.** A challenge that needs a capability no unit gives
    (reading a local SQLite schema); reference tool committed beside it.
27. **H6 Build a Remedy.** A pathology no unit covers, taken from the record:
    the machine-wide `killall -f uvicorn` seen in the 2026-10-29
    running-commands sessions; reference guard committed beside it.

### Close

28. `PENDING` is empty; every page is `measured` or has left the track;
    ROADMAP Status and `## Now`, the CHANGELOG, a glossary entry for "lesson
    contract" and "flow switch", pathologies entries for any new failure
    shape; `npm test` and the ladder suite pass; plan `## Result`, archive.

## Order and checkpoints

Tasks 1–7 first: they make the contract real and prove it on the lesson
whose challenge exists. Tag `checkpoint-2026-MM-DD-uniform-lessons-e4` when
E4 conforms. Then Easy, Medium, Hard in order, a checkpoint tag at each
tier's end.

## What would stop this plan

The E4 deciding run on the LAN 6-bit misses the rule (before not 0 of 3).
Then the reference model question reopens before any other challenge is
built, recorded as a dated correction to the spec.
