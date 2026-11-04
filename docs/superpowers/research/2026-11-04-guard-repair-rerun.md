# Foreground guard repair and remedied rerun

**Measured before inference:** help-query and native refusal-count regressions
failed, then passed after independent fixes. Repository tests641/641 passed.
Updated contained image `ce76e13a` passed27 boundary checks and10 actual-Pi
fake-provider interaction checks. **Conjecture:** the rerun's coding outcome.

## Repair and evidence

`cd106b0` allows simple known server CLI help/version queries, preserving blocks
on arbitrary scripts, substitutions and compound foreground starts. `58036f2`
counts Pi's native blocked `tool_execution_end`, retaining legacy results and
deduplicating by instance/tool-call ID. The retained original trace contains
the native refusal; no provider-history inference is needed. Old records remain
unchanged. [Spec](../specs/2026-11-04-foreground-guard-repair-design.md).

Actual Pi permits help/version, refuses a genuine foreground server, reports
exactly one refusal, loads all five units, sends all three prompt fragments,
trims12000 characters to8000 plus note, and settles. This qualifies interaction,
not coding quality. An initial proof-export helper expected run.json from the
lower-level runner; it was corrected to call report on the retained native trace.
No inference or measured source changed during that correction.

## Same screen, distinct new host

Paul requested repair then rerunning the remedied arm. Keep the same n=1 cold
Vanilla Easy Phase1 screen and ordered units: `prompt/name-the-layout`,
`prompt/python-developer`, `prompt/verify-the-spec`, `guard/foreground-server`,
`context/trim-tool-output`. This is a repeat presence screen, not a rate or a
default-selection experiment. Keep Pi1.4.0, model/weights, sampling1/.95/20,
16384 output ceiling, two50k slots, collection concurrency1, deadline600s,
open-call cutoff180s, original four-check oracle and containment policy.

Original H100 `kmz813v3rm3f88` could not restart: host GPUs occupied, read back
EXITED. The live Secure catalog lists H100 in EU-FR-1/AP-IN-1 at$3.99/hour;
Pod `dnjioygj7izxh0` was created in EU-FR-1 with the account-read CUDA12.8 image,
20GB container/50GB persistent disk, SSH only. Runpod allocates32vCPUs/188GB RAM.
Verify actual hardware, rebuild the pinned90a backend, qualify and freeze before
the screen. Do not mix this host with the earlier6+6+1 cohort or infer causal
timing improvements. Inference uses only the Pod GPU; Mac runs Pi/tools.

Report hidden checks, health, completion, requests/output/context/time, actual
query/refusal behavior and cleanup. Retain model failures and mixed transport
errors; missing usage stays unknown. No favorable replacements. Four hidden
checks do not establish whole-phase acceptance. Compare source/image changes
explicitly and preserve previous records.

## Shutdown

Guardian stops on completion, unresolved blocker180s or15:45:27UTC November4
(30 minutes including setup). Verify EXITED before reporting/publishing. Keep
persistent files; storage billing continues. All earlier Pods stay stopped.

## What would falsify this

Real starts gaining a help exemption, duplicate/missed native refusals, material
drift, unexpected modules, changed scoring or unverified cleanup invalidates claims.

## Risks

Capacity/startup may fail; setup consumes the time bound. One five-unit session
cannot attribute an effect, establish repeatability or establish comparative rates.

## Outcome

[Retained repeat](../../../evals/2026-11-04-guard-repair/README.md): hidden4/4,
healthpass, settled39.932s,19requests,9078output, peak full prompt13558.
All19requests sent16384; no provider error or unknown usage. No server/help
command attempted, no refusal, no trim note. These behaviors were exercised
only in the separate actual-Pi interaction qualification. Model wrote one test
and passed it after an initial absent-tests error. All failures remain retained.

Actual hardware: H10081559MiB, driver595.91.07, CUDA12.8.93, AMD EPYC9554;
new host qualified/frozen at15:21:41UTC. Source/image identity reverified before
and after collection. Pod stopped automatically on completion; independent MCP
readback EXITED. No owned Docker containers/volumes or tunnel remain. Earlier
records unchanged; no rate, causal timing or default-promotion claim.
