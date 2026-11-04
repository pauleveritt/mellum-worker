# Baseline deep analysis: isolation, acceptance and failure mechanisms

**Date:** 2026-11-03

**Question:** Is anything serious enough to fix before further counted runs?

**Measured:** retrospective inspection of twelve retained Phase 1 sessions,
source/configuration and their native requests, tool results and final artifacts;
fifty additional read-only health requests, with no inference.

**Inference:** future containment and remedy choices need qualification; this
analysis does not establish a remedy's effectiveness or a causal worker penalty.

## Findings

### 1. Critical: a run contacted and signaled a pre-existing host service

**Fact.** Worker attempt 5 (`20261103T233814Z-easy-73b011`) ran the following:

| Request | Retained evidence |
| --- | --- |
| 36 | `ps aux` showed PID 36820 running `uvicorn app:app --reload --port 8765`, started at 1:10 PM; the current attempt began 18:38 EDT. |
| 38 | `lsof` identified port 8765 listeners PID 36820 and 36822. |
| 39 | `curl http://localhost:8765` received a 1,194-byte AgentClinic page, different from this attempt's home template. |
| 46 | `kill $(lsof -t -i :8765)` returned success. The model also attempted broad `pkill -f` commands. |

The external page entered subsequent provider request history. Its original
workspace or originating session was not captured; its start time establishes that it predates
this attempt. The model's own app used port 8000. This is observed interference,
not merely a theoretical risk of parallel runs.

The harness gives the child a fresh directory, private Pi profile and process
group, then sweeps owned workspace processes after execution. It does not confine
native read/bash access to the host filesystem, processes or network. Cleanup
success therefore establishes cleanup of the current run, not run isolation.
Even sequential sessions can inspect or signal unrelated services.

**Effect on evidence.** The current artifact was written before the external
page was fetched; the hidden grader later imported the current workspace in
process. Its 4/4 hidden-check result remains a valid observation of that artifact.
Its behavioral/request/time record is affected by an uncontrolled external
service. Preserve the sample and raw evidence; do not silently remove it or claim
an uncontaminated comparative execution. Other sessions were not shown to contact
port 8765, but the shared host boundary was equally available to them.

**Recommendation.** Establish filesystem/process/network containment for all
native agent tools before unattended or parallel collection. Qualify it with an
unrelated sentinel service that remains unreachable/unkillable from a run. Keep
this a general runner guarantee; a command-name blacklist or a prompt warning
would not establish the boundary. Requalify the environment and collect a new
reference before promotion claims. Existing records remain exploratory evidence.

**Sources:** worker raw trace requests 36/38/39/46 and subsequent payloads, via
[raw provenance](../../../evals/2026-11-03-worker-easy/raw-evidence.json);
[runner source](https://github.com/pauleveritt/mellum-worker/blob/378217f0b10b588a702c1ccb409488a7f00531b0/learn/code/harness.py#L476);
[compact evidence](2026-11-03-baseline-deep-analysis/evidence.json).

### 2. Important interpretation: cold-session arms have no initial payload contrast

**Fact.** All twelve first provider payloads have one identical canonical hash
after replacing only the exact workspace path. No timestamp or other setting
was removed. The worker's pinned filter, reapplied to all 137 observed worker
payloads with its actual headless options, changed none of them.

**Inference and limit.** The recorder sees post-worker payloads, so reapplication
is an idempotence check, not a complete pre/post capture. Source and cold history
explain the result: no parent conversation/on-marker requires isolation; the
thin worker preserves Pi's system prompt/tools/reasoning and adds no remedy.
The comparison exercises wrapper activation/compatibility, not two different
coding strategies. The observed +30% request median cannot be attributed to the
worker from these small independent cohorts. No default was promoted.

**Recommendation.** Use the floor as the reference for explicit additive remedy
screens. Test history isolation separately with a controlled parent-history
contract; a cold task cannot demonstrate that benefit. Avoid another whole cold
worker batch merely to chase these medians.

**Sources:** [payload hashes and normalization](2026-11-03-baseline-deep-analysis/payload-equivalence.json);
[worker filter options](https://github.com/pauleveritt/mellum-worker/blob/378217f0b10b588a702c1ccb409488a7f00531b0/extensions/mellum-worker.ts#L575).

### 3. High usability failure: verification becomes a foreground server

**Facts across these twelve sessions:**

- Nine stalled on a server call: 4 Vanilla and 5 worker.
- Final unresolved calls consumed 722.1 s of 901.611 s Vanilla execution (80%) and
  903.0 s of 1246.636 s worker execution (72%). Time outside those final waits was
  179.511 s and 343.636 s; this is not a GPU-time estimate.
- Seven of those nine had already received `Do not: start servers` by reading
  the workspace notes. A prose rule was available and was not sufficient here.
- Only one session wrote a test file and invoked pytest. It is the only session
  that both passed all hidden checks and settled.
- All three hidden-check failures lacked any tool result showing the roadmap.
  All nine hidden-all-pass artifacts had read it. This is descriptive association,
  not proof that forced reading alone fixes the task.

**Recommendation.** After containment, screen one explicit foreground-server
remedy; keep it separate from spec discovery and verification remedies. Blocking
a server does not establish that the model will run tests or satisfy the spec.
Preserve Vanilla as the unmodified floor. The 180 s cutoff is an instrument limit,
not a repair that lets the model continue afterward.

**Sources:** [requirements/test visibility](2026-11-03-baseline-deep-analysis/reading-and-accounting.json);
[per-run evidence](2026-11-03-baseline-deep-analysis/evidence.json);
[workspace notes](../../../learn/code/suites/easy/base/AGENTS.md). Matching tool-call
IDs against results agreed with the collector's FIFO calculation in all twelve;
there is no observed false-stall attribution in this sample.

### 4. Important acceptance limit: four home checks do not cover the whole phase

**Fact.** The fixed oracle checks the response/tagline, doctype, language and
navigation links. The roadmap also specifies a functioning reload startup
command, shared layout, responsive viewport, CDN assets, favicon and other
structure. The hidden score does not independently establish every requirement.

**Concrete counterexample.** Worker attempt 1 passed 4/4 and health. Its
`uvicorn.run(app, reload=True)` startup failed at requests 18 and 20 with exit 3:
`You must pass the application as an import string to enable 'reload' or 'workers'.`
It then launched uvicorn by CLI and stalled. Passing hidden checks did not imply
that the documented `python app.py` entry point worked.

**Recommendation.** Continue labeling 4/4 as hidden-check coverage, not complete
Phase 1 acceptance. Audit the acceptance contract before a broader product claim;
any expanded oracle is a new version applied symmetrically to future arms.
Do not change the frozen grader or retroactively rescore these sessions.

**Sources:** [fixed oracle](../../../learn/code/suites/easy/grader/test_phase1_home.py),
[roadmap](../../../learn/code/suites/easy/base/specs/roadmap.md), worker attempt 1
raw requests 18/20, [static artifact inventory](2026-11-03-baseline-deep-analysis/coverage.json).

### 5. High measurement gap: recurring transport errors lack root-cause evidence

**Fact.** Six `Connection error.` events occurred across five of twelve sessions
(6/228 observed provider dispatches). Each had zero recorded SSE events and a
3–158 ms error duration. Native Pi subsequently continued. Missing usage affects
three worker and two Vanilla totals; current unknown labeling is conservative.
No observed SSE event does not prove the server generated zero tokens.

The pinned provider formats the normalized error into a message, while the
OpenAI client can retain a nested transport cause. That cause/response-boundary
information was not preserved in these traces. OOM, SSE parsing, SSH resets,
connection reuse and local fetch failures cannot be distinguished from the
recorded string. Fifty health GETs through the same tunnel and Node 24.22.1 all
returned 200; those non-streaming reads do not clear the historical errors.

**Recommendation.** Before a token-budget comparison, record a redacted error
cause chain/code, request/response boundary and correlation IDs across client,
tunnel and server. Diagnose with a small uncounted transport qualification; do
not add retries or alter transport silently inside a frozen measurement.

**Sources:** [event summaries](2026-11-03-baseline-deep-analysis/evidence.json),
[health-probe scope/result](2026-11-03-baseline-deep-analysis/transport-probe-summary.json),
pinned Pi bundle `dist/bundle/chunks/openai-completions-27RKPL37.js` (hash in the
reference manifest), installed OpenAI `client.mjs:770–840`. Root cause unverified.

### 6. Reporting bug: legacy context is uncached input, not full prompt size

**Fact.** `report()` takes max native `usage.input`, excluding cached prompt
usage. For example, worker attempt 4 records context 1596 while a raw provider
usage event reports 8,120 prompt tokens; attempt 5 records 6,957 versus 28,989. This
field understates the real context footprint on cache hits.

The separate native max-output audit used native session context, not this field,
and verified all 228 dispatches across the two arms. This reporting defect does
not invalidate that audit or the known output totals.

**Recommendation.** In a future instrument revision, derive full prompt size
from raw provider usage or a verified sum of native input/cache components.
Keep uncached input as a separate diagnostic and test cached-request fixtures.
Retain current raw records and publish a dated derived correction.

**Sources:** [cached-token comparisons](2026-11-03-baseline-deep-analysis/reading-and-accounting.json),
[report source](https://github.com/pauleveritt/mellum-worker/blob/378217f0b10b588a702c1ccb409488a7f00531b0/learn/code/harness.py#L788).

## Recommendation and confidence

Block further unattended/parallel counted runs on containment. Instrument the
transport boundary and repair context reporting before stronger budget claims.
Then requalify and retain a fresh safe reference, screen foreground-server handling
as one explicit unit, and assess spec discovery/verification independently.
Confidence is high for the observed host interference, payload equivalence,
foreground calls, startup counterexample and context undercount; transport root
cause and remedy effectiveness remain unknown. No model/GPU retuning is justified
by this evidence alone.

## What would falsify this

A complete provenance record showing port 8765 was owned by this attempt, absence
of its response from later payloads, differing canonical initial requests, or
contradictory raw usage/startup outputs would change the corresponding finding.
A clean sandbox qualification or measured remedy can support a future result;
it does not erase the observed events here.

## Risks

The sample is small and the affected run was not prospectively isolated. Static
checks do not establish full acceptance. The old server's exact originating
workspace is unknown. A repeated quiet health probe cannot identify an intermittent
streaming failure. Archived counts, raw assets, graders and plans are preserved;
the comparison's clean-isolation interpretation is withdrawn, not its raw facts.
