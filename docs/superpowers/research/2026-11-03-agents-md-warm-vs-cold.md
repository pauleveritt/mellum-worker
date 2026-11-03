# The eval runs cold: is the suite's AGENTS.md worth loading?

- **What is measured:** the easy suite's pass rate and turns for two arms, each
  run cold (the current default) and warm (the suite's own `base/AGENTS.md`
  loaded), on local Mellum 2.1 Q4 via llama-server on `:8001`.
- **What is conjecture (until this run):** that `--no-context-files` strips the
  suite's intended guide as an unintended side effect of machine isolation, and
  that loading it lifts the baseline — so part of what the prompt remedies buy is
  re-supplying what `AGENTS.md` would have given.

## Why this is in question

`--no-context-files` entered in `c27fd07` ("one isolated run per task") inside an
isolation bundle — `--no-approve --no-extensions --no-skills
--no-prompt-templates --no-themes --no-context-files` — all meant to block the
developer's ambient config. But the run is already isolated: the workspace is a
fresh `mkdtemp`, the suite's `base/` (its `AGENTS.md` and `specs/`) is copied in,
and Pi runs with that temp dir as cwd. From a temp workspace no ancestor holds an
`AGENTS.md`, so dropping `--no-context-files` would load the suite's own
`AGENTS.md` and nothing from the machine. That file is written as agent
instructions ("requirements are in `specs/roadmap.md`", the test command, "do not
start servers") — exactly the convention a coding agent follows, and exactly what
real Pi and the warm hands-on sandbox both load.

## Arms, n, rule

A new harness switch, `--context-files`, keeps the workspace's `AGENTS.md` (warm);
off by default the run stays cold. Four cells, easy suite, `--repeat 3`,
`--grade`, `--deadline 600`, `--stall 180`, judged on the hidden grade:

| Cell | Command |
|---|---|
| vanilla cold | `--arm vanilla` |
| vanilla warm | `--arm vanilla --context-files` |
| worker cold | `--arm worker` |
| worker warm | `--arm worker --context-files` |

**Decision rule.** If warm lifts the baseline (vanilla or worker) by a clear
margin, the cold run is an accident: re-baseline the easy ladder warm and re-weigh
every prompt remedy against the warm floor (`name-the-layout` especially, which
is partly doing `AGENTS.md`'s job). If warm does not move the rate, the cold run
stands and this note records why the two are equivalent for this model.

## What would falsify / risks

- **Falsifies "cold is an accident":** warm and cold pass at the same rate and
  similar turns — the model ignores `AGENTS.md`, so stripping it costs nothing.
- **Risk — n is small.** n=3 is a screen, a lead, not a rate to ship a default on;
  a decision to re-baseline needs the fuller ladder run after.
- **Risk — one model, one backend.** Local Q4 only; a larger quant or a different
  model could read `AGENTS.md` where this one does not, or the reverse.

## Result

_(pending the run)_
