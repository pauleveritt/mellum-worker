# Satyrn Pi port: review for Andre

The port gives us a clean place to simplify the product and its vocabulary,
preserve the source evidence, and re-earn the implementation and tests. This
branch collects the design and proposed refactoring; implementation comes later.

The agreed scope is Pi only, the fixed Mellum subject model, a thin worker with
explicit remedies, and Education owning lessons and gamification. The
[brief](satyrn-pi/BRIEF.md) records these constraints and the measurement rules.

## Proposals for Andre

1. *Adopt Harbor's eval vocabulary.* Use dataset, task, trial, job, verifier and
   trajectory with precise boundaries. The [current → proposed table](docs/superpowers/research/2026-11-16-proposals-for-andre.md#vocabulary-for-the-port)
   maps the changes; Hamel/Shreya guide evaluation practice.

2. *One progression.* Use Vanilla → Base → Easy → Medium → Hard. Keep what is
   enabled separate from the tasks being evaluated; retire Baseline Worker and
   keep `bare` in historical mappings.

3. *Make additions explicit.* The worker stays thin; presets start empty and
   remedies earn inclusion through measurement, one candidate per cycle.

4. *Define the domain first.* P1.2 agrees worker/eval responsibilities, shared
   run meaning and a small glossary. Enforce a numeric jargon budget and review
   terminology in onboarding, output and scoring explanations.

5. *Keep one development workflow.* Use Superpowers and SDD throughout the port
   and ongoing work. Brainstorm each phase, add bounded feature cycles as needed,
   and close each cycle with review and evidence.

## What to review

Which proposals would you change, and what source evidence or behaviour would
we lose? Also resolve how task requirements can have one authoritative home
rather than diverging between the roadmap and prompts.

The Harbor renames are proposals for P1.2; the staged glossary still uses the
earlier names. The agreed `eval --suite` and `run.json` interfaces remain explicit
decisions. Detailed cleanup items are in the [full proposal list](docs/superpowers/research/2026-11-16-proposals-for-andre.md#proposals-for-andre).

## Reading path

- [Design brief](satyrn-pi/BRIEF.md): product scope, constraints and architecture.
- [Roadmap](satyrn-pi/ROADMAP.md): twelve phases, initial cycles and their boundaries.
- [Staged handoff](satyrn-pi/README.md): what will be copied into the new repository.
- Supporting detail: [glossary audit](docs/superpowers/research/2026-11-16-glossary-audit.md),
  [vocabulary review](satyrn-pi/docs/superpowers/research/2026-11-16-vocabulary-review.md),
  and [Andre's newer acceptance-feedback work](satyrn-pi/docs/superpowers/research/2026-11-16-upstream-acceptance-feedback.md).
