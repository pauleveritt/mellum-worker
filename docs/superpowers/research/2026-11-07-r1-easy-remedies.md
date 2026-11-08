# R.1: Easy remedies, Base earned first — results

## For Andre

- **What this is:** R.1's measured result, under its
  [preregistration](2026-11-07-r1-preregistration.md) and [spec](../specs/2026-11-07-r1-easy-remedies-design.md).
  Every number below is a counted Easy session (13 checks, host card, budget proxy, thinking on).
- **Base is Vanilla, and so is `preset:easy`.** Across three counted steps no unit beat plain
  Vanilla Pi within the 20% budget limit. Both presets are `[]`.
- **The mediated test buys quality at three times the cost.** With it, 15 and 18 of 24 sessions
  passed all 13 checks, against none for Vanilla; median requests were 47 and 61, against 21.
- **What to look at:** the stall result in step three (Vanilla 4 of 24, each handler 0), which
  the step-three rule reported but did not judge; and whether the mediated test's cost can come
  down without losing its full passes.

**What is measured.** 216 counted Easy sessions, 2026-11-07 to 08: Screen 1 (15), step one (48),
Screen 2 (9), step two (24), step three (120, n = 24 per arm). M5 Max, llama.cpp b12110, Pi
1.4.0. Records: [Screen 1](../../../evals/2026-11-07-r1-screen1/table.md),
[step one](../../../evals/2026-11-07-r1-step-one/table.md),
[Screen 2](../../../evals/2026-11-07-r1-screen2/table.md),
[step two](../../../evals/2026-11-07-r1-step-two/table.md),
[step three](../../../evals/2026-11-07-r1-step-three/table.md).

**What is conjecture.** Why the mediated arms keep working after they pass (a reading of
traces, below); whether the shown test steers the model toward a foreground launch; anything
about Medium or Hard.

## Ladder run

Harness, Easy, `scripts/r1_batch.py` interleaving arms round-robin. Each screen (n = 3) only chose
the arms of the counted batch that followed it.

| Step | Arms | Decision |
|---|---|---|
| Screen 1 | vanilla, bounded, fg-server, log-follow, layout | log-follow dropped: its guard never fired |
| Step one (n = 12) | vanilla, bounded, fg-server, layout | nothing wins; `preset:base` is `[]` |
| Screen 2 | vanilla, compile-import, mediated-test | compile-import dropped: its hook never fired |
| Step two (n = 12) | vanilla, mediated-test | the mediated test loses on budget |
| Step three (n = 24) | vanilla, fg-server, bounded, mediated + each | nothing wins; `preset:easy` is `[]` |

**Step one:**

| Arm | Mean checks | Full passes | Stalled | Median requests | Median output tokens |
|---|---|---|---|---|---|
| vanilla | 10.58 | 0 | 1 | 16 | 6,285 |
| bounded | 10.83 | 1 | 0 | 20.5 | 7,687 |
| fg-server | 12.00 | 3 | 0 | 19 | 6,818 |
| layout | 9.50 | 0 | 2 | 16.5 | 6,026 |

**Step two:** Vanilla 10.67 mean checks, 0 full passes, 2 stalled, 15.5 / 6,683 median;
mediated-test 10.33, 4 full passes, 10 stalled, 29.5 / 21,505. The mediated test cleared the
quality bar (+4 full passes) and failed budget.

**Step three:**

| Arm | Mean checks | Full passes | Stalled | Budget endings | Median requests | Median output tokens |
|---|---|---|---|---|---|---|
| vanilla | 11.33 | 0 | 4 | 1 | 21 | 7,842 |
| fg-server | 11.38 | 2 | 0 | 0 | 21 | 7,246.5 |
| bounded | 12.04 | 5 | 0 | 0 | 22.5 | 7,967.5 |
| mediated+fg-server | 11.04 | 15 | 7 | 12 | 47 | 27,028 |
| mediated+bounded | 11.75 | 18 | 0 | 20 | 61 | 25,787 |

The bar for a handler was +1 mean check or 6 more full passes. `bounded` missed by one full
pass, and `fg-server`'s step-one lead (+1.42 checks) did not hold at n = 24 (+0.05). The mediated
arms cleared quality and failed budget, at 47 and 61 median requests against a 25.2 limit.

## Persuasion → enforcement

- The settle layer now guarantees what it only seemed to: each red check's message reaches the
  model (`agent_before_settle` entries are appended) and a hung check is stopped with its
  process group. Unit-tested; it changes no measured number here.
- `bounded-commands` (`tool_call`) and `fg-server` (`tool_call` block) are enforcement. Alone,
  each arm stalled in none of 24 sessions against Vanilla's 4, but the step-three rule did not
  judge stalls. `bounded` bounds every call, so it guarantees no stall. `fg-server` refuses only a
  foreground server start: with the mediated test on, it stalled 7 times, 5 on `tail -f` (the
  log-follow pathology Screen 1 dropped at n = 3) and 2 on `find /`.
- `name-the-layout` is persuasion. Shown once per task, it did not beat Vanilla.
- `compile-import` (`tool_result`, settle) never fired in its screen: a `SyntaxError` occurred in
  1 of 15 Screen 1 sessions and none of its three.
- The mediated test is enforcement at settle plus persuasion at the start. The enforcement is
  what moves full passes from 0 to 15–18 of 24; the cost is that the model keeps working. 32 of 48
  mediated sessions ended on budget, though 33 had reached 13/13 on the hidden grade.

## Why the mediated arms run long (read from traces)

- The test is a superset of the oracle. Its extra checks are what most often sent the model
  back: a page's own `<title>` block, the `app.py` launch with reload, and the project's own tests.
  26 of 48 final workspaces pass the mediated test; the other 22 ended red, on budget or a stall.
- **Our defect, fixed (`eaf48a3d`).** When the model's own server already held the port, the
  launch check reported an empty log, and the model went hunting for running servers. It hit 10
  of 48 sessions. It cannot carry the budget result alone.
- Sessions that re-dispatched zero times still reached 64 requests: showing a 13-test file at the
  start seems to set a higher bar for "done" on its own. That is a reading, not a measurement.

## Leads (not results)

- **Stall handlers on the stall rule.** At n = 24, Vanilla stalled 4 times and each handler none;
  step one's stall rule would have admitted both. A preregistered run that judges stalls again
  would settle it.
- **A cheaper mediated test.** The budget, not quality, decided against it. Tests that track the
  oracle more closely, a lower re-dispatch cap, or ending at green may keep the full passes for
  less.
- **The shown test as a hint.** Step two's foreground launches followed a test that launches the
  app the same way.
- **Log-follow, again.** Screen 1 dropped `guard/foreground-log-follow` because its guard never
  fired in three sessions; step three's mediated+fg-server arm stalled on `tail -f` in 5 of 24.

## What would falsify this

- A second counted Vanilla batch at n = 24 with 6 or more full passes: then Vanilla's 0 was a
  draw, and the mediated test's quality gain is smaller than it looks.
- A handler meeting the quality rule in its own preregistered batch.

## Risks

- n = 24 sees moderate effects only; `bounded` missed by one full pass, which is inside the noise.
- The budget limit is relative to Vanilla's median, so a cheaper Vanilla batch moves every
  verdict with it.
