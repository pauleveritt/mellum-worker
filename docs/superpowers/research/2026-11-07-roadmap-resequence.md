# Re-sequencing the roadmap after F.4: what `integration` was missing

## For Andre

- **What this is:** a check, before opening R.1, of the branches touched since 2026-11-04 against
  `integration` (@`b3fc45c`). R.1's row was written before three days of results were carried over,
  so it would have measured remedies on a floor missing decisions that were already made. Nothing
  was run.
- **The main change is the budget.** `integration` still reads budget off a wall-clock deadline
  (F.3's `completion`), which depends on the host. Our call, from LC.39's request and token
  budgets: from F.5 on, the primary cost is requests and output tokens. Wall time is a loose
  hang-guard, and a run that hits it is censored: reported on its own line, never averaged in.
  Your `33e0b92` reached a similar position from the delegate screens. It informs this choice,
  and where our measurement differs (output tokens beside requests, budgets enforced per
  session), we'll say why.
- **The new order:** sync `integration` to `origin/main` (your three commits) and `remove-omlx`, then F.5 (runs we
  can trust on the M5 Max), R.1 (Easy remedies), F.6 (parallel pods), R.2 Medium, R.3 Hard, A.1.
- **What to look at:** `origin/remove-omlx` lands with the sync (below); whether F.6 belongs
  before R.2.

**What is measured.** Nothing new. Every figure below cites a record that already exists:
LC.39's portable floor (`lc40-thin-worker`, `evals/2026-11-05-portable-floor`), the
single-source baselines (`evals/2026-11-06-single-source-baselines`), and `33e0b92`'s screen
(n = 3 per arm, scratch driver).

**What is conjecture.** That F.5's port is enough for R.1 to trust its numbers, and that Easy on
one Mac is fast enough without pods. The second assumption rests on one batch: 24 Easy sessions
in about 42 minutes on 2026-11-06.

## Ladder run

None. This note changes the order of the work, not a setting. F.5 proves itself with a host card
and a Vanilla smoke on Easy; R.1 keeps its preregistered n ≥ 12 batch.

## Persuasion → enforcement

The new order puts enforcement under the instrument before any remedy is measured. A request
budget enforced at the provider is a hard stop the model cannot argue with; a conformance check
refuses a host whose numerics are wrong before any session counts. R.1's candidates are then
ranked by which hook could reach the failures that prompt text did not: `tool_result` for
compile/import errors, settle for the mediated test, and the bash tool for the stall.

## What `integration` was missing

| Source | What | Where it lands |
| --- | --- | --- |
| `origin/main` `33e0b92` | Andre's position: requests, not seconds, as the cost; wall time as a loose hang-guard; censored runs reported apart | sync; informs F.5's budget, which is our own choice |
| `origin/main` `f0e31ea` | `guard/foreground-server` blocks a server start, not a command that names one (6/6 runs converged, a lead) | sync; an R.1 stall candidate |
| `origin/main` `efdba03` | Finer plan steps at budget 3 is a negative (0/18) | A.1 |
| lc40, LC.39 | Request/token session budgets, the conformance check and host card, a session user | F.5 (budgets, check, card); F.6 (session user, rentals) |
| lc40, LC.39 | The Mac failed conformance (Metal perplexity NaN at llama.cpp b11669), yet every later run used it | F.5 reruns the check on the current build |
| lc40, LC.41 | A native `PATH` without the harness venv (`7adeaa5`), the port-8000 leftover guard (a stray server answered for 13 hours, across three batches), runs kept outside the repo | F.5 |
| lc40, LC.41 | `tool/bounded-commands` (a 30 s default bash timeout) and LC.38's log-follow guard | R.1 stall candidates |
| lc40, 11-07 | `check/mediated-test` and Medium's mediated tests, built and dry-run; the screen is preregistered (`20c538b`) but has not run | R.1 (Easy), R.2 (Medium) |
| lc40, overnights | Title override and the Phase 4 id miss are habits prompt text did not fix; Hard's 0/34 was a `SyntaxError` | R.1's ranking |

`lc39-portable-floor` and `paul/initial-fixes` are already in `lc40-thin-worker`; nothing on them
is new.

## Calls made here (for review)

- **R.1's control is plain Vanilla**, as `AGENTS.md` defines the floor. The bash bound is
  measured as a unit, not folded into the control as lc40's `base.json` did.
- **Easy stays on the M5 Max.** Pods set up slowly (LC.40 found setup cost about as much as the
  cohort), and they pay off only in parallel, which matters for Medium and Hard.
- **F.6 rather than a new phase** for the pods: it is floor infrastructure.

## `origin/remove-omlx`, scheduled with the sync

Andre's branch (2026-11-05, not merged) removes the oMLX path and makes llama.cpp on :8001 the
default. `integration` still names oMLX in the README, `run_ladder.py` and `scripts/screen.sh`.
Paul cleared it on 2026-11-07, so it lands in the sync step, after `origin/main`, and F.5 names
llama.cpp as the floor's backend. A test merge shows conflicts in `AGENTS.md` and `CHANGELOG.md`.
It also edits four files that F.1 removed (the dashboard and `content-tool-call-assist`), and
those deletions stand.

## What would falsify this

- F.5's Vanilla smoke shows the Mac still non-conformant on the current llama.cpp. Then Easy
  needs a pod after all, and F.6 moves before R.1.
- An R.1 arm whose request counts disagree with its wall time by more than load explains. That
  would mean requests do not measure the cost a user feels.

## Risks

- Porting from lc40 brings code across one cycle at a time; anything not named here stays on the
  reference branch.
- The 42-minute figure is one batch on the old harness and the pre-F.4 oracle.
