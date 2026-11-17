---
phase: LC
feature_cycle: LC.27
cycle: 1
lifecycle: active
---

# LC.27 — remedy units, one role each

Spec: [`2026-10-29-remedy-units-design.md`](../specs/2026-10-29-remedy-units-design.md).

## Why

The 2026-10-29 lesson check showed a lesson cannot show its own FAIL → PASS:
its remedy is fused into the worker and the suites sit under the pass floor
of a strong host. Learners attempting The Challenge cannot add, drop or bring
a remedy. This cycle makes each remedy a selectable unit and gives both
sections the list.

## Decisions taken before this plan

- **Nothing measured changes.** `extensions/mellum-worker.ts`, its guard
  defaults, `prompts/mellum-worker.md` and `package.json` are untouched until
  task 6's equivalence proof; no unit is installed by the package.
- **Units wrap, never copy.** A unit imports the existing function.
- **Opt-in experimental units stay opt-in.** `tool/*`, `check/*` and
  `workflow/*` wrap the PR #4 extensions the backlog entry "Experimental agent
  extensions" keeps uninstalled; a unit makes them loadable, not default.
- **Lesson challenges are LC.26's work.** This cycle fixes the format and the
  rule; each fixture is its own preregistered task under LC.26.
- **Known gap, not fixed here:** `confineSearch` blocks searches only. An E4
  `no-prompt` session on 2026-10-29 wrote `app.py` to the repository root by
  absolute path. Extending `guard/stay-in-workspace` to writes is a guard
  change, so it needs its own screen and the re-baseline the backlog entry
  "PR #1 prompt and guard extraction" requires.

## Tasks

Every task: test shown failing first, atomic commit, changelog entry when the
user-facing surface changes.

1. **Unit scaffold.** `remedies/` with one unit (`guard/break-repeat-loops`)
   and the shared test helper: a fake `pi` that records `on`, `registerTool`
   and `setActiveTools` calls. Test: the unit registers exactly one
   `tool_call` handler and blocks the fifth identical call, matching
   `createLoopBreaker`'s existing cases. `node --test` picks up
   `remedies/**/*.test.mjs` (extend the `test` script's globs, no new script).
2. **The guards and the nudge.** `block-foreground-server`,
   `stay-in-workspace`, `refuse-whole-file-rewrite`, `cap-turns`,
   `nudge-empty-turn`, each with its own-hook-only test and the wrapped
   function's cases.
3. **Context units.** `add-project-facts`, `use-short-prompt`,
   `keep-thinking`, `narrow-tools`. Tests feed a recorded request payload
   through each and compare with the worker's `filterForMellum` output for
   that one concern.
4. **Opt-in units.** `tool/background-long-commands`,
   `tool/lookup-library-docs`, `tool/keep-a-plan`, `check/check-code-quality`,
   `workflow/spec-driven-flow`: each a default export wrapping the existing
   extension, with a load test.
5. **Harness flags.** `harness.py run --remedy LIST` (names or
   `preset:<name>`) and repeatable `--extension PATH`; `run.json` gains
   `remedies` and `extensions` (path and SHA-256). Tests: an unknown unit is
   refused with the list of known ones; a preset expands in order; the argv
   carries one `-e` per unit after the arm's extension; `run.json` records
   both. `baseline.py lessons` checks the model answers before each command
   and reopens the tunnel, never recording against a dead one (the
   2026-10-29 drop).
6. **The worker as a preset.** *(Dated 2026-10-29: proven by equivalence tests
   instead of a rewire; see the spec's phase 2 correction.)* `remedies/presets/baseline-worker.json`, then
   `mellum-worker.ts` composes from the units. Three proofs before the
   inline code goes: request equivalence (byte-identical
   `before_provider_request` output on the worker's recorded payloads),
   decision equivalence (every guard case), and `npm test` plus the ladder
   fast suite unchanged.
7. **The remedies list.** Generated from the units' headers into
   `learn/snippets/remedies.md` by a small script, included on the Lessons
   index and The Challenge (Zensical snippets). Test: the generated list
   names every unit and matches the files. Rows: pathology, unit, lesson,
   evidence, the `--remedy` line.
8. **The Challenge: build your own.** The page section: copy
   `guard/break-repeat-loops` as the template, load it with `--extension`,
   attempt a level, submit by PR with the scorecard and a note.
9. **Lesson pages.** Each lesson names its unit and its lesson check; one
   whose lesson challenge is not built says so, and no page claims a
   FAIL → PASS it has not shown (a test enforces the wording).

10. **The tiered track** *(added 2026-10-29; the spec's dated track
    correction).* Reformat the lessons into Easy E1–E8, Medium M1–M9 and
    Hard H1–H6, each tier starting from the previous tier's preset. Keep
    Paul's six steps, each shortened: Problem; Eval case as **see it fail**;
    Evidence of the problem as the FAIL; Solution as **add the remedy** (the
    unit, its excerpt, the `--remedy` line); Validation as **see it pass**;
    Interpretation in one paragraph. Existing evidence moves with its page
    into a closing fold; a lesson with none says it is not measured yet. Old
    URLs redirect. `preset:easy` and `preset:medium` list each tier's units.
11. **Pictures.** One illustration per new page from the lab server
    (`scripts/illustrate.py`, prompts in `prompts.toml`), same style.
12. **Test each lesson.** Per lesson, in track order: a lesson challenge
    under `learn/challenges/<lesson>/` built to show its one failure, a
    preregistration, and a run at n = 3 without and with the unit on the
    previous tier's preset. The page's lesson check flips to PASS only on
    that record. Start with the units likeliest to show a clean FAIL → PASS
    (`block-foreground-server`, `break-repeat-loops`).

## Checks before close

- `npm test`, the learn suite, the ladder fast suite, the docs caps.
- `uvx --with zensical-glossary zensical build` with the remedies list on
  both pages; glossary entries for **remedy unit** and **preset**.
- The lesson check's record and verdicts are in `evals/` and linked
  from the research note; LC.26 holds the per-lesson challenge tasks.
