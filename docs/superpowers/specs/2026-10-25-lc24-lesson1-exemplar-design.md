# Lesson 1 as the exemplar: the page, the convention, and the badge

Date: 2026-10-25. Status: approved by Paul on 2026-10-25; closed the same day.

**Dated correction 2026-10-25.** The follow-up is **seven** pages, not eight: the
track has eight lesson pages, and LC.24 shipped the opening on one of them. The
rest of this document reads as written.

**Dated correction 2026-10-25 (second).** Three further sentences still named the
ladder the measuring instrument after this cycle's rollout: `harness.md:81-82`,
and `suite.md:156-158` and `:165`, where the page also told the learner that
findings lessons cite `evals/` — a path lesson pages may not link. The
four sentences this cycle flipped were not the whole set. Corrected in LC.19A.

## Intent

Lesson 1, "The primary agent is the wrong worker", is the page a learner meets
first and the model every later lesson copies. It is not currently fit for
either job: its Problem section opens with a measurement rather than a
pathology, its Solution tells the reader not to "make the model the main
agent" — advice that names no decision anyone can take — and its Interpretation
argues against its own evidence by claiming every medium session was killed at
600 s when the baseline's medium sessions finished.

This cycle rewrites that page, gives it the terse summary paragraph the track
has been missing, and gives it evidence strong enough to hold the top badge on
the instrument the course actually teaches. It also settles what that top badge
means: `reference-run` stops pointing at `ladder/` and points at the suites.

`ladder/` is not deleted and `evals/` is not edited. They stay as the
internal instrument and the A0–A21 archive while the lessons move to a
suite-focus.

## Decisions taken before this spec

- **The ladder retires as the lessons' instrument.** `reference-run` is earned
  on `learn/code/harness.py` and the easy/medium/hard suites, with a
  preregistration and a `research-*` release. `evals/` remains citable
  history, not a badge requirement. Lessons already may not link it — seven
  test files assert `!/docs\/ladder\//`.
- **The terse paragraph lands on Lesson 1 and the template only.** The other
  eight lesson pages migrate in a follow-up cycle; a lone exemplar is the point.
- **LC.24 becomes `## Now`; LC.18 moves to Next.**

## Goals

1. The page names a pathology a learner can recognize from their own runs,
   before it names a measurement.
2. The mechanism paragraph says which decisions leave the model's hands, in
   terms a reader can act on, instead of naming a role ("main agent") that is
   an arm label in this repo and a choice nowhere.
3. The Interpretation's medium sentence is corrected: the baseline's medium
   sessions finished at 359 s and 204 s on the M5 Max; the 2026-10-24 medium
   sessions on the M1 Pro did not fit 600 s and now fit 1800 s.
4. The page opens with a two-sentence paragraph: one for the problem, one for
   the solution.
5. Steps 3 and 5 rest on one preregistered run covering easy and medium at n=3
   per arm, and the page says `reference-run`.
6. `learn/about/evidence.md` and `learn/glossary.md` define `reference-run` in
   terms of the suites; the four pages that call `ladder/` "the measured
   instrument" say the same.
7. `learn/lesson-template.md` carries the terse paragraph and its rule, so the
   next lesson starts right.

## Non-goals

- Migrating the other eight lesson pages to the terse paragraph.
- Deleting `ladder/`, editing `evals/`, or changing the ladder's code.
- Changing the worker prompt, guards, tools or facts. No re-baseline is owed.
- A rate, a probability, or a claim that transfers to another machine.
- Re-planning LC.19 onto a suite. It is noted as owed, not done here.

## Design

### The page

Order is unchanged: H1, then the terse paragraph, then the six steps. The
terse paragraph takes no heading of its own — every lesson test asserts exactly
the six `##` headings, and a seventh would cost nine test rewrites.

**Terse paragraph** (rule and first use):

> The primary agent lets one small model plan, choose and decide it is
> finished, so a confident final over unchecked code is the result. The worker
> takes those three decisions out of the model's text and leaves the plan and
> the verdict with you.

**Problem** — the pathology, not the outcome. The failure when the model holds
the plan and the stop condition is not a wrong answer; it is a confident final
over work it never checked, and nothing outside the model knows what "finished"
meant. The paragraph then says what this page's evidence can carry: an
unbounded Pi passed one easy session in three, the old 8/15 is retired, and the
baseline's medium contrast is what survives.

**Solution** — replaces "Do not make the model the main agent" with the three
decisions and where they go: the tool set narrows to seven file tools
(`pi.setActiveTools(WORKER_TOOLS)`, `extensions/mellum-worker.ts:411`); the
instructions become prompt v5, whose last line defines done as the test command
exiting 0 (`before_provider_request`, line 577); a guard may refuse to settle a
turn that ends empty (`agent_before_settle`, line 614). The plan stays with the
operator — one task per `/mellum` — and in a measured run the verdict is a
separate act: hidden tests are copied in and scored after the model stops.

The paragraph ends with the honest limit: on easy the nudge never fired (zero
fires in ten sessions, LC.13A), so what carried those runs was the test
command and the operator's scoring, not the guard.

**Interpretation** — the correction, dated, and the weakest badge named.

### The terse paragraph rule

- Sits between the H1 and `## Problem`, no heading, exactly two sentences: the
  first names the problem, the second the solution.
- Carries no badge, no link, no code span; 45 words or fewer.
- The template shows the two sentences as a placeholder and states the rule
  beside it, in the same way it shows the front matter.

### The badge rule

`learn/about/evidence.md` and `learn/glossary.md` change together:

| Badge | Means | Needs |
| --- | --- | --- |
| `reference-run` | A preregistered run on llama.cpp, made for this lesson | A preregistration written before the run naming the lesson, the arms, n, the reading and the decision rule; the record in `docs/superpowers/research/`; raw evidence in a `research-*` release; machine and deadline in the record |

`cited` loses `evals/` as its only home: it becomes "an existing record
in `evals/` (pre-2026-10-25) or a research note on `main`". The
"Upgrading and downgrading a badge" rule is unchanged — a badge never changes
without a linked record, and the change lands in the same commit as the record.

Four sentences across three files flip their instrument to the suites:
`learn/project/index.md`, `learn/project/toolchain.md`, and
`learn/getting-started/harness.md` (twice).

Only steps 3 and 5 change badge. Steps 1, 2 and 4 keep `screen`, whose meaning
and evidence are unchanged.

### The run

Preregistration in `docs/superpowers/research/2026-10-25-lesson1-preregistration.md`,
written and committed before the run.

- **Instrument:** `learn/code/harness.py`, suites `easy` and `medium`, arms
  `bare` and `worker`, `--repeat 3`, `--grade`, `--deadline 1800`.
- **Machine:** Apple M1 Pro, 8 cores, 32 GiB; `llama-server` 0.7.0, Mellum 2.1
  `Q4_K_M`, `-c 50000`. Wall times are this machine's; peak token counts
  travel.
- **Calibration:** LC.17's medium sessions finished at 894 s and 961 s at this
  deadline on this machine, so 1800 s is 1.9× the observed wall, not a guess.
- **Cost:** 12 sessions, roughly 2 h of wall.
- **Decision rule, fixed before the run.** For each suite, compare passes:
  - If `worker` passes strictly more sessions than `bare`, the page states the
    difference as a count of sessions at n=3.
  - Otherwise the page states a null for that suite.
  - No arm, suite, n or reading is changed after the run; a run that is cut
    short is reported, not rescued.
- **Either outcome publishes.** A null on medium returns Lesson 1 to `screen`
  on those steps and the page says so. The exemplar is the process — one
  preregistered run, one record, one badge change — not the result.

### Tests

Written first and shown failing:

- The terse paragraph exists on Lesson 1 and in the template, is two sentences,
  and carries no badge.
- `evidence.md` and the glossary define `reference-run` with the suites and
  without `evals/`, and still name `evals/` under `cited`.
- The harness lesson page and the two project pages no longer call `ladder/`
  the measured instrument.
- The existing Lesson 1 test keeps asserting six headings, the badge pattern,
  `weakest badge is`, and no `evals/` link.

## Deliverables

- `learn/lessons/primary-agent.md`, rewritten as above.
- `learn/lesson-template.md`, carrying the paragraph and the rule.
- `docs/superpowers/research/2026-10-25-lesson1-preregistration.md`, committed
  before the run, and its record after.
- `learn/about/evidence.md`, `learn/glossary.md` and the three instrument
  pages, carrying the re-pointed badge.
- `tests/lesson-primary-agent.test.mjs` (new) and the added assertions.
- `ROADMAP.md`: LC.24 as a new row, `## Now` pointing at it, LC.18 to Next, and
  LC.19's instrument note.
- `CHANGELOG.md`: one `Changed` entry under `[Unreleased]`.

## Risks

- **Wall time.** 12 sessions at 894–961 s on medium is ~1.75 h, and easy adds
  ~30 min. A machine that slows mid-run produces censored sessions; the record
  reports `deadline` and the page may not count a killed session as a failure.
- **n=3 is not a rate.** Even if the rule fires, the page states a difference
  of one or two sessions, as Lesson 2 already does.
- **Badge regression is possible.** If medium nulls, Lesson 1 is no longer the
  first `reference-run`; the cycle still ships the page, the convention and the
  rule, and `reference-run` simply has no holder yet.
- **LC.19 loses its instrument.** Rungs 6–9 no longer carry lesson 10's
  phase-gated task, so LC.19 needs a suite-shaped instrument before it can
  start. Recorded in its row; not solved here.
