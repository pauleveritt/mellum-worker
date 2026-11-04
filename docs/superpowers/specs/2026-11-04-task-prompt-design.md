# Task-scoped layout instruction

Approved in conversation on 2026-11-04: implement the once-per-task injected
prompt behavior proposed for `prompt/name-the-layout`.

## Behavior

The optional remedy adds one visible `Injected` custom message alongside the
task brief. It leaves the user's text, system prompt and tools unchanged.
Subsequent requests retain that one instruction instead of appending the line
to every user message. Other prompt remedies retain their existing behavior.

With the worker installed, a task is one activation span, including additional
user turns in `/mellum on` mode. No instruction is supplied while the worker is
off. Without the worker, a task is one user-initiated Pi run, including tool
turns and automatic continuations until settled. This supports Vanilla screens.

Enabling the remedy during a task supplies one instruction in the next request.
Disabling it removes its custom messages from outgoing context. A new task gets
a new instruction; old instructions stay in the transcript for inspection but
are excluded from later tasks' outgoing context. Session changes clear local
task state. Context compaction may remove the original message; subsequent
requests in the same task restore one copy without adding repeated transcript
entries. No periodic reminder or failure-triggered nudge is added.

The worker exposes its active span through Pi's internal event bus, solely as
lifecycle information. It installs no remedy. Its marker filter distinguishes
an explicitly labelled injected instruction from the user task, so injection
after the on-marker cannot cause the original brief to be discarded.

## Verification

Show regressions failing before implementation. Cover Vanilla task boundaries,
tool continuations, compaction, worker on/off and repeated spans, mid-task
enable/disable, unchanged task/system/tools and marker-filter composition.
Check actual pinned Pi against a local deterministic provider; no GPU or
counted evaluation is needed. Run the repository suite and docs caps.

## Evidence boundary

This changes delivery, not the instruction text. Older five-unit and guard-only
screens remain unchanged. The new delivery has no coding-quality measurement
until a new screen runs; no preset or default is promoted.

## Result, 2026-11-04

Implemented for name-the-layout only. Seven lifecycle regressions were observed
failing against the original delivery before implementation; all now pass.
Repository suite:647 passed,0 failed. Actual Pi1.4.0 RPC verification with an
isolated profile and deterministic local provider passed12 checks over20
requests: two Vanilla tasks, parent isolation, worker continuation/new span,
disable/re-enable, task text preservation and visible injections. A mid-run
toggle delivered the instruction in the next request and persisted/displayed it
once without starting another turn. Review identified the initial missing
late-injection display; a regression failed first and the corrected publication
passed review.
The same verifier rejected the old delivery because it changed the task text.
Raw local verification lives in runs/2026-11-04-task-prompt/ (not coding evidence).
No GPU was started. Historical experiment records and other prompt units were
not changed. Requalify the measurement image before any new counted collection.
