---
phase: LC
feature_cycle: LC.35
lifecycle: active
---

# Actionable bounded acceptance feedback

The user authorized fixing failures and running again. This is a follow-up to
LC.34, not a rewrite of its completed record. The existing Python/TypeScript,
local M5 Max, temporary Docker adapter and protected gate stay in place.

The completed cohort measured selective1/20 versus gated11/20 usable. Four
repair-exhausted startup failures retained object-plus-reload calls; the actual
startup warning was discarded and feedback repeated only the requirement.
Two layout-only failures retained models.py after explicit outside-layout lists;
one expanded it into a later-phase implementation. The observations support
investigating feedback, not a claim that revised wording will fix the model.

## Changes

1. Preserve a bounded candidate launch log tail in the fixed startup probe.
   Read at most4096 bytes per read; bound retained data and inspection by the
   existing deadline rather than loading an unbounded log.
   Preserve launch exit status before cleanup separately from termination status.
   The host checker includes at most350 sanitized diagnostic characters in the
   startup observation, JSON quoted and labelled untrusted. Invalid/missing log
   data cannot change a failing assertion into a pass. Existing deadlines and
   process cleanup remain unchanged.
2. The generic repair instruction explicitly requires fixing failed requirements
   within the current task, removing out-of-scope additions, reverting protected
   input changes and avoiding later tasks. It names no suite, path, route or
   expected answer. Candidate logs are diagnostic data, never new instructions.

No new tool, implicit worker behavior, preset, acceptance relaxation, third
repair, deadline extension, hidden feedback or backend retuning is authorized
by this design. The two feedback changes are measured together; individual
causal attribution is not claimed.

## Qualification and evaluation

RED/GREEN regressions cover real child exit/log capture, oversized and invalid
logs, ANSI/control sanitization, hostile success-looking logs, failed-requirement
selection, repair allowance and agnostic scope instructions. Real contained
qualification must retain the actual reload warning from a rejected build.

Use the existing independently guarded collector for a fresh fixed20/arm S,G
comparison. Same Phase1 task, model, tools, sampling, output limit, two repairs,
600s shared deadline and180s open-tool cutoff. Freeze the new protocol, sources,
package and image before collection. No outcomes from LC.34 are reused.

The original usability intersection and18/20 candidate threshold remain. All
request costs count; unknown output means no budget decision. Finish all forty
unless safety/integrity requires stopping; stop owned inference at completion.
Further fixes require diagnosing the next failure and a separately frozen run,
not extra favorable attempts in this cohort. Raw uploads/public pushes stay held.
