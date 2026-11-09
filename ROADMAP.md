# Roadmap: mellum-worker

Read [`README.md`](README.md) for what ships and [`docs/sdd.md`](docs/sdd.md)
for how work is recorded. Deferred work is in [`BACKLOG.md`](BACKLOG.md);
closed phases are in [`ARCHIVE.md`](ARCHIVE.md). One feature cycle at a time;
tangents go to the backlog, never into the current cycle.

## Now

**Active:** none; Base's cost bar is Paul's call ([count](docs/superpowers/research/2026-11-09-easy-count-result.md)).
**Next:** R.2.
**After:** R.2, R.3, then A.1, Andre's architect as an opt-in unit.
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
| **F.1** | Loading the worker registers no `delegate` tool and no nudge, proven by a payload check on Easy; dead wood outside Vanilla's closure removed after review. Housekeeping. | Delegation as an opt-in unit (A.1); any remedy; changing Vanilla. | closed 2026-11-07 — [plan](docs/superpowers/plans/archive/2026-11-07-f1-floor.md), [record](evals/2026-11-07-f1-payload/table.md). Payload check met on Easy, n = 1 each: Pi's four tools, no `delegate`, no nudge. Dead wood removed, restorable from 63b6563. |
| **F.2** | Housekeeping: the Pi extension-surface survey brought over from the old branch and corrected (the harness runs thinking on), cut to the floor's units; the backlog pruned to entries the re-boot still wants; the questions for Andre about the live tools F.1 kept. | Building any unit the survey ranks (R.1); deciding how `integration` reaches Andre; removing anything Andre has not answered on. | closed 2026-11-07 — [plan](docs/superpowers/plans/archive/2026-11-07-f2-housekeeping.md), [survey](docs/superpowers/research/2026-11-07-pi-extension-surface-survey.md). Survey re-checked on 21 units, thinking-on corrected; backlog 45 → 22 entries; four questions for Andre open in the plan. |
| **F.3** | Housekeeping, the instrument: the single-source suites from the old branch, keeping the `original` variant, and budget measured honestly in `run.json`: process elapsed time, `completion` and turns apart from requests. Proven by a Vanilla smoke on Easy. | A Vanilla baseline (Vanilla runs as R.1's interleaved control arm instead); any remedy; settle-layer timeouts and additive `entries` (with the first `check/*` arm); a stronger `qualify` (owed before any grader is cited as qualified). | closed 2026-11-07 — [plan](docs/superpowers/plans/archive/2026-11-07-f3-instrument.md), [review](docs/superpowers/research/2026-11-07-instrument-review.md), [smoke](evals/2026-11-07-f3-smoke/table.md). New fields landed; smoke n = 3, one ending on its deadline. |
| **F.4** | Infrastructure: trusted grading independent of workspace configuration; suite assertions aligned with Acceptance; complete Easy Phase 1 checks; explicit grader identity and preserved historical assertions. Deterministic positive builds and failing mutation witnesses establish repairs. | Remedies or model-rate claims; the acceptance-package port; stronger qualify; settle changes; port preflight; Pi-version recording; arbitrary hostile-code sandboxing. | closed 2026-11-07 — [plan](docs/superpowers/plans/archive/2026-11-07-suite-oracle-repairs.md), [evidence](docs/superpowers/research/2026-11-07-suite-oracle-repairs.md). Easy/Medium/Hard: 13/18/34 current checks; review findings fixed. No model-rate claim. |
| **F.5** | Infrastructure: runs we can trust on the M5 Max, ported from `lc40-thin-worker`. A per-session budget of requests and output tokens (from LC.39; Andre's `33e0b92` informs it), with wall time a censoring hang-guard; a conformance check and host card per run; the Pi version, a venv-free `PATH`, the port-8000 guard, runs outside the repo. | Remedies and the settle fix (R.1); pods, rentals and the session user (F.6); Medium/Hard baselines; model, sampling or oracle changes. | closed 2026-11-07 — [plan](docs/superpowers/plans/archive/2026-11-07-f5-run-trust.md), [note](docs/superpowers/research/2026-11-07-f5-run-trust.md), [smoke](evals/2026-11-07-f5-smoke/table.md). b12110 passes numerics (0.57%), so F.6 stays after R.1; a run counts only with `--host-card`. |
| **F.6** | Infrastructure: one held Runpod pod under F.5's budgets and its own host card (2026-11-08: narrowed from several parallel pods). LC.39's session user and rental flow, ported. Its proof is one Easy run, four arms at n = 24 on `--arm vanilla`: Vanilla, the mediated test, and each of its halves. | Parallel pods, pooling, concurrent sessions on one host; renting without the user's yes per rental; pooling pod numbers with the Mac's; new scoring. | done 2026-11-09; pod terminated — [note](docs/superpowers/research/2026-11-08-f6-held-pod.md), [count](docs/superpowers/research/2026-11-09-easy-count-result.md), [fixes](docs/superpowers/research/2026-11-09-settle-fixes-screen.md). |

### Remedies (R)

Units added one at a time on the floor, each judged on quality and budget. A
guarantee through a Pi hook comes before another sentence of prompt.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **R.1** | Easy remedy units on the M5 Max under F.5's host card and budgets, n ≥ 12, preregistered. The settle fix lands first. First, Base is earned: a stall handler and the layout fragment against plain Vanilla. Then the compile/import check and the mediated test on Base, plain Vanilla kept in the batch. [Carried detail](docs/superpowers/research/2026-11-07-roadmap-resequence.md#what-r1-carries) | Architect mode; a preset inherited from the old worker, or a Base assumed before it is measured; a rate from a screen; numbers from the ladder rig (thinking off) mixed with the harness (thinking on). | closed 2026-11-08 — [plan](docs/superpowers/plans/archive/2026-11-07-r1-easy-remedies.md), [note](docs/superpowers/research/2026-11-07-r1-easy-remedies.md), [overnight](evals/2026-11-07-r1-step-three/table.md). No unit beat Vanilla within budget: `preset:base` and `preset:easy` are `[]`. |
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
