# Foreground log-follow screen — six fresh gated tasks

LC.38 finished **4/6 formally usable**, with two retained repair-exhausted
failures. Inference is stopped; an independent 88-resource ownership audit found
no remaining owned process, container, volume or listener, and no frozen drift.
This is **screen_only**: no default promotion or reliability claim.

[Every task](scorecard.md) · [Protocol](preregistration.md) ·
[Accounting](analysis.json) · [Semantic audit](manual-audit.json) ·
[Guard events](guard-event-audit.json) · [Independent shutdown](post-identity-verification.json)

| Quality | Result |
| --- | --- |
| Formal usable / host accepted / final external pass | 4/6 each |
| Hidden checks | 20 passed; four not run in G1 (recorded 20/24) |
| Ruff, complexity and typing | Five pass; G1 not checked |
| Settlement / open-tool stalls | 6/6 / 0 |
| Initial external pass | 0/6 |
| Protected input/layout violations | G1 edited pyproject.toml |

G1 spent 600.669 seconds, exhausted both repairs, and retained an unauthorized
dependency edit. The live gate caught that edit. Final external checking timed
out; hidden grading and health checks could not start because the candidate's
changed dependencies could not resolve. This is a retained candidate failure,
not four observed hidden assertion failures or a passing final artifact. Its
execution classification remains `settled`, not a tool stall or runner deadline.

G6 exhausted both repairs while retaining `uvicorn.run(app, reload=True)`.
The host transported the actual import-string warning, but the model reasoned
that this code should work and continued trying launch commands. Hidden checks
and health passed while required real startup failed; the gate correctly refused
acceptance. All six initially failed title overriding; three initially failed
startup, and one initially lacked project tests. Four became usable after one
repair each. Neither failed task was replaced.

| Budget, all six including failures | Result |
| --- | ---: |
| Provider requests / ordinary model turns | 373 / 369 |
| Output tokens, including thinking and compaction | 183,186; fully reconciled |
| Requests / output per usable result | 93.25 / 45,796.5 |
| Median requests / output per task | 56 / 23,217 |
| Recorded task seconds, combined / median | 1,831.221 / 234.037 |
| Repair continuations / repair requests / repair output | 8 / 158 / 96,118 |
| Failed-task requests / output | 185 / 102,842 |

Two compactions completed, one each in G1/G6. Four requests occurred outside the
ordinary agent hook; relay reconciliation includes all their output, rather
than treating ordinary trace tokens as the total. All 369 ordinary payloads
carried each dedicated layout/verification injection exactly once, including
after compaction. No output totals are unknown.

The actual cohort had ten intercepted server starts and **zero log-follow
attempts/refusals**. Thus no follower stall was observed, but this cohort does not
measure the new guard preventing a model-generated follower. The separately
frozen, uncounted [native fake-provider qualification](native-follow-qualification.json)
does exercise that boundary: the control created its log and stalled at the
five-second cutoff; the guarded call was refused before file creation and
settled in 1.012 seconds with one refusal and two requests. Both cleaned up.
Request 2's matching refusal result was manually inspected; the helper does not
automatically assert its exact content. Source, hash and payloads are retained.

| Uncontrolled screen | Usable | Requests / usable | Output / usable |
| --- | ---: | ---: | ---: |
| [Runtime repair, LC.36](../2026-11-05-runtime-repair-screen/README.md) | 4/6 | 60 | 25,199.5 |
| [Repair authority, LC.37](../2026-11-05-repair-authority-screen/README.md) | 5/6 | 60 | 24,157.2 |
| Log-follow guard, LC.38 | 4/6 | 93.25 | 45,796.5 |

These are descriptive small-cohort results, not causal comparisons. The latest
screen is more expensive per usable result and did not produce a clean cohort.
The gate is useful for refusing incomplete work, but does not yet make this a
trusted autonomous worker. Another unchanged run would not repair the observed
model failures; no favorable retry is justified by them.

Formal usability also overstates semantic quality: G4 literally contains
“A short welcoming paragraph.” G2/G3 use neutral explanatory introductions.
Registered scores remain unchanged and these reservations stay visible. No
browser visual or interaction review was performed. Semantic completeness and
protected-input enforcement are possible future hypotheses, not fixes measured
by this screen.

Source `81f659c`; image
`sha256:300790eca2e16970004b6f2523681ca2bba2f6d81bb5b5b3026d1c2d133381ee`.
Same M5 Max, frozen Q4_K_M model/sampling/context, Pi1.4.0, one task at once,
two repairs,600s task,180s tool,30s checks and independent8h guardian. All125
frozen inputs and qualification groups were checked before counting. Worker,
presets, protected assertions and default comparison recipe remain unchanged.
Raw evidence is archived locally, scanned for known credential formats, and
unpublished. No Runpod GPU was started. Local commits only; publication remains
held following the earlier automatic approval review rejection.
