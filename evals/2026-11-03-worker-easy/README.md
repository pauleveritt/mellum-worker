# Phase 1 Vanilla versus thin Baseline Worker

**2026-11-03 deep-analysis correction:** worker attempt 5 queried a pre-existing
host server and issued a successful port-based kill command. The directory/profile
and cleanup checks did not establish execution isolation. Preserve the observed
artifact grades, counts and raw evidence; treat behavioral/budget comparisons as
exploratory with this uncontrolled interference. The cold arms also share identical
initial model payloads. See [findings and fix priorities](../../docs/superpowers/research/2026-11-03-baseline-deep-analysis.md).
The original collection summary below is retained with these qualifications.

**Measured:** six counted sequential Easy Phase 1 worker sessions on the qualified
Runpod GPU, compared descriptively with the retained six-session Vanilla reference.
**Not established:** statistical superiority, a product-default change, remedy
performance or performance across later phases.

## Quality and budget

| Metric | Vanilla | Thin worker |
| --- | ---: | ---: |
| Counted sessions | 6 | 6 |
| All four hidden checks passed | 4/6 | 5/6 |
| Code health passed | 6/6 | 6/6 |
| Settled | 2/6 | 1/6 |
| Stalled | 4/6 | 5/6 |
| All hidden checks passed **and** settled | 1/6 | 0/6 |
| Provider requests, total | 91 | 137 |
| Provider requests, median | 15 | 19.5 |
| Provider requests, range | 11–20 | 11–49 |
| Execution elapsed, total | 901.611s | 1246.636s |
| Execution elapsed, median | 202.059s | 224.776s |
| Execution elapsed, range | 16.150–223.460s | 24.326–307.669s |
| Exact output-token totals available | 4/6 | 3/6 |
| Sum of known output totals, **subset only** | 14,765 | 23,402 |
| Complete six-session output total/mean | unknown | unknown |

The worker produced one more passing artifact in these samples, but none both
passed and settled. Its median requests rose 30% and median elapsed rose 11.24%.
These are descriptive observations from small independent samples, not causal
or statistical superiority claims. All five worker stalls were foreground-server
calls. The one settled worker attempt failed all four executed hidden checks.
It returned a simplified home page missing required content/structure; settlement
and passing static health did not establish task completion.

The 49-request worker attempt repeatedly tried to start, inspect and stop its
server before its final stall. It remains counted. Five final open calls account
for approximately 903s (72%) of worker execution elapsed. Artifact correctness,
health and completion stay separate; a correct stalled artifact is not a clean
successful session. No exclusions or replacements occurred in either arm.

Elapsed means actual Pi launch-to-exit time, including open-call waits and silent
tails, excluding preflight, grading and operator classification pauses. Runpod
bills while the Pod is running, including idle/preflight time; zero provider cost
fields in the private model profile are not an invoice.

## Every worker attempt

See [scorecard](scorecard.md) and [machine-readable comparison](comparison.json).
Each run directory retains compact records, exact launch, checker diagnostics and
layout. The complete raw records/workspaces are in [raw evidence](raw-evidence.json).
The [Vanilla reference](../2026-11-03-vanilla-easy/README.md) is unchanged.

Requests 10 of attempt2, 41 of attempt5 and 11 of attempt6 returned recovered
`Connection error.` responses after substantive model work. Native Pi continued;
all three were explicitly counted with the evidence/reason retained in
[batch.json](batch.json). The exact transport cause is unproven. Missing usage
makes those attempts' output totals unknown; partial sums are not scorecard totals.
Vanilla's two error-affected totals remain unknown too.

## Shared configuration and audit

The [preregistered protocol](../../docs/superpowers/research/2026-11-03-phase1-worker-comparison.md)
fixes arms, n, scoring and interpretation. Collector source is `378217f`,
checkpoint `checkpoint-2026-11-03-phase1-worker-instrument`. The instrument delta
was independently reviewed; its sole Important finding was reproduced and fixed
RED→GREEN before collection. Full project tests passed 635/635.

The worker arm loads only the unchanged thin worker plus recorder, with
`MELLUM_MODE=1`: no preset, prompt swap, facts, narrowed tools, guards, skills or
context files. Fresh profiles/workspaces and cold Pi sessions; concurrency 1,
600s session deadline and 180s oldest-open-call cutoff. The backend retains its
qualified two-slot configuration; this is not a parallel-run measurement.

[Verification](verification.json) confirms all six native activation/runtime
identities, private profiles/record destinations, post-execution grading and
cleanup. All 137 requests used read/bash/edit/write and sampling 1/.95/20.
[Native-clamp verification](native-max-tokens-verification.json) reconstructed
all 137 requests; each retained the 16,384 output ceiling. Vanilla used the same
native policy but eight requests were reduced by context pressure.

Shared material was checked against Vanilla before launch/resume. GPU, driver,
server argv/runtime libraries, weights, Pi 1.4.0, Node 24.22.1, profile/sampling,
suite/oracle/checkers and limits matched. Only reviewed collector hashes and
intended worker arm/source provenance differed. The 84 Pi bundle/source hashes
were captured after Vanilla and are supplemental historical evidence; they were
verified before this collection. The Node binary hash is prospective; historical
Node identity is limited to its saved path/version. See manifest reference fields.

Inference ran on the Runpod RTX PRO4500 Blackwell 32 GB. Pi, tools and grading ran
on the Mac; the Mac inference server remained stopped. The same SSH tunnel was
used. Changed host pressure, warm caches, stochastic generation and three recovered
transport errors limit timing/causal interpretation. No worker span file was
emitted in headless mode without an explicit mode-off; native startup model-change
and recorder evidence establish activation and execution. Private destination
verification does not claim that a span file exists.

## Reading and next step

No default is promoted. The thin worker has not established a clean Phase 1 gain.
Foreground-server handling is the clearest next explicit remedy to screen under
the same configuration, before expanding to later phases. No remedy was applied
and no further model runs were started as part of this comparison.

Existing failure entries for foreground servers and ineffective self-checks
cover these observations; no new pathology or terminology was introduced.

## What would falsify this

Any mismatched shared input, unexpected remedy/tool/prompt, inactive worker,
altered hidden oracle, invalid cleanup or misrepresented usage would invalidate
the affected comparison. Native request/configuration and retained artifacts can
be independently checked from the published raw evidence.

## Risks

Only Easy Phase 1, one GPU/backend/model and these independent n6 samples are
covered. Unknown output totals prevent a complete token-budget comparison. The
Pod remains running and billable; collection did not authorize stopping it.
