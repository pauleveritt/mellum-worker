# Roadmap: mellum-worker

Read [`README.md`](README.md) for what ships and [`docs/sdd.md`](docs/sdd.md)
for how work is recorded. Deferred work is in [`BACKLOG.md`](BACKLOG.md);
closed phases are in [`ARCHIVE.md`](ARCHIVE.md). One feature cycle at a time;
tangents go to the backlog, never into the current cycle.

## Now

**Active:** none; F.4 is closed, and the order below was [re-sequenced](docs/superpowers/research/2026-11-07-roadmap-resequence.md) on 2026-11-07.
**Next:** F.5, runs we can trust on the M5 Max; `integration` was synced to `origin/main` and `origin/remove-omlx` on 2026-11-07 (`e881e1d`, `a146ca9`).
**After:** R.1, F.6, R.2, R.3, then A.1, Andre's architect as an opt-in unit.
**Parked:** everything in [`BACKLOG.md`](BACKLOG.md), each with a reopen condition.

## Direction

A small model stays out of the ditch when it runs as a **bounded worker with
deterministic controls**, built on Pi's extension hooks: a gate refuses, a check
runs, a payload is exactly what the command line names. Prompt text is
persuasion; it has a role, on top of that bounded worker, never as what holds it
up. **Budget counts the same as quality**: wall time, turns and context size are
reported beside pass/fail, and budget guardrails are enforced, not requested.

## Feature cycles

### Floor (F)

Plain Pi plus the recorder, and the worker as a command tool that adds nothing
by default, so every later unit's effect can be credited to it.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **F.1** | Loading the worker registers no `delegate` tool and no nudge, proven by a payload check on Easy; dead wood outside Vanilla's closure removed after review. Housekeeping. | Delegation as an opt-in unit (A.1); any remedy; changing Vanilla. | closed 2026-11-07 — [spec](docs/superpowers/specs/2026-11-07-worker-without-delegate-design.md), [plan](docs/superpowers/plans/archive/2026-11-07-f1-floor.md), [record](evals/2026-11-07-f1-payload/table.md). Payload check met: `worker` and `bare` on Easy sent Pi's four tools, no `delegate`, no nudge (n = 1 each). Orphan extensions, `dashboard/` and `HANDOVER.md` removed, each restorable from 63b6563. |
| **F.2** | Housekeeping: the Pi extension-surface survey brought over from the old branch and corrected (the harness runs thinking on), cut to the floor's units; the backlog pruned to entries the re-boot still wants; the questions for Andre about the live tools F.1 kept. | Building any unit the survey ranks (R.1); deciding how `integration` reaches Andre; removing anything Andre has not answered on. | closed 2026-11-07 — [plan](docs/superpowers/plans/archive/2026-11-07-f2-housekeeping.md), [survey](docs/superpowers/research/2026-11-07-pi-extension-surface-survey.md). Survey re-checked on 21 units, thinking-on corrected; backlog 45 → 22 entries; four questions for Andre open in the plan. |
| **F.3** | Housekeeping, the instrument. The single-source suites and their test brought over from the old branch (16cf9f9, 7b791ff, 9105bd4), keeping the `original` variant; budget measured honestly: elapsed time from the process, whether the deadline fired (`completion`) in `run.json`, turns distinct from requests. Proven by a Vanilla smoke on Easy, n = 1–2, that lands the new fields, one of them on a deadline. | A Vanilla baseline (Vanilla runs as R.1's interleaved control arm instead); any remedy; settle-layer timeouts and additive `entries` (with the first `check/*` arm); a stronger `qualify` (owed before any grader is cited as qualified). | closed 2026-11-07 ([plan](docs/superpowers/plans/archive/2026-11-07-f3-instrument.md), [review](docs/superpowers/research/2026-11-07-instrument-review.md), [smoke](evals/2026-11-07-f3-smoke/table.md)). Suites single-source with `original` kept; `execution.json`, `completion`, process `wall`, turns apart from requests, and `context` with the cached prefix (a third error the smoke found). Smoke n = 3: two settled at 48.6 s and 41.4 s, one `deadline` at 20.0 s (7 turns, 8 requests). Open for R.1: `run.json` names no Pi version. |
| **F.4** | Infrastructure: trusted grading independent of workspace configuration; suite assertions aligned with Acceptance; complete Easy Phase 1 checks; explicit grader identity and preserved historical assertions. Deterministic positive builds and failing mutation witnesses establish repairs. | Remedies or model-rate claims; the acceptance-package port; stronger qualify; settle changes; port preflight; Pi-version recording; arbitrary hostile-code sandboxing. | closed 2026-11-07 — [spec](docs/superpowers/specs/2026-11-07-suite-oracle-repairs-design.md), [plan](docs/superpowers/plans/archive/2026-11-07-suite-oracle-repairs.md), [evidence](docs/superpowers/research/2026-11-07-suite-oracle-repairs.md). Easy/Medium/Hard: 13/18/34 current checks. Nine independent-review findings fixed; npm 643 passed, 3 skipped; ladder 223 passed; twelve historical fixture controls matched. No model-rate claim. |
| **F.5** | Infrastructure: runs we can trust on the M5 Max, ported test-first from `lc40-thin-worker`. The primary budget is requests and output tokens, enforced per session (from LC.39; Andre's `33e0b92` informs it). Wall time is a loose hang-guard, and a run that hits it is censored and reported apart. Also: the conformance check and a host card that each `run.json` links to, rerun on the Mac's current llama.cpp; the Pi version in `run.json`; a native `PATH` without the harness venv; the port-8000 leftover guard; runs outside the repo. Proven by a host card and a Vanilla smoke on Easy. | Remedies and the settle fix (R.1); pods, rentals and the session user (F.6); Medium/Hard baselines; model, sampling or oracle changes. | candidate — after the `origin/main` sync. If the Mac fails conformance again (Metal perplexity NaN at b11669 in LC.39), F.6 moves before R.1. |
| **F.6** | Infrastructure: parallel runs on rented pods under F.5's budgets and host cards. LC.39's session user and rental flow; several pods, one session each at a time; pooled only where the conformance rule allows. | Concurrent sessions on one host; renting without the user's yes per rental; remedies. | candidate — before R.2, where Medium and Hard batches take hours on one host. |

### Remedies (R)

Units added one at a time on the floor, each judged on quality and budget. A
guarantee through a Pi hook comes before another sentence of prompt.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **R.1** | The first Easy remedy units on the floor, each measured on quality and budget, on the M5 Max under F.5's host card. Plain Vanilla is the control arm, interleaved with each unit in the same batch (no older baseline), n ≥ 12, preregistered; quality from the current Phase 1 checks with grader identity fixed before runs; budget is requests and output tokens, with censored runs reported apart (F.5). The settle fix lands first. Candidates: a compile/import check, a shipped mediated test, and one stall handler (the bash bound, the fixed foreground-server guard or the log-follow guard). | Architect mode; a preset inherited from the old worker, or a bound folded into the control; a rate from a screen; numbers from the ladder rig (thinking off) mixed with the harness (thinking on). | candidate — after F.5. Preregister the assertion digest and execution policy. Old four-check rates do not transfer to the repaired thirteen-check oracle; establish quality and budget together in the new batch. Re-sequenced 2026-11-07 ([note](docs/superpowers/research/2026-11-07-roadmap-resequence.md)): budget moved from F.3's wall deadline to requests; `PATH` moved to F.5; stall candidates from LC.41 and `f0e31ea`. |
| **R.2** | Medium remedy units, opened by a Vanilla baseline on the repaired 18-check oracle in the same batch. The mediated-test screen preregistered on the old branch (`20c538b`) is the first candidate. | Units chosen before Medium's own Vanilla batch; architect mode. | candidate — after F.6. |
| **R.3** | Hard remedy units, opened by a Vanilla baseline on the repaired 34-check oracle in the same batch. | As R.2. | candidate — after R.2. |

### Architect (A)

Andre's delegate/architect mode: most likely the route from Medium to Hard, and
the only way Mellum becomes the main agent.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **A.1** | Andre's `delegate` tool and architect path as an opt-in unit on the floor, measured on quality and budget. | Default-on delegation; claims carried over from screens on the old suites. | candidate — after an Easy remedy tranche (R); the code stays on `main`. Inherits Andre's 2026-11-07 leads: finer steps at budget 3 is a negative (0/18, `efdba03`); architect-direct is a wash on Easy and untested on Medium (`33e0b92`). |

## Gates

A feature cycle closes under [the SDD closing rules](docs/sdd.md#closing-a-feature-cycle):
its plan records the result and is archived, roadmap/backlog state is current,
the suite and document caps pass, and claims match the evidence they cite. A
phase closes when every row is closed or superseded; its section then moves
verbatim to [`ARCHIVE.md`](ARCHIVE.md). Releases separately require matching
tags, package and README versions, and a changelog section.
