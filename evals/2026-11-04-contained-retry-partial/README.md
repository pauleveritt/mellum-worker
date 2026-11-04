# Partial contained Vanilla retry and five-unit interaction probe

**Measured:** three counted cold Vanilla Easy Phase1 attempts on one frozen
RTX PRO4500 backend, actual-Pi five-remedy interaction checks, setup failures
on later hosts, and final shutdown. **Conjecture:** a completed n=6 Vanilla rate,
Worker comparison, or coding benefit from the five remedies. None was collected.

## Partial quality and budget

| Attempt | Hidden checks | Health | Completion | Turns / requests | Output tokens | Execution seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 132947Z-9c1f17 | 4/4 | pass | settled | 25 /25 | 8,128 | 46.828 |
| 133039Z-0b7304 | not run (0/4) | pass | stalled | 17 /17 | 2,991 | 200.129 |
| 133405Z-3fff8a | not run (0/4) | not checked | settled | 33 /33 | unknown | 61.707 |

All three attempts remain counted; this is a partial cohort, not the registered
six-session reference. One demonstrated all four hidden checks plus health and
settled normally. Four checks cover less than whole-phase acceptance.

Total execution308.664s and75 requests. The two complete output totals sum to
11119; the third and the cohort total remain unknown. All75 recorded payloads
sent `max_tokens:16384`, temperature1,top-p.95,top-k20. Elapsed excludes grading;
it is not billed GPU time, which also includes setup/qualification and idle time.
Each run's `accounting.json` preserves limits and transport boundaries without
putting raw prompts/traces in Git. Full/uncached context remains per-run in
`run.json`; complete context is unknown for the mixed-error third attempt.

The second attempt hit the180s open-call cutoff on a foreground server; its
hidden import failed because generated files did not supply the expected app
module. Health passed. The third added `uvicorn` to project dependencies without
updating the lock, causing offline checker provisioning to fail. Two recovered
502s correlate with host-relay upstream `ECONNRESET`; they are not assigned a
speculative server/SSH root cause. After substantive work, this mixed failure
was conservatively counted with absent grades and unknown usage, preserving
both model and infrastructure effects rather than selectively replacing it.

The [`machine` field](20261104T132947Z-easy-9c1f17/run.json) describes the Mac
harness host. Inference used the verified Pod GPU, not the Mac GPU. The
[backend freeze](../../docs/superpowers/research/2026-11-04-contained-retry-study/backend-config.json)
and corrected image40796579 were shared by these three attempts. No worker
extension or remedy was loaded. The old native/A40 records remain separate.

## Remedies: interaction only

The user's five unchanged units were checked together through actual contained
Pi with a local fake provider: `prompt/name-the-layout`, `prompt/python-developer`,
`prompt/verify-the-spec`, `guard/foreground-server`, `context/trim-tool-output`.
[Seven checks passed](../../docs/superpowers/research/2026-11-04-contained-retry-study/five-remedy-qualification.json):
all five loaded in order, three prompt fragments reached the provider, the
foreground Uvicorn call was blocked,12000 output characters were trimmed to8000
plus a retrieval note, and Pi settled. Initial wrong-port probe failure retained.
This proves hook behavior/loading; the counted n=1 coding screen did not start.
No preset/default is promoted and no individual remedy benefit is established.

## Infrastructure and shutdown

The first controller treated routine review as terminal, stopping the4500 and
losing its host GPU. Local orchestration now permits explicit classification
with a180s bound. A subsequent PRO6000 build log reached100% compilation before
a readiness failure. That check conflated a finished build with missing weight
readiness; [local regression proof](readiness-proof.json) shows old exit2 and
corrected exit0 for build-done/download-active, with six states passing. Exact
remote build/download termination details were not retrieved before shutdown;
no completed PRO6000 backend qualification is claimed. Corrected helper source
is archived but was not exercised on another GPU.

The PRO6000 could not restart. Fresh PRO6000/4500 placements failed; an H200
allocated but repeatedly failed container creation before SSH existed. Its
[Runpod system logs](h200-boot-logs.json) show Docker context deadline followed
by repeated exit1 before our model/application started. It was stopped. Two
fresh A100 placement attempts then failed capacity. Community catalog had no
suitable stock. No further Pod was created or left waiting for capacity.

[Final MCP readback](final-pods.json) verifies all five account Pods EXITED,
including the original and A40. No owned measurement containers/volumes or retry
watchers remain. Persistent `/workspace` disks total250GB and continue storage
billing. They were retained, not deleted. The six/six/one study is outstanding.

[Raw evidence](raw-evidence.json) includes the complete three-run batch,
backend qualification, failed/successful fake-provider probes, setup controllers
and logs, corrected readiness proof and final shutdown records. The unique
research asset was downloaded and SHA-256 verified; earlier assets are preserved.

## What would falsify this

Unsupported counters/identities, archive mismatch or unexpected loaded modules
invalidates the corresponding claim. No whole-phase or comparative claim exists.

## Risks

Only three Vanilla attempts, one with unavailable grading and usage. Offline
dependency caches constrain tool behavior. Higher GPU price did not overcome
host capacity/startup failures; stopping can lose the allocation immediately.
