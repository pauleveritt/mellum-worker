# Runtime repair screen — six fresh gated tasks

LC.36 finished **4/6 formally usable**, with two repair-exhausted model failures.
This uncontrolled screen is **screen_only**, not a reliability or improvement
claim. It does not replace the earlier selective/gated comparison. Inference is
stopped; independent verification found no owned resources or frozen drift.

[Every task](scorecard.md) · [Registered protocol](preregistration.md) ·
[Accounting](analysis.json) · [Semantic audit](manual-audit.json) ·
[Independent shutdown](post-identity-verification.json)

| Quality | Result |
| --- | ---: |
| Hidden checks | 23/24; five tasks passed all four |
| Ruff and complexity | 6/6 |
| Typing | 6/6 |
| Settlement | 6/6 |
| Final external acceptance / host accepted / usable | 4/6 each |
| Initial external acceptance | 0/6 |
| Deadline / stall failures | 0 / 0 |

| Budget, six tasks including failures | Result |
| --- | ---: |
| Provider requests / ordinary turns | 240 / 240 |
| Output tokens, including thinking | 100,798; fully reconciled |
| Requests / output per usable result | 60 / 25,199.5 |
| Median requests / output per task | 38.5 / 16,128.5 |
| Recorded task time, sum / median | 983.841 s / 145.596 s |
| Repair continuations / repair requests | 8 / 67 |
| Repair output | 37,055 |
| Failed-task requests / output | 102 / 42,759 |

All six needed title-block repair; four became usable after one repair. G4 never
created project tests despite repeated nonempty-test failures, then regressed the
required tagline from “your human” to “our human.” G6 created tests and fixed its
title but retained `uvicorn.run(app, reload=True)`. Its final message explicitly
dismissed the observed launch warning because TestClient and its own tests passed.
The protected gate correctly refused both tasks; self-reported completion was false.

The runtime/scope changes did not produce a clean screen. No timeout-wrapped stall,
guard refusal, scope expansion or compaction occurred here, so the screen cannot
establish those fixes' efficacy. All 240 ordinary payloads carried each dedicated
layout/verification injection exactly once. No outside-hook requests or unknown
output totals occurred.

Formal usability still has semantic limits: G1 contains the literal placeholder
“A short welcoming paragraph.” G2 has a neutral explanatory introduction rather
than an explicitly welcoming one. These reservations do not rewrite registered
scores. No browser visual assessment was performed.

Source `fcdc8a1`; image
`sha256:22138599c87530272fd1f762a9f43830a23d4a04babb07fad7552027f1e03cc1`.
Same M5 Max, frozen model/sampling, one task at once, two repairs, 600s task,
180s tool cutoff and independent 8h guardian. All four qualification groups and
live native inference passed before counting. Batch-v1 stopped before inference
because reviewed fixes invalidated image source hashes; retained as superseded
qualification evidence. No counted replacement or favorable retry occurred.

The next small hypothesis is clearer repair authority: external failures cannot
be waived by self-authored tests, missing required tests need creating, and passing
behavior should be preserved. That is an unmeasured wording hypothesis, not a
reason to weaken assertions, add repairs, or claim a trusted worker.

Raw evidence remains local and unpublished. Local commits only; public push was
previously blocked by automatic approval review pending publication authorization.
