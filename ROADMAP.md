# Roadmap: mellum-worker

Read [`README.md`](README.md) for what ships and [`docs/sdd.md`](docs/sdd.md)
for how work is recorded. Deferred work is in [`BACKLOG.md`](BACKLOG.md);
closed phases are in [`ARCHIVE.md`](ARCHIVE.md). One feature cycle at a time;
tangents go to the backlog, never into the current cycle.

## Now

**Active:** none; F.3 closed 2026-11-07 (single-source suites, honest budget).
**Next:** R.1, Easy remedies with Vanilla as the interleaved control — brainstorm first.
**After:** A.1, Andre's architect as an opt-in unit.
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

### Remedies (R)

Units added one at a time on the floor, each judged on quality and budget. A
guarantee through a Pi hook comes before another sentence of prompt.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **R.1** | The first Easy remedy units on the floor, each measured on quality and budget. Vanilla is the control arm, interleaved with each unit in the same batch (no older baseline), n ≥ 12, preregistered; quality read from the full Phase 1 acceptance package, since Easy's hidden checks sit at the ceiling; budget from F.3's fields. Candidates: a compile/import check, a shipped mediated test, bounded commands, `PATH` via `spawnHook`. | Architect mode; a preset inherited from the old worker; a rate from a screen; numbers from the ladder rig (thinking off) mixed with the harness (thinking on). | candidate — next. Cross-check: Vanilla on corrected Easy near the old branch's 11/12 hidden all-pass says the port is faithful. |

### Architect (A)

Andre's delegate/architect mode: most likely the route from Medium to Hard, and
the only way Mellum becomes the main agent.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **A.1** | Andre's `delegate` tool and architect path as an opt-in unit on the floor, measured on quality and budget. | Default-on delegation; claims carried over from screens on the old suites. | candidate — after an Easy remedy tranche (R); the code stays on `main`. |

## Gates

A feature cycle closes under [the SDD closing rules](docs/sdd.md#closing-a-feature-cycle):
its plan records the result and is archived, roadmap/backlog state is current,
the suite and document caps pass, and claims match the evidence they cite. A
phase closes when every row is closed or superseded; its section then moves
verbatim to [`ARCHIVE.md`](ARCHIVE.md). Releases separately require matching
tags, package and README versions, and a changelog section.
