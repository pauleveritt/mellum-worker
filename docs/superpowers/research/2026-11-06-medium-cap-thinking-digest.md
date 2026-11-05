# Medium plan loop — the turn cap is tier-dependent, reduced thinking is the fix, the state digest backfires

**What is measured:** a sequence of medium screens (n=3 each, the shipped plan
loop driven through `pi -p`, the hidden oracle summed across the four per-phase
grader files to 18) that vary three off-by-default levers on top of the
committed worker controls — a per-worker turn cap, a reduced-thinking nudge, and
a state digest handed to each fresh worker. **What is conjecture:** that the flat
turn cap is tier-dependent (good on easy, starving on medium); that cutting the
per-turn thinking makes a step cost fewer turns so the cap fits; and that the
digest's inline file contents cost more in prefill than they save in re-reads.

## Provenance

Real shipped extension (`extensions/mellum-worker.ts`, the `PLAN` branch), real
local model (Mellum Q4_K_M via llama-server on `:8001`), real hidden grader
(`learn/code/suites/medium/grader`). Driven from a scratchpad driver, **not**
`run_ladder` — a repeated screen of the shipped loop, a lead, not a recorded
rate. Each rep starts from a clean `suites/medium/base` seed; the task is the
four phase prompts concatenated (the whole spec). The medium base ships a real
`tests/test_home.py`, so `hasTests` is true there and the no-tests clause stays
off — correctly, there are tests.

## Results (medium, n=3, score out of 18)

| arm | rep1 | rep2 | rep3 | median | mean | floor |
|-----|------|------|------|--------|------|-------|
| baseline — plain plan-mode (prior screen) | 7 | 15 | 17 | 15 | 13.0 | 7 |
| full stack **+ cap 25** | 10 | 18 | 8 (DEADLINE) | **10** | 12.0 | 8 |
| full stack **+ cap 25 + reduced thinking** | 18 (DEADLINE) | 15 | 16 | **16** | **16.3** | **15** |
| full stack **+ cap 25 + reduced thinking + digest(contents)** | 10 (DEADLINE) | 14 (DEADLINE) | 13 (DEADLINE) | **13** | 12.3 | 10 |

"full stack" = `architect-direct` + `worker-direct` + `smoke` + `preset:medium`
+ `repeat-loops` + `outside-workspace` + `exists`. Baseline row is from
[2026-11-05-plan-mode-n3](2026-11-05-plan-mode-n3.md).

## What the arc showed

1. **The flat turn cap is tier-dependent.** `MELLUM_TURN_CAP=25` bounded easy's
   thrash and held easy at 4/4. On medium it *starved* the bigger steps: the cap
   fired repeatedly, workers were cut off before finishing phase-3/4 routes
   (`POST /complaints` → 405), and the median fell to **10** (below baseline's
   15). A setting measured on one tier does not transfer to the next — the
   medium remedies are not the easy stack carried over.

2. **Reduced thinking is what makes the cap fit.** Mellum exposes no
   reasoning-effort dial (`supportsReasoningEffort: false`), and
   `enable_thinking=false` pollutes the content channel, so the only working
   lever is the prompt. Telling the worker to think in one short sentence per
   tool call made each step cost fewer, denser turns — so cap 25 covered the
   work instead of cutting it off. Median **10 → 16**, floor **8 → 15**: the
   low-variance collapse that hit both the baseline (7/18) and the capped stack
   (8/18) disappeared. This is the medium lead of the session.

3. **Smoke catches structural zeros only.** The parse + import + template check
   caught a would-be-zero in isolation (an `HTMLResponse` import error, a
   `{{ extends }}` template slip) and left clean builds alone. But medium's lost
   points are *incomplete behaviour* — a route that returns 405 because it was
   never written — which smoke cannot see. That is the per-step-gate /
   acceptance-test frontier the plan loop deliberately dropped; no structural
   check closes it.

4. **The state digest backfires with inline contents.** The digest cut a rep's
   read/explore calls (182 → 140) and total tool calls (316 → 279) — the
   manifest genuinely kills the `ls`/`find` cold start. But re-sending each
   file's *contents* in every one of ~16 worker briefs inflated prefill: in the
   same 30-minute wall the worker completed *fewer* turns, so *less* got done —
   **all three** digest reps hit the deadline and scored 10 / 14 / 13 (median
   13), below the cap25+terse floor of 15. The manifest half is cheap and good;
   the inline-contents half
   is net-negative on a many-step tier. A manifest-only digest is the untested
   cheaper variant.

## Decision

- **`cap 25 + reduced thinking` is the medium lead** — it beats the baseline on
  median (16 vs 15), mean (16.3 vs 13) and, most of all, floor (15 vs 7). Adopt
  only after a preregistered `run_ladder` run confirms it; until then every
  lever stays **off by default** and the shipped loop is unchanged.
- **The state digest (with contents) is a recorded negative** — do not adopt.
  Keep it off-by-default and reproducible for the manifest-only follow-up.
- Smoke, architect-direct, hasTests remain off-by-default research levers; none
  is a standalone win on this evidence.

## What would falsify this / Risks

- A preregistered ladder run where `cap25 + reduced thinking` ≤ baseline across
  rungs — then the screen's median-16 is variance, not a win.
- **Many levers at once.** The win bundles five changes; the attribution to
  "cap + thinking" is inference, not an ablation. A clean ablation (terse alone;
  terse + architect-direct; + smoke) is unmeasured and owed before any default
  change.
- `cap25 + reduced thinking` rep 1 still hit the 30-min deadline (it scored 18
  regardless). Speed is marginal, not solved; a tighter deadline could cost a
  rep points. The digest aimed at this and made it worse.
- n=3, one concatenated prompt, scratch driver — a screen, not a ladder rate.
- The manifest-only digest is conjecture: it might recover the read savings
  without the prefill cost, or the cold-start reads might not be the real
  wall-time driver at all.
