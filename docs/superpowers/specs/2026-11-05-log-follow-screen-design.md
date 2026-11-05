---
phase: LC
feature_cycle: LC.38
lifecycle: active
---

# Foreground log-follow screen

LC.37 G4 created an empty log, then started a detached server followed by
foreground tail-follow on that log. The tool stayed open180s and the artifact
still failed real startup. Prior trace confirms the file existed; this was a
live follower, not merely a missing-file error. User authorized fixing observed
failures and fresh runs without routine approval.

Add one explicit additive unit, guard/foreground-log-follow. Do not put it in
the worker or a preset. It rejects a foreground tail command with follow mode
(-f,-F,--follow or --follow=...), including clustered options, compound inputs
and common existing env/uv/timeout wrappers. Shared shell scanning/wrapper
normalization may be extracted without changing server classification. Stop
option interpretation at -- and skip -n/-c/--lines/--bytes operands. Permit
finite tail snapshots, quoted descriptions, tail help/version queries and
explicitly detached followers. A foreground follower is rejected even with a
timeout wrapper: this unit chooses finite snapshots, not indefinite observation.
Background allowance is not a process-containment guarantee.

The refusal says blocked before execution, not application output, and directs
finite log snapshots plus bounded readiness checks and owned process cleanup.
No suite path/route/value, no hidden feedback, no model prompt swap. This is a
hang-prevention heuristic; arbitrary shell/Python waits remain bounded by the
existing container watchdog/task cutoff, not certified safe by this guard.

Use the existing selected six-task screen with the prior six units plus this
one explicit guard. Default comparison arm recipe stays unchanged: append this
guard only when screen mode is selected, recording selected remedy names in
prepared/backend collection metadata. Freeze a new protocol/source/image.
Same assertions, feedback, model/hardware/sampling, two repairs,600s task,180s
tool,30s checks,8h guardian,660s reserve. No mid-cohort edits/replacements.

Test unit hook/metadata and actual blocked/allowed consumer inputs RED/GREEN.
Test screen registration includes guard while default comparison retains prior
recipe. Qualify new image and actual native Pi blocked-call transport using a
fake provider before counted inference. One fresh final review. Run all6,
report costs/semantics/unknowns and independent shutdown. Screen-only even6/6.
Correct the discovered report matcher for new blocked-before-execution refusal
wording; preserve legacy counts/deduplication and annotate prior cohorts with
dated trace audits, without changing original records, usability or budgets.

No causal/reliability promotion from a small uncontrolled screen. Further
iteration requires a material observed defect, not a disappointing sample.
