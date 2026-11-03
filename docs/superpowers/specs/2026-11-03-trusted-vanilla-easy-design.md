# Trusted Vanilla Pi baseline on Easy

**Date:** 2026-11-03. **Status:** proposed design; no baseline collected.

## Intent and agreed scope

First make the documented harness path trustworthy, then retain six counted
Vanilla Pi sessions on Easy as a reference for later Baseline Worker runs.
Lower correctness or materially higher resource use in the worker is a reason
to investigate and remediate it; thresholds for that later comparison are not
part of this change. The user approved Easy only, six sessions, a 600-second
session deadline and a 180-second open-tool-call cutoff.

The baseline is pure Vanilla Pi plus the recorder. No worker, remedies,
skills, project context files, prompt changes, or recovery mechanism is added.
A stall ends the attempt; it does not unblock a command and continue coding.

## The compact scorecard

One row per attempt, with these six fields plus its run identifier:

| Quality | Budget |
| --- | --- |
| Hidden checks passed / total; distinguish checks that did not run | Model turns (provider requests) |
| Code health: pass, fail, or not checked | Output tokens |
| Completion: settled, stalled, deadline, or error | Actual elapsed time |

Hidden-test success is artifact correctness, independent of normal completion.
Code health means Ruff correctness checks and Complexipy's existing threshold;
Pyrefly remains advisory. An omitted or failed-to-start checker is never a
passing check. Preserve checker execution results so that distinction can be
verified. Do not expand the grader's requirements.

Elapsed time covers Pi execution from launch to process exit, including silent
waits, and excludes post-run grading. Never substitute trace-event span or
summed response durations for elapsed time. The 180-second cutoff measures an
open tool call's age, not time since its latest output. Record actual termination
independently of the configured limits. Require native settlement evidence for
the label settled; a process exit alone is insufficient.

Keep the underlying trace for diagnosis. Context counts, tool breakdowns, type
findings, and detailed timings stay out of the default scorecard. Shared
configuration is recorded once per batch. Do not introduce a combined numerical
quality/budget score or a leaderboard of best attempts.

## Trustworthy collection

Provide one documented suite command that selects Vanilla explicitly and
resolves the repository's Pi pin, default llama.cpp profile, grading, and the
agreed limits without hand-assembled flags. Reuse the existing harness and
backend implementation; do not create a second runner. Generic harness
capabilities may support other arms, but this collection is Easy/Vanilla only.

Before collection, qualify the existing Easy grader against known-good and
known-broken fixtures. Test the instrument using stand-in Pi processes for
success, wrong artifacts, omitted grading, provider failure, stall, deadline,
and interruption/cleanup. Each new regression test is shown failing before its
fix. Check the effective-request recorder against local Pi 1.4.0 source and a
controlled transformation test before changing it: identical Vanilla and thin
worker prompts do not by themselves prove a recorder defect.

Preflight must verify the resolved Pi version and llama.cpp backend/model
identity against the pinned configuration before counting sessions. An unhealthy
or mismatched backend stops collection with a useful diagnostic. Never kill an
unrelated server to make the port available. Do not upgrade Pi, modify the
model, alter sampling, or use an oMLX override for this baseline.

Run sessions sequentially in fresh workspaces and private profiles; keep the
hidden grader absent during execution. Verify the trace's runtime identity and
loaded extensions against the intended Vanilla configuration. Keep collection
visible, with start/completion updates; do not suppress execution evidence with
a grep/tail pipeline.

Failures, stalls, and deadlines from model execution count toward six. A proven
infrastructure failure is retained, labeled separately, and replaced; no
selective reruns of unsuccessful model attempts. A provider/runtime error after
substantive model work is not automatically an exclusion: inspect its evidence
and record the reason. All exclusions and replacements are visible.

**Builder choices:** stop the batch for diagnosis after an infrastructure
failure rather than retrying blindly; resume from retained records. Serialize
collection ownership so startup cleanup never kills another active batch.
Cleanup is scoped to identified run-owned processes. Detect and clean stale
run-owned processes before another session can inherit their ports; record
cleanup failures and stop instead of grading a potentially still-mutating
workspace. SIGKILL cannot execute a finally block, so test recovery on the next
invocation as well as graceful interruption. Never kill by server name alone.

## Preservation and reuse

Store full run directories in a dedicated ignored runs directory, not an
ephemeral temporary directory. Retain all attempts, traces, checker outputs,
final workspaces, and the shared configuration needed to diagnose them.
Commit a compact baseline record under evals/ with six counted run identifiers,
exclusions, scorecard, and provenance; do not commit trace.jsonl, stdout.txt,
or diff.patch. Raw evidence promotion follows the repository's research-release
rules; no existing evidence or archived plan is rewritten.

The batch manifest identifies the harness/recorder revision, Pi version and
executable, backend build, model weights/quantization, machine, effective
profile/sampling, checker versions, suite/grader contents, limits, and cold
context policy. Hash inputs where feasible rather than copying their contents
into every result. Include the documented collection command.

Reuse this baseline when only the worker/remedy changes. Before comparing,
verify that the task, grading, model/backend configuration, runtime, instrument,
limits, and relevant environment remain compatible. Same model ID alone is
insufficient. Machine/load/cache differences particularly limit wall-time
comparison. Do not claim permanent validity or paired trials across independent
samples. Six sessions are a local reference, not a precise rate estimate.

## Recording work and completion

Update FIXES.md as instrument changes actually land, naming what was implemented
and its verification. Add dated corrections to hypotheses contradicted by
source/tests; do not present the old transcript's prompt/guard assumptions as
measured facts. Keep planned and implemented work distinguishable. Changelog
entries accompany changes to commands, records, or documentation as required.

Finish only after the instrument checks, npm test, docs caps, and relevant
Python tests pass; the qualified, pinned collection produces six counted
sessions; cleanup is verified; and retained evidence supports the scorecard.
Worker parity, foreground-server remedies, other suites, a skill/tool entry
point, and broader telemetry are outside this phase.
