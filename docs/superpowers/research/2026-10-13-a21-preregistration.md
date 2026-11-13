# A21 preregistration: the lighter `## Mellum` section and a one-file roadmap

Date: 2026-10-13, written and committed before any A21 run. Paul asked for
A21 on 2026-10-13 ("do all 3 of the loose ends"), the GPU run included.

**What is measured.** Nothing yet. This fixes the arms, n, scoring and the
decision rule before the runs.

**What is conjecture.** That the bullets the README, setup skill and
`/mellum learn` have recommended since v0.1.5 (`Test command:` plus a
`Do not:` naming the bends, no `Write only:` list) keep A19's results, and
that asking for "Phase N of specs/roadmap.md" works as well as one spec
file per phase ([facts wording note](2026-10-11-facts-wording.md)).

## Question

Do Mellum Mode runs on AgentClinic rungs 6–9 hold up with the README's
section and a one-file roadmap, against the section A19 measured and one
spec file per phase, on today's code and Pi?

## Arms

Both from `ladder/` at the commit that adds this file, Pi 1.1.0
(`--pi-executable` default `pi`), Mode with guards and facts on,
`--profile baseline`, `--deadline 600`, rungs 6–9, `--repeat 3`: 12 runs
each.

- **A21** (`evals/2026-10-13-ablation-a21-light-section-roadmap/`):
  `--facts-section light --roadmap one-file`. `AGENTS.md`'s section is
  `ladder/run_ladder.py` `LIGHT_SECTION`; `specs/` holds only
  `roadmap.md`, the four phase specs verbatim; the task is
  `Implement Phase N of specs/roadmap.md`.
- **A21 control** (`evals/2026-10-13-ablation-a21-control/`): no variant flags,
  so A19's fixture (three bullets including `Write only:`; one spec file
  per phase; task `Implement specs/phase-N-….md`).

A21 runs first, then the control, one after the other. The two changes in
A21 are measured together, as the backlog entry defined A21; the decision
below does not need to tell them apart.

## Scoring

The ladder's `check_agentclinic`, unchanged: the facts test command passes,
the hidden tests of phases 1..N pass, existing tests are kept (additions
allowed), and nothing is written outside `app.py`, `models.py`,
`templates/`, `tests/` (`outside_write_list` empty). A pass needs all four.
The write-list check still applies to A21, which is not told the list:
that is what the run tests.

## Decision rule

Let *a* and *c* be the passes out of 12 for A21 and the control, and *o*
the A21 runs with a non-empty `outside_write_list`.

1. If *c* < 7, the control has drifted from A19 (9/12): no decision; record
   it and look for the cause (Pi 1.1.0, code since `aff031a`) first.
2. Else, if *a* ≥ *c* − 1 and *o* ≤ 1: keep the README, setup skill and
   `learn` as they are, and say A21 measured them.
3. Else: the README, setup skill and `learn` go back to recommending a
   `Write only:` line (A19's measured section), and the backlog keeps a
   one-variable follow-up if the cause matters.

With n = 12 per arm a difference of one run is noise; the rule only acts
on larger gaps, and its failure branch returns to the measured section.

## Descriptive only

Median requests and wall time per arm; leftover processes stopped
(`leftover_processes`); for A21, whether a run built a later phase than
asked (a later phase's hidden test passing). None of these changes the
decision.

## What would falsify this

A control far below A19 would mean today's setup, not the section, is
being measured (rule 1). An A21 that passes but writes outside the layout
in two or more runs would show the list was doing work the named bends do
not.

## Risks

- The arms run in sequence, not interleaved; server state or thermal drift
  over about 50 minutes affects the second arm more.
- Twelve runs per arm cannot separate the section from the roadmap shape.
- The phase specs keep `python app.py` from A19's fixture; ac-demo now
  says `uv run --frozen python app.py`. Both arms share it.
