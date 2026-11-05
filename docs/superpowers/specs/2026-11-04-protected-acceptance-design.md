# Protected external acceptance with bounded repair

## Intent and authority

LC.34 makes a worker's final answer provisional until an external acceptance
check passes. The user requested implementation and an overnight plan after
the [controlled comparison](../../../evals/2026-11-04-local-controlled6/README.md)
left the best selective arm below its trust bar. This design is proposed for
review; no implementation or overnight collection has started.

The user chose an explicit additive remedy, protected external tests, bounded
repairs, local inference, complete budget reporting and shutdown at completion.
The numerical limits and implementation choices below are the author's calls.
The hidden grader remains an independent outcome measure; its code, results
and failures never become repair feedback.

## What this builds

An opt-in `check/external-acceptance` remedy asks a trusted external controller
to verify the current task before allowing completion. A failed acceptance
check returns a bounded diagnostic and continues the same Pi task. The worker
extension, existing presets and Vanilla floor gain no implicit behavior.

The first supported adapter is the existing temporary contained measurement
backend. Without a qualified external controller, enabling this remedy is a
configuration error before inference, never an unprotected local fallback.
Docker remains a temporary experiment adapter, not a required product backend.

An operator supplies a frozen acceptance package derived from the task's
written requirements. The generic remedy/controller contains no suite route,
filename or expected answer. Suite-specific checks live separately from both
the generic gate and the hidden grader.

## Protection and the completion decision

The host owns the package hash, task identity, deadline, repair allowance and
receipt journal. None lives in model-writable storage as an authority. The
acceptance package is absent from the model container and available read-only
in a fresh grading container. The model container has no Docker socket, host
filesystem, credentials or control over the checker command.

At `agent_before_settle`, the remedy posts an opaque check request and waits.
A narrow mailbox transported through Docker exec is sufficient; it grants no
general host execution or extra network route. The host selects the workspace
from its own task identity, freezes the model container, safely exports a
regular-file snapshot, records its hash, then resumes the container. Verification
runs on a separate copy; test side effects cannot alter the worker's files.
Only one request is outstanding; duplicate/stale IDs or excess requests fail
closed. Every exchange and verdict has a host-owned sequence and task ID.

The mailbox is untrusted. A model-side success message, changed counter or
forged acknowledgement cannot mark the task accepted. After Pi exits, the host
freezes/exports the final artifact and independently checks it again. It accepts
only a successful complete check of that exact snapshot, under the same frozen
package. That recheck consumes time, but no inference or additional repair.

Tests, runner and result plumbing must be protected from candidate execution:
do not import candidate code into the process that owns the authoritative
assertions or receipt. Runtime probes execute candidate code in a separate
unprivileged process/container; the trusted checker owns assertions over their
bounded observations. No project `conftest.py`, pytest configuration, plugin,
environment or import path may replace the checker. Read-only test files alone
are insufficient if imported candidate code can skip/assertion-patch the tests.
Probe transports carry data, not code to execute in the controller.

This guards the measured coding worker and its tools, not arbitrary kernel or
container-runtime exploits. Adversarial application behavior can defeat a
finite behavioral test; do not call passing this package proof of correctness.

## Bounds and outcomes

- At most **two repair continuations** after the initial generation: at most
  three settle checks, plus one final independent artifact recheck.
- One **600-second task deadline**, including inference, snapshots, checks and
  repairs. Never reset it at redispatch. Each check has at most **30 seconds**
  and is capped by remaining task time. Open coding tool cutoff stays **180s**.
- Repairs keep the same session, task identity, model, tools, sampling and
  remedies. Existing once-per-task injections do not multiply on repair.
- Feedback includes only acceptance requirement IDs, observed failures and
  at most **8,000 characters**, never hidden-grader output. It does not expose
  the checker source, commands chosen by the model or an editable oracle.
- Check statuses: `pass`, `fail`, `checker_error`, `timeout`, `integrity_error`.
  `fail` means a requirement assertion failed; an incomplete check list,
  missing result, lost transport, stale ID or malformed receipt cannot pass.
- Task statuses: `accepted`, `repair_exhausted`, `deadline`, `stalled`,
  `model_error`, `checker_error`, `integrity_error`. Pi settling is recorded
  separately and cannot substitute for acceptance.
- An exhausted repair budget still gets its last check. Never stop checking
  merely because no further continuation is available. Model aborts/errors
  do not trigger recovery generations or become accepted on artifact quality.
- Checker/integrity errors stop the task; no blind repair or fail-open settle.
  An integrity failure stops the batch. Checker failures are retained and
  reviewed before any replacement under an unchanged freeze.

## Acceptance package and qualification

The package declares a schema version, spec hashes, stable requirement IDs,
check timeout and immutable runner/probe files. The host records all hashes
before collection and verifies them after each check. Successful process exit
without every expected requirement result is an error, not a pass. Requirements
may have multiple checks; report the coverage map rather than claiming that a
raw check count proves completeness.

The initial package covers Easy Phase 1 only. Its matrix maps every explicit
Phase 1 clause and applicable project constraint to an automated check or a
stated judgment limit. Include FastAPI root application; actual home response;
shared Jinja layout; HTML5/lang/viewport; Bootstrap 5 CSS and bundle placement;
favicon; default title and page override; navbar brand and links; hero/tagline
and welcoming paragraph; guarded reload and actual bounded startup; nonempty
passing project tests; preserved base inputs and phase-appropriate layout.
Do not demand a Phase 2 route merely because Phase 1 navigation links to it.
Semantic wording such as "welcoming" gets an explicitly limited structural
proxy and independent manual audit, not an undocumented exact-string rule.

Qualify before live authority: at least two valid variants (including optional
HTML attributes, reordered markup and differing lawful title block names),
empty/broken outputs, and one seeded omission per requirement. Include startup
with an app object plus reload, hard-coded title, request-parameter 422,
import-time server launch, missing tests, configuration/plugin injection,
early `exit(0)`, forged receipt and package mutation attempts. Every valid
variant must pass and every targeted omission must be rejected for its mapped
requirement. A qualification miss blocks collection; fix and requalify before
freezing. Do not copy requirements from hidden-grader implementation.

## Evidence and budget

Retain initial and each repaired snapshot, check results, host journal, bounded
feedback, trace, relay boundaries, final independent check and provenance.
Record task completion and acceptance separately. Report before/after quality
and the number rescued by repair, including cases the gate passes but hidden
grading or independent manual review rejects.

Count all provider requests and generated tokens, including thinking,
compaction, failed requests and unsuccessful repairs. Preserve unknown usage
as unknown. Associate each request with the task and repair interval; reconcile
against host relay boundaries and llama.cpp timing. Qualify forced compaction
on the actual pinned Pi, because the current native recorder has a known blind
spot. No budget conclusion if reconciliation fails. Report total/per-task
requests and tokens, tokens per accepted-and-independently-usable task, repair
overhead, input/cache where known and actual elapsed time. Setup/probe inference
is retained separately from counted tasks.

## Proposed overnight protocol

Prerequisite: implementation, red/green tests, independent code review,
checker mutation qualification, containment qualification and actual Pi
pass/fail/repair/exhaustion/compaction probes all pass. Freeze all sources,
images, model and checker packages before the first counted task.

Preregister **six fresh tasks per arm**, sequential and alternating S,G:
S is the prior selective five remedies, G is S plus the new gate. Evaluate both
arms with the same final acceptance package, hidden grader, code-health checks,
layout and external project-test rerun. Only G receives acceptance feedback.
Keep the M5 Max, Pi 1.4.0, llama.cpp build 11669/620d2225c, Q4_K_M hash,
two existing 50,176-context slots, sampling 1/.95/20, output ceiling 16,384
and q8_0 K/V unchanged; coding concurrency remains one.

Primary usable outcome requires all acceptance requirements, all hidden checks,
health, layout, nonempty project tests, settled un-aborted completion and no
integrity issue. Report each component as well as the intersection. G is only
a Phase 1 candidate if it reaches at least **5/6 usable tasks**, has at least
as many usable tasks as S, and uses no more total output tokens per usable task
than S (undefined when there are none). Report request cost separately. If
neither meets the rule, promote neither; no extra retries or mid-batch fixes.
This small single-task experiment cannot establish multi-phase trust.

Proposed independent batch limit: **two hours from inference-server launch**,
including live qualification. This limit is pending the user's timing answer;
do not treat silence as approval. A batch cut short is incomplete, not six
failures or a favorable smaller cohort. No new task starts without its full
600-second allowance plus 60 seconds for cleanup. Setup builds happen before
starting inference. A separate identity-checked watchdog and finally-path
cleanup stop owned inference and containers on success, failure or cutoff.
Verify no owned listener/container/volume remains. Never kill unrelated
listeners. No Runpod resource is started. Raw evidence stays local under the
user's upload hold.

## Excludes and open decision

No new prompts, retuning, extra remedies, parallel coding, later phases,
automatic preset promotion, grader rewrites or hosted spend. No claim that
old verify/acceptance extensions now satisfy this protected contract.

Only the overnight hard-stop preference remains a user decision. Other values
above are proposed engineering defaults, available for correction at review.
