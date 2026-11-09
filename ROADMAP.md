# Roadmap: mellum-worker

Read [`README.md`](README.md) for what ships and [`docs/sdd.md`](docs/sdd.md)
for how work is recorded. Deferred work is in [`BACKLOG.md`](BACKLOG.md);
closed phases are in [`ARCHIVE.md`](ARCHIVE.md). One feature cycle at a time;
tangents go to the backlog, never into the current cycle.

## Now

**Active:** none; the [2026-11-09 review](docs/superpowers/research/2026-11-09-phase-worker-review.md) records the evidence and replan.
**Next:** F.8, a verified phase boundary; [F.7](docs/superpowers/research/2026-11-09-f7-qualify-acceptance.md) is closed.
**After:** R.1a, one local Easy phase; R.1b, one cost candidate; R.2, the Medium phase workflow.
**Parked:** R.3 and A.1 until Medium delivers useful accepted phases; other work remains in [`BACKLOG.md`](BACKLOG.md).

## Direction

A small model stays out of the ditch when it runs as a **bounded worker with
deterministic controls**, built on Pi's extension hooks: a gate refuses, a check
runs, a payload is exactly what the command line names. Prompt text is
persuasion; it has a role, on top of that bounded worker, never as what holds it
up. **Budget counts the same as quality**: wall time, turns and context size are
reported beside pass/fail, and budget guardrails are enforced, not requested.

**2026-11-09 direction:** implement Easy or Medium one requested phase at a
time, from the last verified checkpoint. Keep our stronger grading and budget
controls when reconciling Andre's work. Acceptance repairs precede a watched
local trial; economics count all attempts per accepted phase. The failed Easy
verdict and empty presets stand. [Decisions and evidence](docs/superpowers/research/2026-11-09-phase-worker-review.md).

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
| **F.7** | Qualified phase acceptance: map written requirements to checks, version Medium's status-label correction, close the cross-path ID coverage gap, and replay positive/negative builds. Reconcile Andre's tests while retaining our stricter grading. | New model sessions; changing historical scores; deleting legitimate requirements to match incomplete grading; runtime remedies. | closed 2026-11-09 — [note](docs/superpowers/research/2026-11-09-f7-qualify-acceptance.md), [plan](docs/superpowers/plans/archive/2026-11-09-f7-qualify-acceptance.md). Medium 19 checks, Easy four-phase bundle, both maps enforced; original grader retained. No model run. |
| **F.8** | A verified, bounded phase boundary: explicit gate verdicts, trusted execution and supplied-test integrity, closed handover exposure, clamped command bounds, grade-on-budget and verified checkpoints. Reuse the flow's machinery. | New orchestration architecture; new default remedies; acceptance-rate or savings claims from unit checks. | candidate — after F.7; [boundary findings](docs/superpowers/research/2026-11-09-phase-worker-review.md), [stall evidence](docs/superpowers/research/2026-11-09-phase-worker-review/stalls.md). Fix the default-clamp bypass; exercise cleanup on Linux. |

### Remedies (R)

Units added one at a time on the floor, each judged on quality and budget. A
guarantee through a Pi hook comes before another sentence of prompt.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **R.1** | Easy remedy units on the M5 Max under F.5's host card and budgets, n ≥ 12, preregistered. The settle fix lands first. First, Base is earned: a stall handler and the layout fragment against plain Vanilla. Then the compile/import check and the mediated test on Base, plain Vanilla kept in the batch. [Carried detail](docs/superpowers/research/2026-11-07-roadmap-resequence.md#what-r1-carries) | Architect mode; a preset inherited from the old worker, or a Base assumed before it is measured; a rate from a screen; numbers from the ladder rig (thinking off) mixed with the harness (thinking on). | closed 2026-11-08 — [plan](docs/superpowers/plans/archive/2026-11-07-r1-easy-remedies.md), [note](docs/superpowers/research/2026-11-07-r1-easy-remedies.md), [overnight](evals/2026-11-07-r1-step-three/table.md). No unit beat Vanilla within budget: `preset:base` and `preset:easy` are `[]`. |
| **R.1a** | One watched local Easy Phase-2 attempt from a strict-passing Phase-1 checkpoint, with an explicit bounded/settle candidate and qualified cumulative acceptance. Record cost, integrity and the accepted checkpoint under the current Easy budget. | Preset promotion; a whole-roadmap rate; an automatic batch or GPU rental; raising the budget to finish. | candidate — after F.8; [trial](docs/superpowers/research/2026-11-09-phase-worker-review.md#ladder-run). One success establishes presence only. |
| **R.1b** | One cost/interaction candidate screened against corrected Base on the same phase. Andre's no-live-server is first if the spiral recurs; think-briefly is a separate follow-up. Record accepted work, all-attempt cost and tails. | A bundle of changes; fresh-context savings assumed from trace subtraction; retroactive acceptance; default or preset promotion from a screen. | candidate — after R.1a; [economics](docs/superpowers/research/2026-11-09-phase-worker-review.md#economics-and-remedy-choices). Choose the smallest informative screen; no automatic large count. |
| **R.2** | Medium requested one phase at a time, with qualified strict acceptance, cumulative regressions and accepted checkpoints. Diagnose Phase 4 from a known-good Phase 3 if needed, then test the sequence from its own work; comparative claims retain Vanilla. | Crediting seeded success as end-to-end success; transfer from Easy; deleting requirements absent from the hidden grader; architect mode. | candidate — after useful Easy phase work; [review](docs/superpowers/research/2026-11-09-phase-worker-review.md). Supersedes the automatic post-F.6 batch; original n=3 scores stand. |
| **R.3** | Hard remedy units against their own Vanilla floor, after qualified acceptance and a useful Medium phase workflow. | Transfer of Medium rates; an automatic overnight or larger-rung architecture run. | parked — reopen when R.2 delivers accepted phases within a declared cost ceiling; [review](docs/superpowers/research/2026-11-09-phase-worker-review.md). |

### Architect (A)

Architect/delegation remains an opt-in scaling question. Andre's one-pass lead
does not establish the paired architecture comparison; a larger-than-four-phase
experiment follows useful phase work rather than blocking it.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **A.1** | Andre's delegate/architect path as an opt-in unit, compared with one agent on matched contracts, reasoning instructions and all-attempt cost; test larger specs only when scaling is the question. | Default-on delegation; a fivefold saving treated as a paired result; replacing the phase-at-a-time user goal. | parked — after useful Medium phase work and an observed scaling limit; [reconciliation](docs/superpowers/research/2026-11-09-phase-worker-review.md). Earlier architecture leads remain historical. |

## Gates

A feature cycle closes under [the SDD closing rules](docs/sdd.md#closing-a-feature-cycle):
its plan records the result and is archived, roadmap/backlog state is current,
the suite and document caps pass, and claims match the evidence they cite. A
phase closes when every row is closed or superseded; its section then moves
verbatim to [`ARCHIVE.md`](ARCHIVE.md). Releases separately require matching
tags, package and README versions, and a changelog section.
