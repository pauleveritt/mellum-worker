# R.1 preregistration: earning Base, then Easy's units on it

## For Andre

- **What this is:** the arms, n, interleaving and decision rule for R.1's two counted batches on
  Easy, fixed before any counted session. The design is the
  [R.1 spec](../specs/2026-11-07-r1-easy-remedies-design.md).
- **Status:** the rule was agreed with Paul on 2026-11-07. The grader digest and the execution
  policy are filled in below before step one starts; nothing counted runs until they are.
- **What to look at:** the rule. Once the first counted session runs, the rule cannot change.

**What is measured.** Nothing yet.

**What is conjecture.** That 12 sessions per arm are enough to see a halving of stalls, or a
one-check gain. Both are thresholds we chose, not power calculations.

## Ladder run

Harness, Easy (13 current checks), M5 Max, llama.cpp b12110 on :8001, Pi 1.4.0, thinking on,
`--host-card`, `--grade`, `--stall 180`, Easy's `budget.json` (64 requests / 32,000 output tokens,
`wall_safety` 1,200 s). Arms are interleaved round-robin in one batch, so drift in the host hits
every arm alike.

- **Step one:** `--arm vanilla`; `--arm worker --remedy <unit>` for each candidate that Screen 1
  keeps, from `tool/bounded-commands`, `guard/foreground-server`, `guard/foreground-log-follow`
  and `prompt/name-the-layout`. n = 12 each.
- **Step two:** `--arm vanilla`; Base (`--arm worker --remedy preset:base`, or Vanilla if Base is
  empty); Base + `check/compile-import`; Base + `check/mediated-test`. n = 12 each.

## Screens (leads, n = 3 each)

A candidate enters the counted batch unless, in its three screen sessions, its hook never acted
(the trace shows no bound applied, no block and no injection), or its mean checks passed is 2 or
more below Vanilla's in the same screen. Vanilla's stall count in a screen drops no candidate:
three sessions can't tell whether stalls are rare. Screen 2 uses the same rule against Base.

## Decision rule

- **Stall handler** (against Vanilla). It wins only if all three hold:
  - Vanilla has at least 2 of 12 sessions stalled or censored, and the handler has at most half
    as many.
  - Its mean checks passed is at most 1 below Vanilla's.
  - Its median requests and median output tokens are each at most 20% above Vanilla's.

  If two handlers win, Base keeps the one with the lower median requests. If Vanilla stalls in
  fewer than 2 sessions, no handler enters Base.
- **Quality unit** (`prompt/name-the-layout` against Vanilla; each step-two unit against Base). It
  wins if:
  - its mean checks passed is at least 1 higher, or at least 3 more of its 12 sessions pass all 13
    checks;
  - and it keeps the same 20% budget limit.
- **Stacking:** if both step-two units win, a combined screen (n = 3, a lead) runs before both go
  into `preset:easy`.
- **Which sessions count where:**
  - Mean checks passed and full passes include every session, each graded as it stands.
  - Budget medians leave out stalled and censored (`wall_safety`) sessions, whose cost was cut
    short; those are reported on their own line (Paul, 2026-11-07).
  - A `budget` ending counts as a session everywhere.
  - No arm is stated as a rate beyond its n.

## Fixed before step one

Fixed at `r1-easy-remedies` @ `fa4ea31`, before any counted session.

- **Grader identity** (`--grader current`), sha256 of each file in `learn/code/suites/easy/grader/`:
  `_contract.py` `94ab3961…a871d`, `_easy_acceptance.py` `ba58cc09…f02ff`, `_easy_launcher.py`
  `ffa3b404…2a340`, `test_phase1_acceptance.py` `0e47a066…eff5aa`, `test_phase1_home.py`
  `e4c3289d…84fdd`, `__init__.py` empty. Thirteen checks.
- **Execution policy:** `learn/code/grading.py` (`89623d22…6ce87`) and `grading_worker.py`
  (`f26fcb2c…db9c1`). Each grade runs on a disposable copy without the project's configuration,
  with Easy's own `pyproject.toml` and `uv.lock`, through `uv --no-config run --project <trusted>
  --frozen --with pytest --no-editable python -I grading_worker.py`, in an environment with no
  `PYTHON*`, `PYTEST*` or `UV_*` overrides, plus `PYTHONUTF8=1` and
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
- **Host card:** written to `~/mellum-runs/r1/host-card.json` before Screen 1; its sha256 is
  recorded in each `run.json` (`host_card.sha256`) and in the step-one record.

## Step three (added 2026-11-07, before its runs)

Steps one and two are decided under the rules above: Base is Vanilla, and the mediated test lost
on budget. Their records showed what those rules could not judge: `fg-server` led on quality
(+1.42 checks, 3 full passes) but was judged only on stalls, and the mediated test stalled in most
sessions. Step three is an overnight batch that judges every unit on what it changed. The
grader identity and execution policy above still hold; the host card is refreshed before it.

- **Arms** (n = 24 each, interleaved, counted): `vanilla`; `fg-server` (`--arm worker --remedy
  guard/foreground-server`); `bounded` (`tool/bounded-commands`); `mediated+fg-server` and
  `mediated+bounded` (the same arm with `check/mediated-test` added).
- **Base.** `fg-server` and `bounded` are each judged against Vanilla on the quality rule:
  mean checks at least 1 higher, or at least 6 more full passes out of 24, with median requests and
  median output tokens each at most 20% above Vanilla's. Stalls are reported, not a gate. If both
  win, Base keeps the one with the higher mean checks (on a tie, the lower median requests). If
  neither wins, Base stays Vanilla.
- **`preset:easy`.** When Base is a unit, the mediated arm with that unit is judged against the
  Base arm by the same rule; when Base is Vanilla, both mediated arms are judged against Vanilla
  and the better winner (by mean checks) is taken. `preset:easy` is the winning mediated arm's
  units exactly as measured (its handler and `check/mediated-test`); if no mediated arm wins, it
  is Base.
- Counting is as in step one and two: every session in the means, stalled and censored ones out
  of the budget medians.

## Persuasion → enforcement

A rule fixed before the runs is the measurement's own guarantee: it can't drift toward whichever
arm happens to look good. Each unit's hook, and what it guarantees, is in the spec.

## What would falsify this

- Vanilla's stall count in step one differs widely from F.5's smoke (1 in 3). Then the stall
  rule tests a rare event, and the result says so.

## Risks

- A stall handler that also changes quality would be judged only on stalls. Mean checks is
  reported for every arm, so a quality gain or loss stays visible.
