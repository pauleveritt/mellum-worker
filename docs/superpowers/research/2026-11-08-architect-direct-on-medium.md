# Architect-direct cuts the architect's deliberation on medium — the easy wash was a floor effect

**What is measured:** the medium plan-arm screen the 2026-11-07 note called for
(n=3 per arm, the shipped plan loop driven through `pi -p`, the hidden oracle
summed across the four per-phase grader files to 18), comparing the default
architect with `MELLUM_DELEGATE_ARCHITECT_DIRECT=1`, on a **request-count** cost
axis with a loose hang-guard. **What is conjecture:** that the architect's
request count is the thing the nudge moves (not the plan's step count, which it
leaves alone); that the small score dip is n=3 noise rather than a real cost;
and that collapsing the architect's request variance is a durable effect, not a
three-rep coincidence.

## The rig (preregistered, same as the easy screen)

Both arms run the **medium win config** — `worker-direct` + `smoke` +
`preset:medium` + `repeat-loops` + `outside-workspace` + `exists`,
`MELLUM_TURN_CAP=25` — and the **only** difference is architect-direct off
(ctrl) or on (adirect). worker-direct carries the reduced-thinking nudge that is
part of the medium lead, so it is held constant across both arms. The task is
the four phase prompts concatenated; each rep starts from a clean
`suites/medium/base` seed. Primary outcome: **architect requests** (profiler
role `architect: …`). Score/18 is a guardrail that must not regress. Wall is
informational; the DEADLINE 3600s / STALL 300s guard is a loose hang-guard, and
any rep hitting it is censored. Run on HEAD (`33e0b92`) with the fixed
`guard/foreground-server`.

## Result (medium, n=3 per arm, score out of 18)

| arm | arch req | total req | score | steps | converged |
|-----|----------|-----------|-------|-------|-----------|
| ctrl (arch-direct off) | 32 / 133 / 73 → **79.3** | 458 / 322 / 282 → **354** | 16·12·18 → **15.3** | 20·15·19 | **3/3** |
| adirect (`ARCHITECT_DIRECT=1`) | 32 / 38 / 66 → **45.3** | 329 / 441 / 173 → **314** | 17·14·13 → **14.7** | 22·21·12 | **3/3** |

What it shows:

1. **Architect-direct cuts the architect's requests — the opposite of easy.**
   Mean architect requests fell **79.3 → 45.3** (~43%), and the spread
   collapsed from **32–133** to **32–66**. The ctrl architect fell into a
   133-request deliberation loop on rep 2 — the exact "thinks instead of does"
   churn the observation named — and architect-direct had no rep anywhere near
   it. On easy the same nudge was a wash (15.0 → 13.0, overlapping ranges)
   because a single tiny phase gave it nothing to re-derive; on medium's
   four-phase spec it bites, exactly as the easy note predicted.

2. **The saving is deliberation per plan, not fewer steps.** adirect did not
   plan fewer steps — it split into 22 / 21 / 12 against ctrl's 20 / 15 / 19.
   The nudge does not make the architect carve a smaller plan; it makes the
   architect stop re-reading and re-deriving while it carves whatever plan it
   carves. "Read each file ONCE, write the plan directly" is doing the work its
   wording claims.

3. **Total requests fell too, modestly.** 354 → 314 (~11%). The architect is a
   small slice of the total (workers dominate: ~270 each arm), so a 34-request
   architect cut moves the total only a little. Worker requests were a wash
   (274.7 vs 269.0).

4. **Score dipped slightly, within n=3 noise.** 15.3 → 14.7 mean, median 16 →
   14. Both arms have one near-perfect rep and one low rep (ctrl 12, adirect
   13); the dip is inside the three-rep spread, not a clean regression, but it
   is **not** clearly neutral either. This is the open question a ladder run
   must settle: does the architect-request cut cost correctness, or is the dip
   noise?

Convergence was **3/3 both arms, 6/6 overall, zero stalls** — the
`guard/foreground-server` fix continues to hold end to end.

## Decision

- **Architect-direct earns its place in the medium win stack.** This screen
  isolates its contribution: on the tier where it was adopted it cuts architect
  deliberation ~43% and kills the request blowups, where on easy it did nothing.
  The "wash" from 2026-11-07 was a floor effect of a one-phase spec, not
  evidence against the lever — the easy note said as much, and this confirms it.
- **The lever is tier-dependent, like the turn cap.** A lever measured as a wash
  on one tier can be a real win on the next; test it on the tier where it was
  adopted, not only the cheap one. This mirrors the cap25 tier-dependence
  (2026-11-06).
- **Still a lead, not a rate.** It stays as it already is (part of the adopted
  medium win); nothing changes on the strength of a scratch screen. The
  preregistered `run_ladder` for the medium win must (a) confirm the
  architect-request cut and (b) check the score holds at larger n.

## What would falsify this / Risks

- **n=3, one medium spec, scratch driver** — a screen, not a `run_ladder` rate.
  The architect-request cut leans on ctrl's single 133-request blowup; drop that
  rep and ctrl is 32/73 (mean ~52) against adirect's 45.3, a much smaller gap.
  A ladder run with more reps could shrink the effect.
- **The score dip may be real, not noise.** If a larger-n medium run shows
  adirect's score consistently below ctrl's, the architect-request saving is
  being bought with correctness and the trade must be weighed, not banked.
- **The request count treats every request as equal.** An architect request
  carries a large spec prompt; cutting 34 of them saves more wall than 34 worker
  requests would. Report both axes — here wall moved the same direction
  (adirect reps were not slower).
- **Variance collapse may be the artifact.** If repeated runs reproduce ctrl
  blowups but adirect never blows up, the real win is variance, not the mean —
  a different and arguably better claim. If adirect also blows up at larger n,
  the tight 32–66 band here was luck.
