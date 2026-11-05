# Protected acceptance: twenty tasks per arm

**What is measured:** forty fresh Easy Phase 1 tasks on one frozen local M5 Max
backend, alternating selective remedies (S) and S plus protected external
acceptance (G), twenty each. **What is conjecture:** broader task reliability,
future feedback improvements, and output-token efficiency of G.

The protected gate increased observed usable results from **1/20 to 11/20**.
It did **not** meet the registered **18/20** reliability threshold. The joint
registered decision is **no decision**, because one interrupted generation makes
G's total output unknown. No default or preset is promoted.
[Preregistration](preregistration.md), [every task](scorecard.md),
[analysis](analysis.json), [records](records.json), [decision](decision.json).

## Quality

| Registered component | Selective S | Gated G |
| --- | ---: | ---: |
| All hidden checks actually pass | 20/20 (80/80 checks) | 20/20 (80/80 checks) |
| Code health: Ruff and complexity | 19/20 | 19/20 |
| Normal settlement | 20/20 | 18/20 |
| Final changed paths within phase layout | 19/20 | 15/20 |
| Complete automated external acceptance | 1/20 | 12/20 |
| All registered usability conditions | **1/20** | **11/20** |
| Wilson 95% interval, usable proportion | 0.9–23.6% | 34.2–74.2% |

S failed title override in nineteen tasks; four also failed documented startup,
three failed nonempty project tests, and other misses included layout and
favicon. Eighteen S tasks passed hidden checks, health and settlement while
failing external acceptance. The four hidden checks do not exhaust the spec.

Every G task failed its first acceptance check, including title override in all
twenty. G used **29 repair continuations**: eleven tasks used one, nine used two.
Eleven usable results were rescues from an initial failure. Twelve tasks were
host-accepted after an independent final snapshot check; G1 failed health due
to an unused import, leaving eleven usable. Six exhausted repairs, G4 stalled
on an open tool and G12 reached the deadline. None of these failures is replaced.
Final checked failures included startup (five), phase layout (three), and changed
frozen base input (one); counts overlap and exclude G12's uncompleted final audit.
[Per-task checks and receipts](checks/).

Typing is separate from the registered health flag: Pyrefly passed 20/20 S and
18/20 G. G17 is formally usable but its test accesses `BaseRoute.path`, producing
a type-check error. Formal usability therefore does not mean every typing check
passed. G14's typing failure accompanies its rejected layout violation.

## Budget

All tasks, including failures and repairs, contribute to these request totals.
Output includes thinking; local output tokens are not a monetary price.

| Metric | S | G |
| --- | ---: | ---: |
| All inference requests | 484 | 841 |
| Median requests per task | 22.5 | 39.5 |
| Request range | 16–38 | 20–90 |
| Requests per usable task, failures included | 484 | 76.45 |
| Total generated output | 203,948 | **unknown** |
| Median output per task | 9,800 | **unknown** |
| Output per usable task | 203,948 | **unknown** |
| Recorded execution seconds, combined | 1,885.543 | 4,221.579 |
| Median recorded execution seconds | 91.021 | 197.362 |

G used about 74% more requests overall and about 84% fewer requests per usable
result in this cohort. That descriptive request improvement does not establish
the registered output-token criterion or a general reliability rate.

G12 made 90 requests, compacted once, began one repair and hit its 600-second
inference/check deadline (601.657 seconds recorded including overhead). The
backend has 89 completed generation timing records: the interrupted generation
has no final token timing. Its total remains unknown. **340,867 output tokens
cover the nineteen fully measured G tasks only**, not the whole arm. The
recorded compaction generated 3,442 summary tokens; it is retained separately
within G12's incomplete accounting, never dropped or treated as a full budget.

The 259 repair-period requests include the interrupted request; 258 have complete
mapped generation timings. Their 161,303 known output tokens are a partial
repair scope, not an exact repair total. Failed tasks consumed 460 S and 430 G
requests. S's nineteen failures used 193,742 output tokens. Eight fully measured
G failures used 159,586; the ninth is G12, so G's failed-task output is unknown.
Per-task distributions and all scope distinctions are in [analysis](analysis.json).

The once-per-task layout/verification injections remained exactly once in all
88 audited ordinary payloads around G12's compaction: 53 before, 35 after.
This verifies delivery continuity, not compliance. Native agent hooks omit two
of the 841 relay-counted requests; compaction and interrupted-request accounting
remain visible. [Continuity audit](prompt-continuity-audit.json).

## What the gate establishes, and what it does not

The host owns the package hashes, task identity, two-repair allowance, shared
600s deadline, at-most-30s checks and final receipt. Candidate execution runs in
separate temporary containers; assertions run in a host subprocess. Failed
hidden checks are never repair feedback. The worker extension and presets are
unchanged; both arms start from Vanilla Pi 1.4.0 plus recorder. The gate is an
explicit opt-in measurement remedy and requires its external controller.

Qualification covers eight valid title/hero variants, individual omissions,
hostile candidates, actual-Pi pass/repair/exhaust/tamper, compaction, controller
death and owned-resource recovery. A fresh review's seven Important findings
were fixed with regressions before collection. [Qualification](qualification/),
[execution notes](execution-notes.md), [verification](verification.json).
Finite behavioral observations cannot attest arbitrary malicious application
behavior, and containers do not prove protection against runtime exploits.

Hero and welcome meaning use declared structural proxies. Source/text inspection
of all forty home templates found generic or placeholder introductions, including
G6's neutral wording despite an automated pass. There was no browser visual
review. These reservations are retained without rewriting the registered score;
an automated pass is not semantic proof. [Manual audit](manual-audit.json).

G4 left `timeout 10 ... uvicorn ... --reload` open until the host's 180s tool
cutoff; a timeout wrapper did not make this command return. The foreground guard
is a heuristic, not process containment. S/G recorded 3/14 refusals; these are
observed interventions, not a prevented-hang rate.

## Qualification costs and provenance

Two earlier cohorts were stopped for checker false failures, never reused as
comparative evidence. The first retained two attempts/48 requests; v2 retained
fourteen/485 requests. Both totals have unknown output. Twelve fully measured v2
attempts account for 157,599 output tokens; one fully measured first-batch attempt
accounts for 7,291. These are separate partial setup scopes, not setup totals.
The correction removed invented CSS-name constraints and qualified lawful title
overrides. [Abort records](qualification-aborts.json). Fake-provider tests and
short live setup probes are also excluded from coding-task budgets.

Source `444ec7a`, image `sha256:189f508eb9c1ae00d520ef4d404f45a672cdafc1f5b48953ebd9e5abf9895876`.
Same controlled6 local configuration: llama.cpp build11669/620d2225c, pinned
Q4_K_M weights, all29 layers and KV on M5 Max Metal; requested context100000,
two effective50176 slots but one coding task at once. Sampling1/.95/20,
max output16384, thinking preserved. [Frozen registration](registration.json),
[backend](backend-config.json), [live read-back](backend-live.json).

Inference stopped at 06:08:48 UTC on Nov5. Independent verification found no
recorded server/controller process, no listener8002, no owned container or volume
across 237 ownership records, and no frozen-input drift. The guardian exited and
its owned server returned0. Unrelated Docker resources were left alone. No Runpod
GPU was started. [Shutdown verification](post-identity-verification.json).
Raw evidence is held locally; **no upload**. [Archive manifest](raw-evidence.json).

## Next leads, falsification and risks

The gate is useful for detecting incomplete work; two repairs are insufficient
for dependable completion here. Next, screen bounded actionable startup failure
observations and a repair that respects the phase boundary. A settle-only gate
also cannot redirect a long initial work loop. These are leads, not measured
improvements; do not stack more prose or increase n before testing the failure.

**What would falsify this interpretation:** an independently qualified follow-up
under fixed scoring showing that these failures persist despite the proposed
feedback, or a valid saved artifact rejected by the current checker.
**Risks:** one repeated task, one machine/model/backend, semantic proxies,
unknown interrupted output and qualification expense. The result does not cover
later phases, other tasks, hosted GPUs or parallel inference.
