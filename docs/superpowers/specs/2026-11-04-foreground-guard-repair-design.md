# Foreground guard and refusal-accounting repair

## Approved scope

Paul requested fixing the two defects observed in the H100 screen, then
rerunning the remedied arm. Preserve the thin worker and five additive units.
This is a small repair; existing containment and run procedures are reused.

## Behavior

Recognized server CLI help/version queries terminate without starting a server
and must pass the guard. Permit simple direct invocations, including the
observed `uv run --frozen uvicorn --help`, uv flag wrappers and Python module
invocations. Keep the exemption narrow: an arbitrary script may ignore help,
and compound commands or substitutions must not gain an exemption merely by
containing a help flag. Existing real foreground starts remain blocked;
existing background forms remain allowed. No suite-specific paths or answers.

Pi emits a blocked call's refusal in `tool_execution_end`, without a tool
`message_end`. The report must count this event, retain legacy tool-result
message support, and deduplicate by Pi instance and tool-call ID. Repeated
provider history and assistant quotations are not additional refusals.
Historical run records remain unchanged; derived audits can cite the repair.

## Verification and rerun

Show each regression fail before its fix. Verify help passes, real starts and
compound bypass attempts remain blocked, native refusals count exactly once,
and different calls/instances count independently. Run the repository suite.
Rebuild and qualify the contained image, including a real Pi fake-provider
interaction that permits help and blocks a genuine start with count1.

Rerun the same five-unit Vanilla Easy Phase1 n=1 screen, recording changed
source/image identity and preserving the earlier6+6+1 comparison. Requalify
the inference backend; reuse the H100 freeze if the original GPU returns.
If hardware changes, record a separate backend and make no causal timing claim.
Retain failures and unknown usage, publish reviewed evidence, and stop/read back
the Pod immediately when done or blocked. This single screen selects no default.
