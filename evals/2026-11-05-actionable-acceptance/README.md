# Actionable acceptance feedback: twenty tasks per arm

Forty fresh Easy Phase 1 tasks ran on the frozen local M5 Max backend,
alternating selective remedies (S) and S plus protected external acceptance (G).
G received bounded startup diagnostics and explicit current-task repair scope.
The worker, presets, acceptance criteria, two-repair limit and deadlines stayed
unchanged. [Preregistration](preregistration.md), [every task](scorecard.md),
[analysis](analysis.json), [records](records.json).

**Measured:** S produced **0/20 usable results**, G **10/20**. G missed the
registered **18/20** threshold. The joint rule returns **no decision**, with
unknown G output and no S usable-result denominator. No default is promoted.
The preceding cohort produced 1/20 and 11/20: this follow-up does not demonstrate
an overall reliability improvement. Individual feedback effects are not separated.
Broader task reliability and proposed next remedies remain conjecture.

## Quality

| Registered component | Selective S | Gated G |
| --- | ---: | ---: |
| All hidden checks pass | 20/20 (80/80 checks) | 19/20 (77/80 checks) |
| Code health: Ruff and complexity | 19/20 | 19/20 |
| Normal settlement | 20/20 | 16/20 |
| Changed paths within phase layout | 17/20 | 18/20 |
| Final saved artifact passes external check | 0/20 | 11/20 |
| Host-accepted completed task | n/a | 10/20 |
| All registered usability conditions | **0/20** | **10/20** |
| Wilson 95% usable interval | 0–16.1% | 29.9–70.1% |

S missed title override eighteen times, startup nine, nonempty passing project
tests four, phase layout three and guarded reload once; counts overlap.
Nineteen S tasks passed hidden checks, health and settlement while failing the
more complete external contract. Hidden checks do not exhaust the public spec.

Eighteen G tasks entered repair, using **29 continuations**: seven used one,
eleven used two. G7 passed initially; nine usable tasks were rescues.
Six tasks exhausted repairs; G1, G6 and G17 hit the deadline; G12 stalled.
Ten completed tasks were host-accepted and usable. G12's saved artifact passes
external acceptance, but `timeout 5 uv run --frozen python app.py` remained open
until the 180s cutoff. An acceptable artifact alone is not normal completion.
Final checked failures included startup five times, with other misses in titles,
layout and rendered HTML. Three deadline tasks have timeout results, not a
completed final external audit; missing observations are not passes.

G3's source template contains the expected markup, but its route returns a plain
string that FastAPI serializes as JSON. Reading the source and rerunning its own
passing test did not verify the actual response. G2 repeatedly saw the real
import-string startup warning but treated its project-test pass as sufficient.
G1 expanded into later phases before ever settling, so repair feedback could not
act. These traces support the next investigation, not a claim that more prose
will solve it. [Per-task receipts](checks/).

Typing is separate from registered health: Pyrefly passed 18/20 S and 20/20 G.
Source/text inspection covered every saved home artifact, including S14's inline
content. G5's bare home-page description and G14's neutral introduction expose
the declared welcome-proxy limitation. There was no browser visual assessment;
formal usability does not establish semantic completeness.
[Manual audit and reservations](manual-audit.json).

## Budget

All tasks, failures, repairs and relay-counted inference requests are included.
Output includes thinking; local tokens are not a monetary price.

| Metric | S | G |
| --- | ---: | ---: |
| All inference requests | 591 | 975 |
| Ordinary recorded model turns | 589 | 964 |
| Median requests per task | 27.5 | 38 |
| Request range | 18–102 | 17–119 |
| Requests per usable task, failures included | undefined (zero usable) | 97.5 |
| Whole-arm output | 225,947 | **unknown** |
| Median output per task | 10,338.5 | **unknown** |
| Output per usable task | undefined | **unknown** |
| Combined recorded seconds | 2,083.843 | 5,135.117 |
| Median recorded seconds | 93.2155 | 182.322 |

G used about 65% more requests than S in this cohort. Compared descriptively
with the preceding G cohort, requests rose from 841 to 975 and usable results
fell from eleven to ten. This is not a controlled estimate of individual
feedback effects or a known output-efficiency improvement.

G's **308,948 output tokens cover seventeen fully measured tasks only**.
G1/G6/G17 have cancelled generations without final backend token timings;
whole-arm and failed-task output remain unknown. The 279 repair-period requests
have 277 complete mapped generations, accounting for **189,547 known partial
repair output tokens**, not an exact repair total. Failed tasks consumed all
591 S requests and 654 G requests; seven fully measured G failures used 159,223
output tokens, with three other failed-task totals unknown.

S completed one compaction, G four, with all associated inference retained in
relay accounting. Ordinary agent hooks omit two S and eleven G requests; these
are included in the totals above. All **1,553 ordinary provider payloads** have
exactly one dedicated layout injection and one verification injection. G1 later
quoted marker text in its own reasoning; those quotations are distinguished
from additional injected messages. [Continuity audit](prompt-continuity-audit.json).

## Qualification, provenance and shutdown

Valid variants, omissions, hostile observations, native-Pi pass/repair/exhaustion,
tampering and compaction qualified before collection. The omitted-startup build
remained rejected and delivered the actual import-string warning. A fresh review
found first-URL readiness regression; a process-backed test failed first, then
passed for later URLs, split ports and a launch line without a newline.
[Qualification](qualification/), [execution notes](execution-notes.md).

Source `6283298`; image
`sha256:caefef6da36f64f1e5f79adfc38f7d2d9413e241a1521c1ad92540a25288a552`.
Same llama.cpp11669/620d2225c and pinned Q4_K_M weights, all29 layers/KV on
M5 Max Metal; requested context100000, two effective50176 slots, one task at a
time. Sampling1/.95/20, output16384, thinking preserved. Two repairs,600s shared
task deadline,180s open-tool cutoff,30s checks and independent8h watchdog.
[Registration](registration.json), [backend](backend-config.json).

Preflight batch-v1 used the pre-review image and fake-provider qualification;
it was never used for Mellum task collection. Both preparation directories and
the short native live setup probe are retained separately from counted budgets.
No earlier outcome was reused. No Runpod GPU was started.

Inference stopped at **08:41:54 UTC, November5**. Independent checks of217
ownership records found no owned container/volume, server/controller/guardian,
listener8002 or frozen-input drift. The watchdog's server exited0.
[Shutdown audit](post-identity-verification.json), [verification](verification.json).
Raw evidence is held locally, with no upload. [Archive manifest](raw-evidence.json).

## Next leads and falsification

The next small screen should test the observed timeout-wrapper guard gap,
truthful blocked-call guidance, task-scoped verification instructions and explicit
observed-failure wording. Keep the same acceptance requirements and limits;
freeze separately and do not add favorable retries to this cohort.

A lawful saved artifact rejected by the checker, repeated scope expansion or
continued dismissal of observed startup failures would falsify the proposed
fixes. This one repeated task, stochastic model, semantic proxies and incomplete
output accounting limit generalization. The result establishes neither
multi-phase trust nor hosted or parallel-inference performance.
