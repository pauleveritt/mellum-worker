# Foreground server guard: distinguish execution from mention

The user approved repairing the observed diagnostic false positive and then
working toward a trusted local remedy comparison on 2026-11-04.

## Small repair

Recognize known server executables, Python server modules/scripts and explicit
inline Python server calls. An import, package inspection, TestClient request,
printed command or source search must remain allowed merely mentioning uvicorn.
Check simple shell commands independently: a read, help query or background job
must not exempt another foreground launch in the same shell input. Keep the
existing refusal, background allowance, native accounting and opt-in remedy.

Use a small quote-aware shell word/command scanner, no dependency or subprocess.
This remains a best-effort hang-prevention heuristic, not a shell/Python parser
or security boundary. Arbitrary wrappers, generated code and dynamic imports can
hide starts; the isolated runner and open-tool deadline remain necessary.

Show diagnostic and compound-command regressions failing first, retain existing
launch/help/background cases, run the full suite and review the change. Rebuild
and qualify the contained image, including an actual diagnostic command and real
launch refusal, before new measurement. No instruction text changes.

## Measurement boundary

The comparison is a separate preregistered local Phase 1 experiment. It selects
neither a global preset nor a whole-workflow success claim. The previous cohorts
are historical and remain unchanged. Raw evidence stays local under upload hold;
all inference is stopped at the end, including failure paths.

## Result — 2026-11-04

Three diagnostic/compound-command regressions failed against the original
classifier. Review found background-pipeline/group and escaped-line regressions;
two additional tests failed before those corrections. Focused checks pass 42/42,
the repository suite passes 658/658, and independent corrected review passes
58 focused checks plus nine launch/diagnostic probes with no remaining findings.
The rebuilt image passes 27 boundary checks and 11 actual-Pi five-unit checks,
including executing the original diagnostic and recording exactly one real
launch refusal. The full suite's first invocation lacked sandbox cache/socket
access; the same suite passed with the required permissions. No model session
was counted during these qualifications.
