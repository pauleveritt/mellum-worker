# Phase 1 Vanilla versus thin Baseline Worker

**At registration:** the retained six-session Vanilla Easy Phase 1 reference was
measured; the thin worker was not yet measured. The protocol below was recorded
before collection. **2026-11-03 update:** both six-session arms are now retained;
[results and limits](../../../evals/2026-11-03-worker-easy/README.md).

## Authorized comparison

Paul requested “Run the Phase 1 baseline comparison first” after agreeing six
sequential worker sessions with the existing Phase 1 Vanilla reference. Full
multi-phase collection and remedy experiments are deferred.

- Reference: `evals/2026-11-03-vanilla-easy/`, instrument `e54b6f1`.
- New arm: `worker`, thin mode extension plus recorder only. No preset, prompt
  swap, project facts, narrowed tools, guards, skills or context files.
- Six counted Easy Phase 1 attempts, fresh profiles/workspaces, native Pi 1.4.0
  and the same actual Node runtime. No selective retries. Count model errors,
  stalls and deadlines; replace only proven infrastructure failures with reasons.
- Reuse the qualified Runpod GPU, backend libraries/build, weight hash, profile,
  sampling/native output clamp, suite/oracle/checkers, 600s session deadline,
  180s open-call-age cutoff and sequential concurrency. Verify shared material
  against the reference before launch. The unrelated Mac server is now stopped;
  host load/cache differences limit elapsed-time comparison.
- Existing collector gains only explicit Vanilla/worker selection, worker source
  and activation provenance, and reference compatibility checks. Review the
  instrument delta before collection. Outcomes/scoring/execution stay unchanged.
- Quality: per-attempt hidden passed/total, code health and completion separately.
  Budget: observed provider requests, output tokens if complete, launch-to-exit
  elapsed excluding grading. Report all rows and arm counts/medians; no six-run
  token mean/total is available for Vanilla's two unknown totals.
- Reading rule: inspect any loss of all-hidden-pass or clean completion, or an
  increase in request/elapsed medians, as a diagnostic lead. Do not select a
  default or claim statistical superiority from these small independent samples.
  A “material budget” threshold is not needed for this descriptive comparison.
- Preserve raw traces, sessions, workspaces, logs and preflight; publish a unique
  research-release asset without replacing existing evidence. Commit compact
  scorecards, provenance and compatibility limitations. Update FIXES as work lands.

## 2026-11-03 outcome

Six worker attempts counted, no exclusions/replacements:5/6 hidden-all-pass,6/6
health,1 settled/5 stalled,0 passing-and-settled. Vanilla:4/6 hidden-all-pass,6/6
health,2 settled/4 stalled,1 passing-and-settled. Worker request median19.5 versus
15 and elapsed median224.776s versus202.059s. Worker output totals unknown in3/6,
Vanilla2/6. All 137 worker requests and cleanup/activation audited. No default
promoted; foreground-server handling remains an explicit next remedy to screen.

## What would falsify this

A mismatched shared input, unexpected extension/remedy, inactive worker, altered
oracle, unverified cleanup or dishonest usage total invalidates the affected
comparison. Stop for diagnosis; do not disguise it as a model result.

## Risks

Six Phase 1 sessions do not establish full-project performance. Timing includes
SSH transport and native cache behavior; shutting down an idle Mac backend may
change host pressure. Native worker requests can match Vanilla requests; this
is possible behavior, not proof of recorder failure. Known missing token totals
prevent a complete output-budget comparison. Runpod remains billable while idle.

## 2026-11-03 deep-analysis correction

Worker attempt 5 read a pre-existing host server's response and issued a successful
port-based kill. Cleanup/configuration checks did not establish run isolation;
clean-isolation interpretation is withdrawn. Counts and frozen raw artifacts stay
unchanged. All twelve initial model payloads are also identical after workspace
normalization, so request/time differences do not establish a causal worker cost.
[Detailed analysis and prerequisites](2026-11-03-baseline-deep-analysis.md).
