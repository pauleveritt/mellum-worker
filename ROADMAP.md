# Roadmap: mellum-worker

Read [`README.md`](README.md) for what ships and [`docs/sdd.md`](docs/sdd.md)
for how work is recorded. Deferred work is in [`BACKLOG.md`](BACKLOG.md);
closed phases are in [`ARCHIVE.md`](ARCHIVE.md). One feature cycle at a time;
tangents go to the backlog, never into the current cycle.

## Now

**Active:** none; F.1 closed 2026-11-07 (a floor with nothing hidden).
**Next:** R.1, Easy remedies on that floor — brainstorm first.
**After:** A.1, Andre's architect as an opt-in unit.
**Parked:** everything in [`BACKLOG.md`](BACKLOG.md), each with a reopen condition; the backlog itself owes a pruning cycle.

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

### Remedies (R)

Units added one at a time on the floor, each judged on quality and budget. A
guarantee through a Pi hook comes before another sentence of prompt.

| Cycle | Ships | Excludes | Status |
| --- | --- | --- | --- |
| **R.1** | The first Easy remedy units on the floor, each measured on quality and budget. Candidates: a settle fix, a shipped mediated test, a compile/import check, bounded commands. | Architect mode; a preset inherited from the old worker; a rate from a screen. | candidate — after F.1. |

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
