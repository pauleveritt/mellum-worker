# Contained H100 Phase 1 comparison and five-remedy screen

**Measured:** six Vanilla and six thin Worker Easy Phase1 attempts, then one
Vanilla five-remedy screen, on one qualified frozen H100 inference backend.
All thirteen attempts are retained. **Unestablished:** a causal Worker benefit,
a remedy success rate, individual remedy effects, or whole-phase acceptance.

## Quality and completion

| Arm | n | All four hidden checks pass | Health pass | Settled | Hidden + health + settled | Stalled |
| --- | --- | --- | --- | --- | --- | --- |
| Vanilla + recorder | 6 | 2 | 5 | 1 | 0 | 5 |
| Thin Worker + recorder | 6 | 4 | 5 | 1 | 1 | 5 |
| Vanilla + five remedies (screen) | 1 | 1 | 1 | 1 | 1 | 0 |

The Worker cohort includes one unavailable hidden grade: generated code imported
nonexistent `fastapi.templates`, so the launched grader could not collect tests.
It remains a counted failure; unavailable does not mean four checks executed and
failed. The other five Worker attempts and all Vanilla attempts ran the checks.
The oracle covers four requirements, less than complete Phase1 acceptance.

Every baseline stall ended on a foreground server command at the180s open-call
cutoff. Vanilla's sole settled run passed2/4, missing tagline/navigation; Worker's
sole settled run passed4/4 plus health. These are separate quality/completion
observations, not evidence that the thin wrapper improves generation. All twelve
initial provider payloads were identical after replacing run-specific workspace
IDs ([audit](final-verification.json)). Later sampled trajectories differ.

## Budget

| Arm | Provider requests total (median/run) | Output tokens total | Execution seconds total (median/run) |
| --- | --- | --- | --- |
| Vanilla, n=6 | 128 (17.5) | 34,889 | 1,097.240 (213.771) |
| Worker, n=6 | 124 (18) | unknown | 1,070.735 (202.003) |
| Five remedies, n=1 screen | 18 (18) | 5,823 | 28.504 (28.504) |

Worker has four complete output totals summing24,146; two remain unknown after
recovered502s. Neither missing total is treated as zero. Requests equal the
recorder's model-turn measure. All270 actual provider payloads sent
`max_tokens:16384`, temperature1,top-p.95,top-k20. Elapsed is actual execution,
excluding grading; billed Pod time also includes setup, qualification and waits.

Peak full prompt context: Vanilla16,997 (all six maxima known); Worker13,627
among four known maxima, with two unavailable; remedy10,949. Peak uncached input
is retained separately:2,691/1,628/1,642 respectively. These are prompt maxima,
not output allowances or cohort token totals. Per-attempt records and accounting:
[Vanilla scorecard](vanilla/scorecard.md), [Worker scorecard](worker/scorecard.md),
[machine-readable comparison](comparison.json), [all run records](records.json).

## What the remedy screen actually showed

The ordered units were `prompt/name-the-layout`, `prompt/python-developer`,
`prompt/verify-the-spec`, `guard/foreground-server`, `context/trim-tool-output`.
All five loaded; all three prompt fragments reached the actual provider payload.
The run created and executed its own test with
`uv run --frozen python -m pytest tests`:1 passed. Hidden4/4 and health also pass;
it settled normally in28.504s, without a stall or leaked process.

The [payload audit](remedy-observations.json) found one guard refusal, for
`uv run --frozen uvicorn --help`. That command is a harmless help query:
this is an observed guard false positive, not proof it prevented a real server
hang here. The raw `guard_blocks` counter says0 despite the provider-visible
refusal; raw evidence stays unchanged, with the separate audit recording1.
No trim note appeared in this single screen; loading alone establishes no coding
benefit for trimming. The separate [fake-provider interaction proof](../../docs/superpowers/research/2026-11-04-contained-retry-study/five-remedy-qualification.json)
exercised trimming and guard refusal, but is not coding evidence.

This bundled n=1 screen is a lead. It establishes this observed successful run,
not an improvement rate or attribution to one of five units. No preset or
shipped default changes. Recommended next measurement: a registered repeated
remedy contrast, isolating the guard and prompt fragments; first address the
help-command false positive and refusal-counter omission as distinct fixes.

## Provenance and retained failures

The [H100 continuation](../../docs/superpowers/research/2026-11-04-contained-h100-study.md)
registered the same6+6+1 protocol before collection. Its [freeze](../../docs/superpowers/research/2026-11-04-contained-h100-study/backend-config.json)
records actual GPU/binary/library/weight hashes and argv: llama.cpp11669/620d2225c,
CUDA12.8, Q4_K_M pinned revision, two50k slots, collection concurrency1, Pi1.4.0,
deadline600s/open-call180s. All arms used corrected contained image40796579 and
the matching27-check proof. Inference used the Pod H100; the Mac ran Pi/tools
inside temporary Docker. The `machine` field names the Mac harness host.
The freeze's `not_started` collection field is its precollection snapshot;
[terminal status](../../docs/superpowers/research/2026-11-04-contained-h100-study/status.json)
and the two complete batch manifests record subsequent completion.

Worker attempts3 and5 recovered502s after work, continued unchanged and stalled.
The relay reports `request_error/ECONNRESET` on requests10 and14 respectively;
precise server/SSH root cause is unproven. Both were explicitly counted with
unknown full usage, not replaced. Attempt3 also has the invalid generated import
and failed health. Zero attempts were excluded. Earlier native, A40 and partial
4500 cohorts stay separate. No measured runner or remedy source changed here.

The [final audit](final-verification.json) reverified both baseline launch
identities, worker activation, shared source/runtime inputs, qualified image,
and cleanup. [Raw evidence](raw-evidence.json) retains traces, sessions, workspaces,
full checker output, relay boundaries, setup/qualification and audit tools in a
unique research-release asset, downloaded and SHA-256 verified.

## Shutdown

The guardian stopped H100 Pod `kmz813v3rm3f88` immediately on completion and read
back EXITED. The [fresh account read](final-pods.json),14:59:23UTC November4,
confirms all six Pods EXITED. No owned measurement containers or scratch volumes
remain; the study controller and SSH tunnel exited. Persistent disks total300GB
and continue storage billing; they were retained, not deleted.

## What would falsify this

Changed shared inputs, unexpected modules, unsupported metrics, selective
exclusion, missing cleanup or an archive mismatch invalidates affected claims.

## Risks

Small baseline cohorts, two mixed transport failures, narrow hidden coverage,
stochastic trajectories, and a five-unit single screen limit generalization.
The help false positive and guard-counter omission remain open findings.
