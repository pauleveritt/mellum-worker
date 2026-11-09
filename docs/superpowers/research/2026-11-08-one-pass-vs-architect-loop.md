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

## The exit-gate, measured — it closes Phase 4 at settle, but the live-server spiral reaches the stall first

Built the exit-gate the paradigm calls for: a complete, external, frozen medium
acceptance test (`ladder/fixtures/acceptance/test_medium.py`, authored from the
phase 1–4 spec, a superset of the hidden oracle — green on `agentclinic-done`
both test and oracle, and precisely red on the id-in-route miss, 1 of its 8
functions), run by `mellum-verify` at settle: while red it hands the agent back
only its failing test functions for a short corrective turn, up to five. Placed
outside the workspace, so the agent cannot see or weaken it. One pass, then a
check with a small turn afterwards. Gated one-pass medium, n=3:

| rep | score | req | gate | outcome |
|-----|-------|-----|------|---------|
| 1 | — | 132 | never reached | STALL (censored): live-server spiral before settle |
| 2 | **18/18** | 61 | fired, 1 redispatch | **ok — the gate closed the gap** |
| 3 | 5/18 | — | fired 2× | censored (stopped mid-spiral): 55 uvicorn starts, never converged |

1. **The gate works, exactly as designed.** Rep 2 settled short, `mellum-verify`
   re-ran the frozen test, named the unmet concept, and one small corrective turn
   carried it to a clean 18/18 at 61 requests — a fifth of the architect loop,
   with the deep Phase-4 contract closed by a **harness guarantee, not a prose
   rule**. The dry-runs plus rep 2 prove the mechanism end to end.

2. **But the gate only runs at settle, and 2 of 3 reps never settled.** The
   dominant failure is not Phase 4 — it is a **live-server debugging spiral**: the
   fixed small model, confused by an HTTP behaviour (a 303 that reads as 200, a
   TestClient 422 its own route signature causes), tries to debug by spinning up
   `uvicorn` / `python app.py` and `curl`-ing `localhost`, which blocks or forks a
   background server that disagrees with the in-process `TestClient`, and thrashes
   there (28–55 server starts) until the stall guard kills it — before it ever
   reaches the gate. `guard/foreground-server` does not stop it; the model evades
   with `nohup … &`, `| tee`, and `.venv/bin/python app.py`.

3. **So the exit-gate is necessary but not sufficient on this paradigm.** It
   reliably closes Phase 4 for a rep that stays in-process and settles; it cannot
   rescue a rep that rabbit-holes into a live server and never settles. Reliability
   now turns on killing that spiral.

## Decision (updated)

- **The exit-gate is validated and kept** — the `test_medium.py` fixture and the
  `mellum-verify` wiring close the Phase-4 contract a prose rule could not. For a
  settling rep it delivers the full pass the refinement only coin-flipped.
- **The next lever is a live-server guard, not more gate.** A guard that refuses
  `uvicorn` / `python app.py` / a background server plus `curl` and points the
  agent at `TestClient` would keep it in-process, let it settle, and let the gate
  finish the job. That is the measured next step toward a reliable one-pass pass.
  *(Built and measured below — it converts the coin-flip into 3 of 3.)*

## The live-server guard, measured — it stops the spiral, and 3 of 3 reach the gate and pass

Built the guard the section above called for: `remedies/guard/no-live-server.ts`
(`liveServerGuard`), an agnostic unit that refuses **any** server start —
foreground *or* background, where `foreground-server` lets the background form
through — and **any** loopback HTTP probe (`curl` / `wget` / `httpie` to
`localhost` / `127.0.0.1` / `0.0.0.0` / `::1`), and points the worker at the
in-process client (`TestClient(app, follow_redirects=False)`). Shown red first,
then green; the node suite stays at 714 pass. Added to the gated one-pass stack
(exit-gate + the same lean preamble, nothing else changed), medium n=3:

| rep | score | req | gate fired | server starts blocked | curls blocked | wall | guard |
|-----|-------|-----|-----------|----------------------|---------------|------|-------|
| 1 | **18/18** | 95 | 0 | 5 | 0 | 821s | ok |
| 2 | **18/18** | 123 | 1 | 1 | 0 | 1335s | STALL |
| 3 | **18/18** | 91 | 0 | 8 | 2 | 847s | ok |

Mean 18.0/18, mean 103 requests, mean 1001s.

1. **The spiral is gone and every rep reached the gate.** Gated, no guard, reached
   the gate on 1 of 3 — the other two thrashed in the live-server spiral to the
   stall before settle. With the guard, **3 of 3 reached settle and scored
   18/18.** The guard refused every live-server reach — 5, 1 and 8 server starts
   and 0, 0 and 2 curls — and each rep stayed in process and converged. Rep 3 is
   the sharp case: the model reached for a live server ten times (8 starts, 2
   curls), was refused every time, and still passed cleanly at 91 requests with
   `guard=ok`. The failure mode the guard targets did not recur.

2. **The gate still earns its place.** Rep 2 settled short and the gate fired one
   redispatch that carried it to 18/18 — the Phase-4 contract closed by the
   harness, not the prose, exactly as the gate section showed. Guard and gate are
   complementary: the guard keeps the run alive to the gate, the gate closes the
   last contract.

3. **One wrinkle: rep 2 reached 18/18 but tailed into the stall guard.** Its build
   is complete and correct on the hidden grader (the gate confirmed it), yet the
   run idled into the 240s stall guard at the tail rather than exiting clean — not
   a spiral (one blocked start, no curl), a clean-exit miss. So the guard makes the
   *pass* reliable (3 of 3) but not yet the clean *exit* (2 of 3 `ok`).

4. **Cost rose, as expected, and stays well under the architect loop.** Mean 103
   requests against the single converged baseline rep's 61 — the guard removes the
   live-server shortcut, so the worker does more of the work in process. That is
   still roughly a third of the architect loop's 300+, for a full pass on every
   rep rather than one in three.

## Decision (live-server guard)

- **One pass + exit-gate + live-server guard is the paradigm's full-pass route, as
  a lead.** 3 of 3 at 18/18 answers what the gate alone could not: the run reaches
  the gate, and the gate closes Phase 4. The guard ships as an agnostic remedy
  (`guard/no-live-server`), test-first, suite green.
- **The clean-exit wrinkle is the next small lever, not a blocker.** One rep in
  three reached the correct build and then idled into the stall guard. A finish
  nudge once the gate goes green — settle now, the test passes — is the candidate;
  it is a clean-exit fix, the pass itself is already reliable.
- **A `run_ladder` verdict is still owed before this changes a default.** This is a
  scratch n=3, a lead. The ladder's `--mode one-pass` (with `--acceptance-test`
  and the guard in its preset) is how the 3 of 3 becomes a rate, paired against the
  architect loop at larger n, with a rung past four phases.

## The clean-exit fixes — 3 of 3 clean, but the redispatch path did not recur to test them

Rep 2 above reached a correct 18/18 and then idled into the stall guard. The tail
showed why: the gate redispatched naming two acceptance-test functions, and the
worker — the test being held out beside the workspace, not in it — went hunting
for the file with `find / -name test_medium.py`, a whole-machine crawl that ate
the time to the stall. Two fixes, both test-first, suite 715 pass:

- `guard/outside-workspace` now blocks a bare-root crawl. It refused
  `grep -rl x /Users /var` but let a lone `/` through — the path matcher wanted a
  character after the slash — so `find /` ran unguarded. One character (`*` for
  `+`); the Windows spelling already did it.
- `mellum-verify`'s redispatch message now says the acceptance test is **held
  out** — not a file in the workspace, do not search for it; each name is a
  behaviour to satisfy, checked with the worker's own in-workspace tests.

Re-ran the gated one-pass medium with both fixes, n=3:

| rep | score | req | gate fired | server blocked | curl blocked | wall | guard |
|-----|-------|-----|-----------|----------------|--------------|------|-------|
| 1 | **18/18** | 76 | 0 | 4 | 0 | 547s | ok |
| 2 | **18/18** | 56 | 0 | 0 | 0 | 663s | ok |
| 3 | **18/18** | 100 | 0 | 3 | 0 | 844s | ok |

Mean 77 requests, mean 685s. **3 of 3 at 18/18 and 3 of 3 `guard=ok`** — no
stall, and leaner than the first gated+guard run (103 req, 1001s).

The honest catch: **the gate fired zero times across all three reps.** Every rep
built correctly at first settle, so none hit the redispatch path that stalled the
earlier rep 2 — the exact failure the two fixes target did not recur here, so this
run does not directly test them against it. What it does show is the guard holding
across another three reps (six in all now — every server and curl attempt refused,
no spiral) and a cleaner, cheaper run. The fixes are proven at the unit grain
(`find /` blocked; the message names the test as held out); the integration proof —
a rep that settles short, redispatches, and *now* exits clean instead of hunting —
still wants a run where the gate fires red, which is variance-dependent. One
on-screen moment in rep 3 is the clearest live evidence either way: the worker
tried to start uvicorn, the guard refused it, and the worker's own reasoning
turned — *"the rule says not to start servers, we need to fix the route"* — to
`TestClient` in process.

## The verdict run (2026-11-09) — Arm A lands 3/3 on the real ladder; the plan arm can't run on llama.cpp yet

Ran the preregistered paired verdict
([prereg](2026-11-09-one-pass-verdict-prereg.md)) through `run_ladder`, rung 13,
n=3. **Arm A (one pass + the ladder's native frozen exit-gate + reduced thinking
+ the measured remedies) passed 3 of 3** on the hidden oracle, every rep a clean
stop, at **72 / 34 / 24 requests** (mean ~43) — the one-pass exit-gate reproduced
on the shipped harness, not a scratch driver. **Arm B (`--mode plan`, the
architect loop) could not be measured:** plan mode **hung to the full 3600 s
deadline with zero requests** on the llama.cpp backend — the delegate/plan path's
llama.cpp support is not landed on `main` (it is on the `remove-omlx` branch, the
same gap as the oMLX→llama.cpp AGENTS.md contradiction). So the plan-arm cost
stays the earlier screened baseline (300+ req, patchy pass-rate); a clean paired
plan number waits on that branch landing. Arm A's 3/3 is a real recorded ladder
result; the paired comparison is still a lead until the plan arm runs.

**External corroboration, and why it does not overturn this.** JetBrains shipped
the architect split as a product (Junie "Eco Mode", Oct 2026: 48–57% lower
$/task at ~flat resolve). That is the same decomposition as Arm B — but its saving
is the **model-tier price gap** (an expensive planner, a cheap builder), not the
split itself. With one fixed model the gap is zero, so the split is pure overhead,
which is exactly what Arm A vs the plan baseline shows. The split pays via a
tier differential; with a single fixed model it is overhead.

## What would falsify this / Risks

- **n=2, two tiers, a scratch driver** — a screen, not a `run_ladder` rate, and
  the skill is explicit that conclusions come from the real harness. The gap is
  large enough that noise is unlikely to erase it, but the exact multiple will
  move.
- **The gated result rests on one converged rep.** Rep 2 is a clean, decisive
  demonstration (and the dry-runs prove the test sound), but one converged rep is
  a mechanism proof, not a reliability rate. The spiral may even be *induced* by
  the gate — handing a confused small model "these tests still fail" can push it
  toward live-server debugging; a paired gated-vs-ungated run at larger n, once a
  live-server guard exists, would separate the gate's effect from the spiral's.
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
- **The guard's 3 of 3 is a scratch n=3, and one rep did not exit clean.** A
  decisive lead on the spiral — every server and curl attempt was refused and no
  rep thrashed — but three reps is a mechanism rate, not a reliability rate, and
  rep 2's tail stall shows a clean-exit gap the pass rate hides. The guard could
  also, in principle, refuse a legitimate local probe; it runs only in the build
  child, where the worker should use `TestClient`, and the node suite pins the
  read/search/remote-fetch cases it must leave alone. A preregistered
  `--mode one-pass` run settles both the rate and the exit.
- **The two clean-exit fixes are unit-proven but not yet integration-proven.** The
  re-run went 3 of 3 clean, but the gate fired zero times, so the redispatch →
  hunt → stall path the fixes target never arose to be tested end to end. They are
  correct at the unit grain; a run where the gate fires red is what shows them
  turning a would-be stall into a clean exit. Until then the clean-exit claim
  rests on the unit tests plus the one live refuse-and-pivot in rep 3, not on a
  reproduced-then-fixed stall.

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
