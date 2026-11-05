# Repair authority screen — six fresh gated tasks

LC.37 finished **5/6 formally usable**. One model tool stalled; all six passed
hidden checks and code health. Inference is stopped; independent ownership and
freeze verification is clean. This is **screen_only**, not a reliability claim.

[Every task](scorecard.md) · [Protocol](preregistration.md) ·
[Accounting](analysis.json) · [Semantic audit](manual-audit.json) ·
[Independent shutdown](post-identity-verification.json)

| Quality | Result |
| --- | ---: |
| Hidden checks | 24/24;6/6 tasks |
| Ruff and complexity / typing | 6/6 /6/6 |
| Settlement / stall | 5 /1 |
| Final external acceptance / host accepted / usable | 5/6 each |
| Initial external acceptance | 0/6 |
| Deadline / checker / integrity failures | 0 /0 /0 |

| Budget, including the failed task | Result |
| --- | ---: |
| Requests / ordinary turns | 300 /300 |
| Output, including thinking | 120,786; all reconciled |
| Requests / output per usable | 60 /24,157.2 |
| Median requests / output per task | 52 /20,146 |
| Recorded task seconds, combined / median | 1,342.766 /197.582 |
| Repair continuations / repair requests / repair output | 7 /116 /52,854 |
| Failed-task requests / output | 59 /20,074 |

All six initially failed title override. Four initially failed startup; three
were repaired to usable, while G4 still failed startup and stalled. Both tasks
with initially missing tests added tests. G5 needed two repairs; other tasks used
one before pass or stall. All300 ordinary payloads carried each dedicated layout/
verification instruction once. No compaction, outside-hook requests or unknown
token totals occurred. **Dated correction,2026-11-05:** the original counter
missed the new refusal wording. [Trace audit](guard-count-correction.json) finds
19 intercepted server starts, including a timeout-wrapped launch, not zero.
Original records/analysis are retained; usability/budgets are unchanged. Repeated
refusals also cost model requests and do not prove every hang was prevented.

G4 started a server in the background, then ran foreground `tail -f` in the same
bash call. The follower kept the call open until the180s tool cutoff. The final
artifact still used `uvicorn.run(app, reload=True)` and failed real launch; the
host gate correctly refused it. Process containment recovered owned resources.
This exposes a concrete foreground-log-follow gap, distinct from server launch
classification. A separate explicit guard is the next small testable correction.

Compared descriptively with [LC.36](../2026-11-05-runtime-repair-screen/README.md),
formal usable count was5/6 versus4/6, requests per usable remained60, and output
per usable was24,157 versus25,200. Median per-attempt requests/output/time rose.
These are small, uncontrolled cohorts: no causal effect or reliability conclusion,
no preset/default promotion, no favorable replacement. The authority text is a
lead, not a demonstrated remedy for every ignored warning.

Manual source reservations remain separate from registered scores: G2/G5 use
neutral explanatory introductions. G3's extra button has an href attribute rather
than an anchor/navigation handler, a source-level concern despite its required
navbar links. No browser visual or interaction review was performed.

Source `e89486c`; image
`sha256:c27c74328d5825106578b22e8392d9280464a3776f72625503326406cd7cf38a`.
Same M5 Max, frozen model/sampling/context, one task at once,two repairs,600s task,
180s tool,30s checks,8h independent guardian. All qualification groups and live
native probe passed. Independent85-resource audit found no owned container,
volume, server, controller, guardian, port8002 listener or frozen-input drift.
Raw/local commits held; no public upload or Runpod GPU started.
