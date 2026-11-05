# Preregistration: the Vanilla floor on the portable rig

Fixed before any counted session. The rig is defined in the
[design](../specs/2026-11-05-portable-floor-design.md); this note fixes the
arm, n, scoring, validity rules and the portability reading. The why is in the
[baselines and remedies audit](2026-11-05-baselines-and-remedies-audit.md).

**What is measured.** Nothing yet. The budget values in the design come from
the per-session distributions of LC.34–LC.38 and the M5 Max's observed
throughput. Those are measurements of other arms, not of this floor.

**What is conjecture.** That a session's outcome on a conforming host does
not depend on which GPU served it, once sessions are limited by requests and
tokens instead of seconds. The portability reading below tests it, coarsely.

## Arm and task

- **Arm:** Vanilla plus the recorder, with no worker extension, remedy unit,
  gate, repair or feedback. It runs natively on the inference host, as the
  design's unprivileged session user. On the Mac it runs as the operator's
  account and is flagged `uncontained`. No Docker is used.
- **Task:** Easy Phase 1, the same prepared inputs as LC.36–LC.38.
- **Scoring:** the hidden oracle, the code-health checks, the layout check,
  and acceptance package `af4122164322e6446b5cb12728693ca32749fdaec2606aa35e1bcaf9e41e3dd9`
  run once at the end in observe-only control mode, as the selective arms of
  LC.34 and LC.35 were. The model never sees any of these results.
- **Limits:** the design's session budgets. That is 120 requests, 64,000
  output tokens, 16,384 per request, a 180 s open tool call and a 3,600 s
  wall safety net.

## Hosts and n

| Host | Class | Counted sessions |
| --- | --- | ---: |
| A | one allowlisted CUDA GPU of one generation, Ampere or Ada | 6 |
| B | one allowlisted CUDA GPU of a different generation, Hopper or Blackwell | 6 |
| M | the M5 Max, Metal | 3 |

**A host is one GPU model under one pin card.** A rental is one instance of
it. A host may span several rentals of the same GPU model, and each rental
has its own host card.

- Each rental must pass conformance before its first counted session and
  again after its last.
- Sessions run one at a time on each host, with the design's sweep between
  them.
- Hosts may run in parallel with each other, since each is its own machine.

**A rental lost mid-cohort.** Its completed sessions count if the rental's
pre-check passed and each session's records reconcile. They are flagged
`post-check unavailable`. A session in flight when the rental was lost is
invalid. The host continues on a fresh rental of the same GPU model after
that rental passes its own pre-check. A lost rental does not count against
the replacement cap. Only the invalid session in flight does.

### Amendment 2026-11-05, before any counted session

The Mac qualification ([record](../../../evals/2026-11-05-portable-floor/qualification/README.md))
found that host M fails conformance on numerics. On Metal at b11669, `llama-perplexity`
returns NaN after the first chunk; CPU on the same build and weights is finite. By the user's
decision on 2026-11-05, **host M is excluded** and the floor is hosts A and B only, n = 6
each. Two consequences are fixed here, before collection:

- **The perplexity reference is rental A**, not the Mac. Host A's numerics item records the
  reference value; host B is compared with it at a relative tolerance of **1%**, fixed now
  rather than calibrated later.
- **The pooled table is A+B.** The A+B+M table and the Mac's descriptive reading are
  dropped. Everything else in this preregistration stands as written above.

## What each session records

- **Completion class:** `settled`, `stalled` at the open-tool cutoff,
  `budget`, `model_error`, or `invalid`.
- **Hidden oracle:** each check, and whether the checks actually ran.
- **Code health**, and **layout preserved**.
- **Acceptance package:** each check by name, including title override,
  startup and nonempty passing project tests.
- **Usable**, by the LC.34 rule: settled, every hidden check run and passed,
  health passed, layout preserved, and the complete package passed.
- **Budget:** provider requests, output tokens and peak full context, all
  relay-reconciled, with any unknown usage reported as unknown.
- **Host card** reference, and the wall-clock time, recorded but not used.

## Readings

All counts are reported per host first, then pooled across A and B, then
pooled with M. Each comes with a Wilson 95% interval.

1. The usable count. **Expected in advance to be near zero.** The selective
   arms, which are Vanilla plus five remedies, were usable 1/20 and 0/20. A
   floor of 0/15 is the anticipated result, not a finding.
2. The pass count for each hidden and acceptance check. This is the floor's
   real content: which requirements plain Vanilla misses, and how often.
3. Completion classes. Any `budget` ending is reported with its trajectory.
4. Budget distributions: median, range and total for requests, output and
   peak context.

## Validity and replacement

- A session is **invalid** if any of these happens:
  - it reaches the wall safety net;
  - it has an unrecovered proxy, transport or integrity failure;
  - the server logged a generation the proxy did not create, which means the
    proxy was bypassed;
  - its sweep fails, or the Mac preflight finds a listener already present;
  - its host fails the post-cohort conformance re-check.
- A transport error that Pi recovers from is **counted** and flagged, with
  its unknown usage handled as the design says.
- Invalid sessions are retained and reported, then replaced in order. Each
  host gets at most two replacements. A third invalid session stops that
  host, which is then reported as incomplete.
- Model outcomes are never replaced. That covers a stall, a budget ending, a
  model error, broken code and any failed check. There are no favourable
  retries and no optional stopping.

## Portability reading

Compare hosts A and B on three components: hidden all-pass, startup pass and
settled.

- **Not portable** if any of the three differs by four or more of six. Four is
  the smallest gap Fisher's exact test separates at about p < 0.1 with six per
  host: 0/6 against 4/6 gives p = 0.061.
- **Not portable** also if one host has three or more `budget` endings and the
  other has none.
- Otherwise **pooling is allowed** for later single-arm references on
  conforming hosts.

Passing does not show that the hosts are equivalent. At six per host, gaps of
three or fewer are not detectable and are not claimed absent. M is reported
descriptively and is not part of the rule.

Whatever the reading, every later comparison runs its arms interleaved on each
host it uses.

## What this decides

It decides no default and no comparison. A complete cohort is fifteen counted
valid sessions, or fewer with each stopped host reported. Once complete, it is
**the** Vanilla reference for this rig. Later arms are read against it,
interleaved on the same hosts.

The record goes to `evals/<date>-portable-floor/` with the raw evidence
stripped. Raw traces go to a `research-YYYY-MM-DD` release only after the
user's approval.

## What would falsify this

- Hosts A and B fail the portability reading. Then the GPU, not just its
  speed, changes outcomes, and every later reference must be blocked by host.
- Sessions end in `budget` far more often than the old deadline censored
  them on the Mac. Then the budget values are wrong for this arm, and the
  cohort reports that rather than re-running with new values.
- The Mac's three sessions fall outside the range of the twelve CUDA
  sessions on every component. That would not trigger the rule, but it would
  be a lead that Metal and CUDA differ.

## Risks

- One task repeated is still one task. The floor says nothing about medium
  or hard.
- Six per host detects only large differences. Pooling is a convenience for
  references, not evidence of equivalence.
- The acceptance package is a structural proxy. A placeholder introduction
  passed it in LC.36 and LC.38, so "usable" can overstate quality.
- A budget limit and a wall-clock deadline censor different sessions. This
  floor is incomparable with LC.31–LC.38 on timing and budgets by design.
- Native isolation is weaker than the LC.33 containment. A session can see
  world-readable files and loopback ports on the pod, and the Mac sessions
  share the operator's account. The disposable pod, the sweep and the bypass
  check bound this risk, but they do not make sessions as isolated as before.
- Rented hosts can disappear mid-cohort. The replacement cap bounds what that
  costs, but a lost host leaves an incomplete per-host table.
