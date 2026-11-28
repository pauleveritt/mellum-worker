# M.7C: Pi harness telemetry smoke

**What is measured:** exactly two rung-1 attempts on 2026-10-11 (America/New_York;
trace UTC dates are October 12), one Mode and one delegated Worker, at source
commit `b108aac`. Both passed the existing task and unchanged-tests checks.
Deterministic replay proves unchanged legacy scoring and shipped guard decisions.

**What is conjecture:** compatibility beyond these paths and any reliability,
performance or Pi-version advantage. These are instrumentation checks, not rates.

| Attempt | Task check | Requests | Tool executions | Parsed chunks | Process elapsed | Telemetry |
| --- | --- | --- | --- | --- | --- | --- |
| [Mode](rung1-baseline-mode-guards-r1/run.json) | pass; tests unchanged | 8 | 7 | 98 | 10.26 s | ok |
| [Worker](rung1-baseline-delegated-guards-r1/run.json) | pass; tests unchanged | 7 child | 6 child | 116 child | 27.19 s, including parent | ok |

Both used isolated Pi **1.1.0**, Node **v24.3.0**, shipped prompt v5 and guards.
The delegated host revision was `8983754bb3ef6603cbbe46dcc2314ec8563ffc23`.
The selected executable was `/tmp/mellum-runs/pi110-hello-ny6sfma5/runtime/node_modules/.bin/pi`;
its canonical package entry was under
`/private/tmp/mellum-runs/pi110-guards-o9x_4230/runtime/node_modules/@earendil-works/pi-coding-agent/`.
The observed child entry matched the selected executable's canonical target.
Rung 1 uses JavaScript: Node preflight passed and fixture Python was not applicable.
No global installation or server configuration changed.

Every Mellum request had `max_tokens=16384`, thinking and preserve-thinking on,
and temperature/top_p/top_k **1/0.95/20**. The read-only setup check passed
binding model settings, global settings and provider checks. The server profile
cap of 4096 and `forced_ct_kwargs=null` were request-overridden values;
`thinking_budget_tokens` and `max_tool_result_tokens` were null. The setup check
reported memory ceiling 48 GB as advice (14 GB advised), not a binding failure.

## Reconstruction

Read `run.json` for launch argv/runtime, runner outcome and task checks; then
join raw events by `(instanceId, requestId)` and native `toolCallId` within that
instance. Each attempt has one observed Mellum instance, continuous sequence,
no association issue and no open execution. Every assistant's visible text
matches the concatenated parsed content chunks for its request; its normalized
message retains stop reason, usage and native duration. Mode's final duration
was 489 ms; Worker's was 2898 ms. All tool executions have native durations
(Mode 1–111 ms; Worker 1–114 ms).

Both processes exited 0 without deadline or signal; observed Mellum settlement
was true and native aborted was false. These facts are separate from task checks.
Worker's trace contains only child provider events; the parent's final report
and lifecycle are in stdout and the process summary. Its parent independently
ran the tests. `final.md` for Worker is the parent's report, not the child's
normalized final; the latter is the last assistant `message_end` in its trace.
There were zero tool errors and nudges in either attempt. No reruns were needed.

Raw review covered the public calculator fixture, rendered agent prompt,
parent/child replies, tool data and ambient host skill descriptions/paths.
No auth/settings files or credential-bearing headers were included. Local
user, workspace paths and public host metadata remain in the evidence.
The deterministic archive contains only the six trace/stdout/diff files;
each archived member was checked byte-for-byte against its source.

SHA-256: `a62352518e2497950e28e5edb7037033781d8208b0115461aca07cef6df32fae`.
Runtime/source/archive provenance is also recorded in [PROVENANCE](../PROVENANCE.md#m7c-telemetry-smokes).

## What would falsify this

A runtime mismatch, incomplete trace, broken per-request reconstruction,
changed replay score or observer-induced guard/payload change invalidates
that part of the compatibility proof. Another host path requires its own evidence.

## Risks

Parsed hooks are not wire capture. Synchronous tracing adds overhead; timings
are descriptive only. Parent provider payloads are not captured for Worker.
These two successful tasks do not establish a reliability gain or a shipped
minimum Pi version. Broader scorer work remains M.7D; policy work remains M.7E.

Raw traces, stdout and diffs: [`smoke-m7c.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-11/smoke-m7c.tar.gz).
