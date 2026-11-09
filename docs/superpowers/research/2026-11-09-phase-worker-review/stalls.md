# Server-stall evidence and the bounded-command decision

## For Andre

**Date:** 2026-11-09. **What is measured:** a census of committed reboot run
records and inspection of the bounded-command implementation. No new inference.
**What is conjecture:** transfer to later phases, the cheapest timeout, and
savings from preventing server launches rather than terminating them.

**Firm conclusion:** retain `tool/bounded-commands` as the explicit stall
backstop in the next phase candidate. It has strong observed support for
preventing command hangs in this configuration. It has not earned a preset,
proved cheap completion, or established Medium/Hard reliability.

### Reproduced census

The [machine-readable census](stall-census.json) lists each record path and
SHA-256, with counts by batch and suite. Scope: `evals/2026-11-07*` through
`evals/2026-11-09*` containing explicit `remedies` arrays. Group by those arrays,
not the arm name: several explicit-remedy arms are labelled `vanilla`.
Count a stall when `completion == "stalled"` or `stalled` is truthy.

| Recorded configuration | Sessions | Stalls | Medium sessions |
| --- | ---: | ---: | ---: |
| Bounded commands, alone or paired | 122 | 0 | 3 |
| Foreground-server alone | 39 | 0 | 0 |
| Foreground-server + shown-and-rerun mediated test | 24 | 7 | 0 |
| Vanilla: no remedies and `arm == vanilla` | 130 | 25 | 3 |
| Settle-only external re-run | 24 | 12 | 0 |

**Correction to the supplied tally:** 25/132 describes all no-remedy records,
including two F.1 payload probes (`bare-r1`, `worker-r1`). Plain Vanilla is
25/130. The bounded count is unchanged: 119 Easy, 3 Medium, no Hard. Every
bounded record identifies the same extension digest, `00b235c8…`; its recorded
timeout environment is unset or unavailable, not a tested nondefault value.

These are descriptive totals across different hosts, budgets and paired units;
do not pool them into a comparative rate or treat them as 122 independent tasks.
The [final Easy count](../2026-11-09-easy-count-result.md) is the clearer matched
comparison: Base 0/32 stalls versus Vanilla 7/32. A post-hoc two-sided Fisher
test gives p = 0.01084, but Base also includes settle. Bounded alone versus
Vanilla in R.1 step three is 0/24 versus 4/24, p = 0.1092. Neither result
retroactively changes that run's preregistered quality/cost decision.
Settle alone's 12/24 stalls supports retaining the timeout beside the re-run.

## Ladder run

No new session: this is a reproducible tally of existing records. No
preregistered rule accepted bounded commands specifically on stalls. Before
a deciding comparison, fix the stall endpoint, strict quality, cost, timeout
configuration and sample size. Do not rent a GPU to rediscover the mechanism.

The next local phase attempt retains bounded commands explicitly. F.8 must
first clamp the configured default as well as a model-chosen timeout and
exercise cleanup on Linux. R.1b may screen Andre's no-live-server refusal
beside the bound if the launch spiral recurs; measure accepted work and waiting
time, not merely zero stalls. Keep legitimate long-command failures visible.

## Persuasion → enforcement

[`tool_call`](../../../../remedies/tool/bounded-commands.ts) mutates bash inputs:
30 seconds when absent, and a 120-second ceiling on model-chosen numeric
timeouts. Pi's native bash timeout kills the process group, covering ordinary
foreground reloaders and `tail -f`; the harness stall cutoff here is 180 seconds.
This is a command bound, not a universal session-liveness guarantee: generation,
other tools, escaped/background processes and repeated commands remain concerns.
A shell timeout wrapper is not equivalent to this process-group mechanism.

**The current maximum is conditional.** `MELLUM_BOUND_SECONDS=300` installs a
300-second timeout when the model omits one; it bypasses the 120-second clamp.
The assertion "never more than 120" is therefore false for current code. Fix
that path before relying on the bound under arbitrary configuration.

**Preventing a hang is not preventing its cost.** The 32 counted Base traces
contain 103 bash timeouts, about 51 minutes of waiting. That is not 103 proven
server starts. Repeated launches can continue, and backgrounded servers can
hold the port; six held-port-only send-backs remain a separate failure shape.
The default could also truncate valid long work, especially on later phases;
the model can request up to 120 seconds, but the quality tradeoff is unmeasured.

**Do not substitute the current foreground-server guard.** Alone it recorded
0/39 stalls, but beside the shown-and-rerun test it recorded 7/24. Five were
`tail -f` on server logs, matching the guard's log-file suggestion. That
interaction was not measured with settle-only. The uniform bash bound covers
log-follow hangs without needing to recognise a server command.

Retain cleanup as an explicit fix to exercise: it never fired in the fixed
screens, so it has no demonstrated saving. Do not add full-test display to the
settle-only candidate or lower the send-back cap on present evidence; the
[economics ledger](evidence.md#remedy-qualifications) preserves those findings.

## What would falsify this / Risks

A current-digest session stalling in bounded bash under a valid timeout below
180 seconds would challenge the mechanism and needs its trace, Pi version and
process tree. Strict-pass losses from valid long commands could outweigh the
stall benefit. Zero observed stalls does not establish zero future risk, and
neither this census nor a new rule can retroactively accept Base.
