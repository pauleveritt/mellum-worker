# Local remedy comparison: six sessions per arm

**What is measured:** preregistration only; no new coding session has started.
Historical local screens found 2/3 layout-only and 3/3 five-unit hidden/health/
completion passes. **What is conjecture:** the extra explicit units improve
consistency enough to earn their budget. This experiment cannot isolate an
individual unit or prove whole-workflow reliability.

## Frozen question and scope

Compare two arms on the same M5 Max Metal backend, image, model, tools, task,
checker versions, settings and deadlines. Pi 1.4.0, Vanilla plus recorder;
no worker extension. Six fresh Easy Phase 1 sessions per arm, sequential,
alternating L,S six times. No concurrent coding sessions and no optional
stopping based on favorable outcomes. Prior cohorts are not counted.

- L: prompt/name-the-layout only, once-per-task delivery.
- S: prompt/name-the-layout, prompt/python-developer, prompt/verify-the-spec,
  guard/foreground-server, context/trim-tool-output. Layout and verification
  are independent task injections; developer stays in the system prompt.

Repair the observed diagnostic guard false positive before freezing sources.
Rebuild/qualify containment and an actual-Pi five-unit interaction including the
formerly refused import command. Reuse the qualified local build 11669,
620d2225c Q4_K_M weights/hash, two 50,176-context slots, sampling 1/.95/20,
16,384 output ceiling and q8_0 K/V. Keep 600-second deadlines and 180-second
open-tool cutoffs. No remedy or prompt changes during collection.

## Reading fixed before collection

Primary quality: hidden checks passed/total, code health, settled/stalled/failed.
Also record a stricter usable result: all hidden checks, health and completion
pass, no out-of-layout writes, and the final full project pytest suite passes
with at least one test. Re-run the project suite externally after collection
using a separate isolated grader container; the worker cannot change this
verification. This is supplementary, not a replacement hidden oracle or a
claim that four hidden checks exhaust Phase 1. Report each component separately.

Budget: all inference requests and generated tokens including compaction and
thinking; sum across every counted attempt, not only successes. Report total
budget per stricter usable result, per-attempt medians, input/cache where known,
tool attempts/errors/refusals and wall time excluding setup/grading. Independent
server timings plus per-run relay boundaries reconcile requests outside normal
agent recording. Missing usage remains unknown; do not silently use partial
sums. If counters cannot reconcile, retain evidence and make no budget decision.

## Decision rule

For this specific Phase 1 iteration, an arm is a candidate I would use if it
has at least 5/6 stricter usable results, no isolation/instrumentation failure,
and reconciled inference budgets. Favor S over L only if it meets that bar,
has at least as many stricter successes, and costs no more output tokens per
stricter success. If both meet the bar and S does not earn its cost, prefer L.
If neither meets it, declare neither trustworthy for unattended use, diagnose
the actual failures, and select the next smallest general remedy rather than
promoting a preset. Requests are a separate budget tradeoff, not hidden in a
single score. Even 6/6 is modest evidence for this task, not a reliable rate.

Model stalls/errors count. Infrastructure failures remain separately retained;
a replacement may be added only for a documented non-model cause, under the
same freeze, with the original budget reported separately. Stop collection on
an isolation/integrity failure; do not mix changed infrastructure into a cohort.
Keep raw evidence locally under the user's upload hold. A task-owned server
has finally-path shutdown and an independent identity-checked time limit.

## What would falsify this

Failure to meet the stricter quality bar, budget reconciliation gaps, poorer
usable output per token, or real request feeds contradicting the selected
remedy delivery. A wider task or multi-phase failure limits any recommendation.

## Risks

One task, small n, stochastic sampling, local hardware and heuristic guards.
A project suite can be weak; separate hidden checks and supplementary audits
remain necessary. Alternation limits order drift but is not seed pairing.
