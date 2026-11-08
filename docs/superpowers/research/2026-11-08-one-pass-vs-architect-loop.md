# One agent in a single pass beats the architect-split loop on both tiers — ~5× cheaper at equal or better score

**What is measured:** a scratch screen (n=2 per tier) pitting a **single agent
building the whole section in one pass** — no architect, no step docs, no
delegation — against the shipped **plan-delegation loop** (architect splits the
spec into per-step docs, a fresh worker builds each), on a **request-count** cost
axis with a loose hang-guard. The one-pass agent runs the easy/medium
prompt+guard stack **minus the per-step turn cap**, under a reduced-thinking,
do-it-all-in-one-pass preamble. Easy = Phase 1 home page (hidden oracle /4);
medium = four phases (hidden oracle summed /18). **What is conjecture:** that the
saving is the delegation overhead itself (the architect's deliberation plus every
worker re-reading the spec from a cold context), not the stronger preamble alone;
that the one-pass agent holds score at larger n (medium lost two points, the same
Phase 4 shape every arm leaks); and that one agent does not fall over on a spec
larger than four phases, where the plan loop's divide-and-build was meant to earn
its cost.

## The rig

The one-pass arm is `MELLUM_WORKER_CHILD=1` one-shot: `/mellum <task>` runs the
whole section in **one agent** until it settles — no architect, no plan, no
step docs. It loads the same remedy units the tiers use —
`name-the-layout` + `python-developer` + `foreground-server` + `verify-the-spec`
+ `repeat-loops` + `outside-workspace` + `exists` — but **not** the turn cap: a
single agent carrying the whole app must not be cut off at a per-step budget. The
preamble is the reduced-thinking, no-split, run-the-tests line measured in the
prompt lab (verbatim at the foot of this note). Each rep starts from a clean
`suites/<tier>/base` seed. Primary outcome: **total requests** (every profiler
line). Score (/4, /18) is a guardrail. Wall is informational; DEADLINE 900s
(easy) / 2400s (medium) with STALL 240s is a loose hang-guard, and any rep
hitting it is censored. The plan-loop baselines are the figures measured earlier
this cycle, for context — not a paired arm in this run.

## Result (one-pass, n=2 per tier)

| tier | score | total req (reps) | mean req | guard | plan-loop baseline |
|------|-------|------------------|----------|-------|--------------------|
| easy (/4) | **4.0** | 11 · 12 | **11.5** | ok, ok | 4/4 @ ~52–64 req |
| medium (/18) | **16.0** | 62 · 78 | **70.0** | ok, ok | ~300+ req, pass-rate patchy |

What it shows:

1. **One pass is ~5× cheaper at equal or better score.** On easy it reaches a
   clean 4/4 at ~11.5 requests against the plan loop's 52–64 — the architect and
   the per-step workers were spending four-to-five times the requests to land the
   same single page. On medium it reaches 16/18 at ~70 requests where the plan
   loop ran 300+ and did not reliably pass. The delegation the loop adds is pure
   overhead on these two tiers: a page the architect never needed to carve, and
   workers each paying to re-read a spec the one agent already had in context.

2. **The score held on easy, slipped two points on medium.** Easy was 4/4 both
   reps. Medium was 16/18 both reps — the same two points every arm has leaked,
   the Phase 4 resolve/reopen id shape. One pass did not fix that miss, but it did
   not make it worse, and it got there for a fifth of the requests.

3. **It was consistent across reps, not a lucky single run.** Easy 11 and 12;
   medium 62 and 78. Both tiers reproduced within a tight band, and both reps on
   both tiers finished clean (`guard=ok`, no stall, no censor). The plan loop's
   medium runs, by contrast, swung widely and sometimes failed to converge.

## Closing the last two points — a prose refinement is a coin-flip, not a lever

The medium gap is Phase 4: the hidden oracle constructs the data object
**directly** and asserts a field is auto-assigned and unique, so the rule must
live on the type that owns the data (an automatic default), not be assigned in
the one route the happy path exercises. The one-pass agent takes the easy side —
assign on the caller — which passes the route and fails direct construction.

A second screen strengthened the preamble with an **agnostic** reading
discipline (names no file, route, field, count or value): treat every clause of a
requirement as binding, and build a rule the spec says must hold *automatically*
into the type that owns the data, so it holds on direct construction, not only
along the route you call. Five medium reps, one censored:

| rep | score | req | guard |
|-----|-------|-----|-------|
| 1 | 16/18 | 53 | STALL (censored — redirect-debug-via-live-server rabbit-hole) |
| 2 | **18/18** | 30 | ok |
| 3 | 15/18 | 41 | ok |
| 4 | 15/18 | 62 | ok |
| 5 | **18/18** | 44 | ok |

Converged scores **18 · 18 · 15 · 15** — a full pass on **2 of 4** converged
reps, mean 16.5, median at the unrefined 16/18 baseline. The refinement moves the
**ceiling** to 18/18 but not the **floor**: when the first draft happens to get
Phase 4 (and the redirect status) right it finishes clean; when it does not, the
prose rule does not reliably rescue it, and once the agent rabbit-holed into
curling a hung server it had started itself. This is the AGENTS.md lesson intact —
**for a fixed small model, a prose rule lands unreliably; prefer a harness
guarantee.** A reliable full medium pass is not a better sentence; it is the
exit-gate route — an external, complete acceptance test that re-runs the hidden
oracle's own checks and re-dispatches the specific failure until the data
invariant holds, which the worker cannot talk its way past.

## Decision

- **One pass is a strong lead against the plan loop on easy and medium** — the
  tiers the plan loop was built for. It is cheaper on requests by ~5×, at least
  as correct on the hidden oracle, and more reliable rep-to-rep. Nothing ships on
  the strength of a scratch screen: this is a lead, not a rate.
- **A reliable full medium pass needs a harness guarantee, not a better prompt.**
  The agnostic preamble refinement reaches 18/18 on half the converged reps but
  leaves the floor at 15–16; it is a coin-flip. The route to a dependable 18/18
  is the exit-gate lead (external, complete, unweakenable acceptance test
  re-dispatching the oracle's own failing check), not more prose.
- **What a `run_ladder` must settle before this changes a default.** The plan
  loop now has a ladder mode (`--mode plan`, rung 13). A one-pass mode belongs
  beside it — the same `direct_agent_dir` plumbing driving the one-shot child —
  so the two can be run as paired, preregistered arms at larger n. The verdict
  run must (a) reproduce the request gap through the real harness, (b) check the
  medium score holds and is not bought by a self-authored exit, and (c) add a
  tier the plan loop's splitting was actually meant for — a spec past four phases
  — because that is where one agent is most likely to run out of room.
- **This does not retire the plan loop; it bounds where it pays.** The loop's
  case was always the long spec one agent cannot hold. These two tiers do not
  test that. The honest reading is "the loop is overhead at this size," not "the
  loop is never worth it" — the ladder's larger rung is how we learn which.

## What would falsify this / Risks

- **n=2, two tiers, a scratch driver** — a screen, not a `run_ladder` rate, and
  the skill is explicit that conclusions come from the real harness. The gap is
  large enough that noise is unlikely to erase it, but the exact multiple will
  move.
- **The stronger preamble is a confound.** The one-pass arm carries the
  reduced-thinking prompt; the plan-loop baselines were measured before it.
  Part of the saving may be the prompt, not the single-pass structure. A paired
  ladder arm that gives both the same preamble would separate them.
- **The medium score may erode at larger n, or hide behind a weak exit.** The
  one-pass agent judges its own done-ness; a run can exit confident on an
  incomplete build (the exit-gate lead). 16/18 twice is encouraging, not proof —
  a mediated, external, complete acceptance test is how that claim gets earned.
- **One agent may not scale past four phases.** The whole case for splitting is
  the spec too large to hold in one context. If a six- or eight-phase rung shows
  one pass degrading — dropping late requirements, thrashing, or blowing the
  request budget — while the plan loop holds, then the loop earns its cost
  exactly where this screen could not see it, and "one pass wins" is true only
  up to a size this run never reached.

---

**The one-pass preamble (verbatim):**

> Think briefly — one short sentence of reasoning before each action, no
> back-and-forth debating. Build the whole thing yourself in a SINGLE PASS: do
> NOT split it into steps, do NOT delegate, do NOT write a separate plan. Read
> the spec files in this directory once (the specs/ folder, AGENTS.md, a
> roadmap), then implement every requirement they state, in order — create each
> file complete and correct, honouring every named contract (module, route,
> variable, field, exact count, verbatim string). If the spec has multiple
> phases, implement them ALL. When the code is written, run the project's own
> tests, fix whatever fails, and stop only when every requirement is met.
