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

Run 2026-11-03, easy, n=3, local Mellum 2.1 Q4 on llama-server `:8001`,
`--deadline 600 --stall 180`. Oracle = the hidden grader (`tests_passed`);
composite = `passed` (oracle plus ruff/no-leak).

| cell | oracle | composite | stalled | turns~ | wall~ |
|---|---|---|---|---|---|
| vanilla cold | 1/3 | 1/3 | 3/3 | 20 | 66s |
| vanilla warm | **3/3** | 2/3 | 1/3 | 21 | 77s |
| worker cold | 1/3 | 1/3 | 2/3 | 23 | 76s |
| worker warm | **3/3** | 3/3 | 0/3 | 17 | 60s |

**Warm lifts the oracle 1/3 → 3/3 in both arms, and collapses the foreground
hang** (cold stalled 3/3 and 2/3; warm 1/3 and 0/3). The margin clears the
decision rule: **the cold run is the accident.** `worker warm` is the cleanest
cell of the four — 3/3 on both metrics, no stall, the fewest turns.

Why it moves, from the traces:
- **Cold does not hide `AGENTS.md`** — every cold session explored (`ls`, `find`)
  and read `AGENTS.md` and `specs/roadmap.md` itself. So "cold" is "not
  auto-injected", not "absent".
- **Auto-injection changes behaviour, not availability.** Warm sessions went
  straight to `specs/roadmap.md`, and — the load-bearing part — heeded the
  file's "do not start servers" and "run the test command before reporting". The
  cold sessions read the same words but started `python app.py` / `uvicorn
  --reload` and hung anyway. Reading is not obeying; the system slot is.

**Implication.** The easy ladder's prompt remedies were measured against a cold
baseline an accident had pushed down to 1/3. A warm easy baseline is 3/3, so on
easy the remedies were largely re-supplying what the suite's own `AGENTS.md`
gives for free. `name-the-layout` is the clearest case — the cold layout misses
(`main.py`, a `request` query-param bug, `ModuleNotFoundError: app`) are exactly
what the auto-injected guide heads off.

**Decision.** Re-baseline the easy ladder warm (the convention-correct and
real-Pi condition) and re-weigh every easy prompt remedy against the warm floor,
at the fuller n a default change needs — this screen is the lead, not the rate.
Whether warm becomes the harness default is that re-baseline's call, not this
note's.

Two bycatch bugs, logged separately, not fixed here:
- `uv run uvicorn --reload` leaks a detached process group the workspace sweep
  cannot kill, so correct code is failed as a leak (vanilla warm session 1).
- A stalled session is still graded on its files, so a hang can score a pass if
  the code was finished first (vanilla cold session 3) — the composite catches
  it, the oracle alone does not.

Raw runs under `runs/agents-md-warmcold/` (git-ignored); promote with traces
stripped if this screen graduates to a recorded ladder run.

