---
phase: LC
feature_cycle: LC.36
lifecycle: active
---

# Runtime repair screen

The user authorized fixing failures and running again while away. LC.35 closed
with0/20 selective and10/20 gated usable results; no reliability improvement
was demonstrated. Its preserved traces establish three concrete problems:

- G12 stalled on a timeout-wrapped server, which bypassed the foreground guard.
- G2 mistook a guard refusal for application output; its message also incorrectly
  said a running server was unnecessary despite required launch verification.
- G1 expanded into later phases before settling; verify-the-spec asks for every
  requirement in the spec rather than the current requested task. G2/G3 also
  interpreted launch exit evidence as a requirement or dismissed it after tests.

## Bounded changes

Recognize GNU timeout/gtimeout wrappers around the same known server launches,
including duration/options and nested uv/env wrappers. A timeout prefix is not
proof of subprocess cleanup. Keep diagnostic/help queries, ordinary tests,
quoted launch descriptions and explicitly detached commands permitted. This
remains a hang-prevention heuristic, not a process-containment guarantee.

The guard refusal states that execution was blocked and its text is not output
from the application. In-process endpoint tests remain useful; they do not prove
required startup behavior. Explain that required launch checks need bounded
lifetime, captured logs/readiness and process cleanup, with no suite-specific
command or answer added to generic guidance.

Narrow the existing once-per-task verify instruction to the current requested
task; do not implement later tasks merely because their requirements are in the
same spec. Runtime checks cannot be replaced by static source inspection or
unrelated passing tests. Keep the existing injection lifecycle unchanged.

The external startup observation explicitly distinguishes required behavior
from observed failure: no readiness, and whether the child exited or remained
alive until the readiness bound. Preserve bounded sanitized untrusted diagnostics.
No changed assertion, oracle relaxation, hidden feedback, extra repair or tool.

## Measurement rig

Add explicit --prepare-screen/--run-screen modes to the existing guarded
collector for a fixed six fresh gated tasks. Default comparison stays exactly
S,G*20. Registration records screen/comparison kind and actual per-arm counts;
completion depends on the selected fixed order. The screen always has a
screen-only/no-promotion decision, even if all six pass. It freezes its dated
protocol, source/package/image/backend, retaining the existing8h guardian,
600s task,180s tool,30s checks and two repairs. No mid-cohort edits or retries.

## Qualification and interpretation

Classifier tests first reproduce timeout wrappers while preserving queries and
background cases. Checker tests exercise actual startup observations and retain
failure authority. Collector tests cover default40 versus screen6, registration,
terminal completion and no screen promotion; qualify the actual contained image,
warning transport, native repairs and compaction before model inference.

These are agent implementation choices under standing iteration authorization:
combine the small corrections, screen six rather than immediately spending
another forty, preserve the current hardware/sampling and use the existing
collector. Alternatives rejected: more repairs or weaker acceptance would change
what success means; a new managed-startup tool is deferred until the smaller
corrections are screened. Individual causal attribution is not available.

Record every outcome, semantic reservations, requests/turns/output/elapsed and
unknown totals. A clean six-task screen is only a lead for a new preregistered
comparison. Continued scope expansion, ignored runtime evidence or a valid build
rejected by the instrument falsifies the fixes. Stop inference and verify owned
resources independently after finish/failure. Raw uploads/public pushes stay held.
