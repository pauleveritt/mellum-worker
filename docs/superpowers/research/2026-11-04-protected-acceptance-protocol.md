# Protected acceptance: fixed overnight comparison

Registered before any counted task. Implements the
[approved design](../specs/2026-11-04-protected-acceptance-design.md).
Scope: Easy Phase 1, fresh workspaces on the local M5 Max, sequential inference.
No later-phase, concurrency or hosted-performance claim follows from this run.

## Arms and fixed sample

Twenty tasks per arm, alternating S,G twenty times. S enables
`prompt/name-the-layout`, `prompt/python-developer`, `prompt/verify-the-spec`,
`guard/foreground-server`, `context/trim-tool-output`. G adds only
`check/external-acceptance`. Both use Vanilla Pi plus recorder as their floor;
neither loads the worker extension. Prompt fragments remain once per task.

G permits two repair continuations and at most three settle checks, followed
by an independent final artifact check with no further inference. One 600s
deadline covers generation, snapshots, checking and repair; a check gets at
most 30s and only remaining task time. Open-tool cutoff remains 180s.
S receives the identical external package as a final audit, without feedback.
Hidden-grader output is never sent to either arm.

## Usability and decision

A usable task must settle normally, pass every hidden check with checks
actually run, pass all code-health checks, preserve the allowed layout and
pass the complete external acceptance package, including nonempty passing
project tests and actual documented startup. G must also have host status
`accepted`, covering the final independently checked snapshot.

G is a candidate only with at least 18/20 usable tasks, at least as many
successes as S, and no greater total output tokens per usable task than S.
Report requests separately, totals including unsuccessful tasks, medians,
per-task distributions, repairs/rescues and Wilson 95% intervals. At zero
successes, per-usable budget is undefined. Unknown inference output or an
incomplete cohort yields no decision. No favorable optional stopping,
post-hoc changes to the criterion, or substituted model failures.

Infrastructure failures are retained separately with their budgets. This
controller stops on an integrity/cleanup failure and reports an incomplete
cohort rather than silently replacing an attempt. A later replacement study
requires an explicit dated registration; this conservative stopping policy
does not manufacture forty outcomes after broken measurement.

## Qualification and freeze

Before launch: immutable image build, containment/hidden-grader qualification,
two correct acceptance variants and individual seeded omissions, hostile
candidate observations, actual-Pi pass/repair/exhaust/tamper exchanges and
forced compaction accounting. Setup uses a fake provider and is not evidence
of Mellum quality. Record all qualifications, package/source hashes and image.

Use the controlled6 llama.cpp build 11669/620d2225c argv and weight SHA256,
Pi 1.4.0, model alias, profile, tools and sampling unchanged. Two server slots
remain configured but only one coding task runs at a time. Verify runtime
hashes, full Metal offload, live props/slots and a short native generation
before registration. Recheck frozen sources/profile and backend each task.

The host relay counts every POST completion; server timings sum every
generation, including thinking, errors, compaction and repairs. Recorder
events classify ordinary and compaction requests. Missing or unmatched
timings yield unknown total output, never a partial budget claim. Keep setup
generations outside per-task log segments; keep repair interval receipts.

## Safety, evidence and interpretation

An independent watchdog stops the owned server eight hours after launch,
or on controller death. Do not start a task with less than 660s remaining.
Normal and exceptional exits stop owned inference and clean recorded
containers/volumes. Recovery uses host controls, never model-exported JSON;
save partial files before removing a model container. Refuse an occupied
port and never stop unrelated listeners. Verify shutdown independently.

Retain local traces, request logs, snapshots, checks and failures in ignored
`runs/`; curate summaries into `evals/` only. Raw upload remains on hold.
Audit welcoming tone/hero semantics manually and label these structural
proxies; passing finite checks is not proof of arbitrary correctness.
No defaults or presets are promoted automatically by this experiment.
