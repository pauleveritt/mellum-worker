# Contained Phase 1 retry and five-unit remedy screen

**Measured at registration:** a fresh RTX PRO4500 Pod is RUNNING, and SSH reads
its real GPU/CUDA identity. The corrected containment proof passed27 checks.
**Conjecture:** quality and budgets of the fresh cohorts, and whether the
five-unit bundle helps. No counted session of this retry has started.

## Authorization and infrastructure

Paul requested another attempt, authorized higher GPU cost if needed, and
suggested five remedy units. The existing A40 and original4500 could not restart
for host capacity; a fresh A40 placement also failed. The live catalog reported
LOW RTX PRO4500 stock in EU-RO-1 at $0.72/hour. A fresh Pod `5ztijjtwz1l4i5` was
created there and read back RUNNING with that price, image
`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, 20GB container disk,
50GB `/workspace`, SSH only and Jupyter disabled. The image came from the existing
account Pod reads. Registered account SSH keys include Paul's RSA public key.

SSH reported NVIDIA RTX PRO4500 Blackwell,32623MiB, driver595.91.07,
compute capability12.0, UUID `GPU-3bfa2a97-d533-79dc-7d3e-db354b15464a`,
CUDA toolkit12.8.93. Runpod allocated28 vCPUs and62GB system RAM. Rebuild the
pinned llama.cpp11669/620d2225c for120a with native tuning disabled; download the
same pinned GGUF and verify its SHA. Qualify/freeze its actual hashes and serving
identity before any counted run. No timing comparison with other hosts is causal.

## Fixed arms and reading

Follow the [original6+6+1 protocol](2026-11-03-contained-phase1-study.md), with
the updated Pod and this explicitly revised exploratory arm:

1. Six cold sequential Vanilla Easy Phase1 sessions, recorder only.
2. Six cold sequential thin Worker Easy Phase1 sessions against that completed
   Vanilla reference; command/mode+recorder only, no old bundled preset.
3. One cold Vanilla Easy Phase1 screen loading exactly, in this order:
   `prompt/name-the-layout`, `prompt/python-developer`, `prompt/verify-the-spec`,
   `guard/foreground-server`, `context/trim-tool-output`.

The first points the model to the project's own paths; the second supplies a
focused developer role; the third asks it to verify all requirements and tests;
the guard blocks foreground server hangs; the context unit trims eligible text
tool results to8000 characters plus a retrieval note. None names a suite path,
route or expected value. Existing units are unchanged. Test actual five-unit
loading/interaction through contained Pi with a fake provider before the screen.
The two-unit screen registered earlier did not run; this five-unit screen
supersedes it for the present retry.

All arms share corrected contained image
`sha256:4079657911571b9a008b2ce97a0195c4c827f6cadc88289605df15e927291d56`
and its [stronger proof](2026-11-04-contained-a40-study/qualification.json).
Keep pinned Pi1.4.0, model/weights, two50k slots but session concurrency1,
sampling and native output semantics,600s deadline,180s open-call cutoff and
original four-check oracle. Mac runs Pi/harness/tools; Pod GPU runs inference.
No Mac GPU. The prior interrupted A40 attempt remains separate, including its
model stall and infrastructure failure.

Record hidden passed/total, code health, completion, model turns/provider
requests, complete output usage or unknown, full/uncached context and actual
execution elapsed excluding grading. Retain all model failures/stalls/deadlines;
retain/classify infrastructure failures before any replacement. Stop for unresolved
integrity or attribution. Four checks do not establish whole-phase acceptance.

The6-versus6 comparison is descriptive compatibility evidence: cold requests may
match, so budget differences do not establish wrapper overhead. The n=1 bundle
is an exploratory lead: it cannot attribute an effect, establish rates or select
a shipped default. A later one-unit contrast is needed to explain improvement.

## Five-unit interaction qualification

The [actual-Pi probe](2026-11-04-contained-retry-study/five-remedy-qualification.json)
passed7/7 checks: all five extensions loaded in the specified order; all three
prompt fragments appeared in the provider payload; the foreground Uvicorn call
was blocked; a12000-character tool reply was trimmed to8000 plus the retrieval
note; Pi settled normally. This used a local fake provider and establishes
interaction/loading only, not coding quality. An initial probe had the wrong
profile port and made no provider request; that failure is retained separately.

## Shutdown

A live MCP guardian stops this new Pod on workflow completion/blocker or at
14:49:15UTC on November4 (90 minutes from creation, including setup). Verify
EXITED after stopping. Existing Pods remain stopped; no extra worker is created.
Keep persistent files; their storage continues billing. Do not leave compute on
while reporting or preserving evidence after a terminal outcome.

## Partial4500 outcome and continuation correction

This host produced three retained counted Vanilla attempts: one4/4/health pass
settled in46.828s; one200.129s foreground-server stall with unavailable hidden
checks and health pass; one61.707s settled mixed failure. The third added
`uvicorn` to project dependencies without updating the lockfile, preventing
offline checker provisioning. Two recovered502s correlate with host-relay
upstream `ECONNRESET`; output/full-context totals remain unknown. It is counted
conservatively after substantive work, preserving both model and transport
failures; no selective replacement. This is a partial cohort, not n=6 evidence.

The controller initially promoted the third attempt's review pause to a terminal
blocker; the guardian stopped the Pod and verified EXITED. Its host then refused
restart for capacity. The [PRO6000 continuation](2026-11-04-contained-pro6000-study.md)
uses a fresh full cohort and a local controller that holds a routine review for
explicit classification (maximum three minutes), rather than treating every
review as terminal. The measured harness/image and scoring policy are unchanged.

## Final retained record

The [partial scorecard and provenance](../../../evals/2026-11-04-contained-retry-partial/README.md)
retain all three counted attempts (75 requests,308.664s; cohort output unknown),
actual sent16384-token limits, five-unit interaction proof and subsequent setup
failures. No completed6+6 baseline comparison or counted remedy screen exists.
All five Pods are verified EXITED; persistent storage remains billable.

## What would falsify this

Backend/input drift, unexpected extensions, unqualified checker launch, missing
cleanup/usage evidence or an altered grader invalidates affected claims.

## Risks

Capacity may disappear after stop. Setup consumes the90-minute ceiling. n=1 is
small and five units confound attribution; the hidden oracle covers only four
requirements. Docker is temporary and changes the execution environment.
