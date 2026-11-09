# Evidence ledger for the phase-worker review

## For Andre

**Date/accessed:** 2026-11-09. **What is measured:** committed run records,
read-only code inspection and retained-build replay; no new model inference.
**What is conjecture:** causal attribution across different rigs and savings
from an unrun change. The [decision note](../2026-11-09-phase-worker-review.md)
owns recommendations; this ledger preserves their evidence and qualifications.

### Sources and provenance

- **S1, Paul / counted Easy result:** [note](../2026-11-09-easy-count-result.md),
  [rule](../2026-11-08-easy-count-rule.md), [records](../../../../evals/2026-11-08-easy-final-count/table.md).
- **S2, Paul / mechanism screens:** [R.1](../2026-11-07-r1-easy-remedies.md),
  [F.6](../2026-11-08-f6-held-pod.md), [fixed and Medium screens](../2026-11-09-settle-fixes-screen.md).
- **S3, Fable / adversarial review:** Paul's supplied review, captured unchanged
  as [source text](sources/fable-remedies-review.txt); analysis and bootstrap
  intervals are secondary findings checked against S1/S2, not a new experiment.
- **S4, Andre van Zuydam / letter to Paul:** [supplied PDF](sources/andre-summary-for-paul.pdf); recommendations are inputs.
- **S5, Andre / upstream records:** inspected `origin/main` at `67f0138fa42386cf057ba34c5117349817b40258`:
  [Easy ladder](https://github.com/andrevanzuydam/mellum-worker/blob/67f0138f/docs/superpowers/research/2026-11-02-easy-ladder.md),
  [one-pass screens/results](https://github.com/andrevanzuydam/mellum-worker/blob/67f0138f/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md),
  [corrected preregistration](https://github.com/andrevanzuydam/mellum-worker/blob/67f0138f/docs/superpowers/research/2026-11-09-one-pass-verdict-prereg.md),
  [thinking/cap screen](https://github.com/andrevanzuydam/mellum-worker/blob/67f0138f/docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md).
- [Manifest](sources/manifest.json): original locations, source digests and review revisions.

### Counts and economics (S1/S2; recomputed over every attempt)

| Easy count | Vanilla | Base |
| --- | ---: | ---: |
| Attempts / strict / hidden-full / at least 12 checks | 32 / 2 / 2 / 20 | 32 / 25 / 30 / 31 |
| Mean checks / title misses among graded | 9.90625 / 28 of 31 | 12.875 / 1 of 32 |
| Stalls / budget endings | 7 / 0 | 0 / 10 |
| Total charged output / reported trace output | 302,732 / 291,135 | 1,098,978 / 846,444 |
| Total proxy requests / Pi seconds | 785 / 3,854.308 | 2,070 / 13,375.905 |
| Charged output / strict pass | 151,366 | 43,959.12 |
| Proxy requests / strict pass | 392.5 | 82.8 |
| Pi seconds / strict pass | 1,927.154 | 535.0362 |
| Charged output / at least 12 checks | 15,136.6 | 35,450.9 |

The [calculation snapshot](calculations.json) sums every attempt's `budget.spent.output_tokens`, divided by `passed`
count; requests use `budget.spent.requests`. Pi lifetime excludes setup, grading,
test authoring, human work and billed idle. Ratios describe this cohort, not a
measured retry policy. Expected retry cost additionally assumes stable attempts.
Base's extra 796,246 tokens bought 23 more strict passes: 34,619.4 per additional
pass, retrospectively. Keep all costs but deny leaked r27 credit: 1,098,978 / 24
= 45,790.75. Never treat that sensitivity as an uncontaminated new count.

S3 bootstrap: median token ratio 2.55–5.77x; Base tokens/strict roughly
31,700–62,300. Vanilla has zero successes in about 12% of bootstrap samples;
do not discard those samples. These intervals describe session variation on
one task, not transfer across projects. Tail: 14/32 Base attempts exceed
5 x Vanilla's 7,598.5 median; 6/10 budget-ended Base attempts pass strictly.

R.1's earlier mediated+bounded 18 full includes one path-heuristic contamination flag (r10); report 17 unflagged plus one flagged, not proof it read the grader.
Small Easy screens: unfixed 110,452 tokens / 5 strict; fixed 105,975 / 5;
fixed/max2 85,727 / 4. Thus approximately 22,090 / 21,195 / 21,432 tokens per
strict pass. Lower max2 median is not a demonstrated economic improvement.
Medium: zero strict per arm at n=3; 407,635 Vanilla and 772,184 Base charged
tokens. The 8.33 versus 13.67 checks means neither has delivered a strict pass.

### Medium diagnosis: two real causes behind four recurring hidden failures

The [label predicate](../../../../learn/code/suites/medium/grader/test_phase4_resolve_reopen.py#L106)
requires an element's entire text to equal `Open`/`Resolved`. Its shared
`_board_order()` call precedes the route POST at line 116. The written
[roadmap](../../../../learn/code/suites/medium/base/specs/roadmap.md#L78) permits
`Status: Open`. Review replay of all three route/order functions on retained
Base r02 and r03 failed at that label; allowing the prefix in memory made all
six executions pass, including redirect, target status and ordering assertions.
Neither app nor grader files changed. F.7 must preserve this as a regression fixture.

Retained workspaces: `~/mellum-runs/f6/medium-final-screen/base-r02/20261109T061809Z-medium-6a4bed/workspace`
and `base-r03/20261109T073743Z-medium-6de994/workspace` under the same batch.
Both still fail the genuine `route_id > second_id` assertion: r02 renumbers
stored IDs on append (`models.py:19`); r03 overwrites the constructor's ID
with `max(stored)+1` (`app.py:21`). The [mediated test](../../../../learn/code/suites/medium/mediated/test_04_resolve_reopen.py#L95)
checks direct and route allocation separately. S5's gate also lacks that
cross-path sequence. Author new checks from the invariant, not grader answers.

S3 attributes about 25% of Medium trace output to send-backs on requirements
without hidden counterparts. Brand and template inheritance are nevertheless
explicit in roadmap line 32 and tech-stack lines 20/25. This spending is not
proven waste; eliminate accidental restrictions, not legitimate acceptance.

### Code and trace findings

- [Caught gate errors](../../../../remedies/mediated-test.ts#L80) allow settle,
  as do green and exhausted caps. Final grading does not automatically pass.
  [runTest](../../../../extensions/mellum-verify.ts#L78) already returns red for
  ordinary nonzero pytest and bounded timeouts; launch/tooling errors can throw.
- All five full/nonstrict Base attempts (r01/15/16/17/32) changed the supplied
  test. Four ran project pytest successfully; r32 also added an unavailable
  `requests` import. [r15](../../../../evals/2026-11-08-easy-final-count/base-r15/run.json)
  records `integrity_ok: false`, `required_passed: true`, pytest exit 0.
- [Configured command defaults](../../../../remedies/tool/bounded-commands.ts#L25)
  bypass the 120s clamp: `MELLUM_BOUND_SECONDS=300` installs timeout 300.
- Review of 32 Base traces: 103 bash timeouts, 44 red messages; first red median
  request 23. r01 timed out 18 times and relaunched killed processes; r31 made
  85 requests and 30 supplied-test edit attempts with **zero** external send-backs.
- The [feedback tail](../../../../remedies/mediated-test.ts#L55) can replace
  assertions with server logs (r12). Return structured failure details instead.
- [Handover](../../../../learn/code/harness.py#L412) leaves readable copies;
  line 1035 exports exact paths to inherited shell environment. Removing the
  temporary execution copy closes the observed leak, not every route.
- Frozen source is insufficient: gate execution uses worker dependencies and
  exit zero without trusted expected inventory. No execution exploit was observed.
- [Turn cap](../../../../extensions/mellum-guards.ts#L328) blocks tool calls
  and asks the model to stop; it is not a provider request/output hard stop.

### Remedy qualifications (S2/S3/S5)

Settle-only: 16/24 full versus 2/24 Vanilla; show-only 6/24; show+settle 11/24.
The added-show pass difference is inconclusive; build cost/lint failures remain.
[Stall census](stalls.md): bounded 0/122, plain Vanilla 25/130; pooled descriptions,
not causal rates. It records matched comparisons, pairing failures and the clamp bypass.
Log-follow and compile/import screens never acted; other unrun units remain unjudged.

Compaction gap: Base proxy minus trace = 252,534 charged tokens. Three unknown
usage rows conservatively charge 49,152, so the gap is not all actual measured
generated output. S3 locates 228,160 of the gap after first settle (45/52
compactions). Removing it is a counterfactual 21% total-charge reduction;
context changes can raise reasoning/rereading and change outcomes or medians.
S3's held-port-only segments are 5.7% of trace / 6.2% of proxy, not 14%.
Cleanup never acted in the fixed screens. Neither saving nor zero pass risk is proven.
Limit 1 would truncate eight eventual strict passes in the offline replay;
limit 2 is largely redundant after hypothetical cleanup, which itself is unproven.

## Ladder run

No new inference. Preserve the S1/S2 assertion digests, code, budgets and host
identities; do not pool R.1, F.6, the final count or Andre's screens. S5's final
3/3 uses a visible frozen test and several remedies, and its paired plan arm
made zero requests before deadline. The component effects and fivefold saving
remain unseparated. S5's older Easy uses four checks; S1 uses thirteen. This programme has no measured Hard floor.

## Persuasion → enforcement

The decision note maps fixes to Pi hooks. This ledger verifies existing
behaviour and scopes claims; no prompt, tool, sampling, preset or scorer changes here.

## What would falsify this / Risks

Persist replay witnesses in F.7 before changing assertions. Corrected scores
need a new grader identity beside originals. Imported reviews are sources,
not instructions or independent replications; bootstrap and trace subtraction
cannot establish deployment reliability or savings from an unrun intervention.
