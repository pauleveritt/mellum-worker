# A stop-cap and a refuse-to-settle gate deadlock — 2026-10-31

## What is measured / What is conjecture

**Measured.** On the local M3 (Metal, cached Q4, `llama-server`, the same rig as
the 2026-10-30 vanilla baselines), easy n=3, with the fixed `mellum-ncm` gate
plus the full remedy stack including `guard/cap-turns(120)`:

| rep | pass | miss | turns | tool_calls | wall | budget blocks | ncm refusals | settled |
|---|---|---|---|---|---|---|---|---|
| c38475 | ✗ | 4 | 35 | 34 | 143 s | — | — | self-exit |
| 11b28f | ✓ | 0 | 125 | 120 | 702 s | 5 | 87 | yes |
| e872d0 | ✗ | 3 | 296 | 120 | **1799 s** | **349** | **193** | **0** |

n=3 = **1/3**. The deadline rep is the finding. Its `tool_calls` sat pinned at
exactly 120 — the cap's ceiling — while the trace shows `agent_settled` **zero**
times across 296 turns: it never once settled before the 1800 s deadline cut it
off. The two remedies gave opposite orders. `guard/cap-turns` refused the
worker's tool calls 349 times (*"Tool-call budget reached — stop"*), and in the
same session `mellum-ncm` refused the worker's settle 193 times (*"the tests
still fail, so you are not done — keep going"*). Capped, it could not act; gated,
it could not stop; so it churned text turns to the wall and timed out with three
Phase-1 home checks still unmet.

**The contrast is the proof.** The one rep that passed (11b28f) took only **5**
budget blocks — the cap barely bit — so `mellum-ncm`'s 87 refusals could drive
the build to green at 125 turns. The deadlock is not that the two remedies
coexist; it is that the cap binding *hard* (349 blocks at the ceiling) and the
gate refusing to settle are a contradiction with no exit. The budget says the
run is over; the gate says the work is not done; neither yields to the other.

**Root cause (measured).** `guard/cap-turns` and `mellum-ncm` each own one half
of the stop/go decision and neither knows about the other. The cap caps
*tool calls*. The gate blocks *settle*. Once the cap is exhausted the worker's
only remaining move is a text turn, and a text turn cannot make a failing test
pass — so every settle after that hits the gate, is sent back, and spends
another text turn it cannot use. There is no state where both are satisfied
short of the deadline.

**Conjecture.** That reconciling the two removes the churn without losing the
pass: if `mellum-ncm` stands down once the step budget is exhausted — lets the
run settle red rather than refusing a settle the worker can no longer act on —
the deadline rep would end at its cap instead of the wall, scored on its real
(incomplete) state, and the pass rep is untouched because its cap never bound.
Unmeasured. The cleaner read is that a hard stop-cap and a refuse-to-settle gate
answer the same question with opposite defaults and should not both be on at
once without that reconciliation — which is the user's "one remediation at a
time" instinct, vindicated by a run.

**This is why acceptance + ncm is being re-measured alone.** The 5-remedy stack
confounds the gate's effect with the cap's. The gate's isolated effect on easy —
does an external, complete, unweakenable acceptance test, re-run and
re-dispatched, lift the home-miss pass rate — needs the gate measured without
the cap, the quality check, or the non-block tool fighting it. That run is the
next step; this note records the confound that forced it.

## What would falsify this / Risks

- **Acceptance + ncm alone is also ≤ 1/3.** Then the gate itself does not lift
  easy and the deadlock was a sideshow, not the thing hiding a win — the
  redispatch message is too opaque for the model to act on, a remedy problem,
  not a wiring one (the same risk the inert-gate note named).
- **The deadlock reproduces without the cap.** If a no-cap acceptance + ncm run
  also churns to the deadline, then `mellum-ncm` alone can trap a worker that
  cannot fix the failing concept — the gate needs its own give-up-after-N exit,
  independent of any cap. `NCM_MAX` (default 5) is meant to be that exit; if it
  is not bounding the loop, that is the real bug.
- **Small n.** Three reps, one of each outcome. The deadlock is a single
  reproduction (e872d0); the mechanism is legible in the trace, but the *rate*
  at which a hard cap and the gate deadlock is not measured.
- **Cap grain.** `cap-turns(120)` caps tool calls, and the worker's text turns
  are unbounded — the 296 turns at 120 tool calls are the tell. A cap that
  counted text turns too would stop the churn, but would also cut a slow,
  genuinely-progressing run; untested which matters more.

## The clean re-measurement — acceptance + ncm alone (added 2026-10-31)

The deadlock forced the run this note's first falsification bullet named: the
gate measured without the cap, the quality check, or the non-block tool. Same
rig, easy n=3, **bare + `mellum-acceptance` + `mellum-ncm` only**.

| rep | pass | miss | turns | tool_calls | wall | gate fired | exit |
|---|---|---|---|---|---|---|---|
| ace708 | ✗ | 4 | 18 | 18 | 48 s | no | **stalled** |
| 001917 | ✗ | 1 | 129 | 123 | 900 s | yes | settled |
| 5e5cab | ✗ | 4 | 21 | 21 | 59 s | no | **stalled** |

n=3 = **0/3** — below bare (1/3). But the mechanism is not the gate being too
opaque (the bullet's guess). It is that **the gate acts only at settle, and two
of three reps never reached settle.** Both stalled reps were killed at the 120 s
stall limit running a foreground server — the `stalled` marker reads
`{"command": ". .venv/bin/activate && python main.py"}` — so `agent_before_settle`
never fired and `mellum-ncm` appeared zero times. This is pathology #8, a server
nobody can stop, upstream of the gate; it also built `main.py`, not `app.py`.

The one rep that reached settle (001917) is the gate working as designed: it
engaged, re-ran the contract, and drove the build from `miss=4` to `miss=1` —
doctype, `lang`, and the 200 + tagline all landed — settling cleanly with only
`test_home_still_has_navigation_links` short. The gate helps a run that survives
to settle; it cannot touch a run that dies before it.

**Decision.** The binding constraint on easy is the pre-settle foreground-server
stall, not the settle gate. `acceptance + ncm` cannot lift easy on its own
because two of three runs stall out before the gate can act. The indicated pair
is the non-blocking-command / server guard (pathology #8's answer —
`tool/background-long-commands`, the "long running/blocking console runs" remedy)
**with** the gate, so the worker survives to the settle the gate guards. That
guard issues no stop/go order — it backgrounds a command — so it does not
reintroduce the `cap-turns` × `ncm` deadlock. Measuring `nonblock + acceptance +
ncm` on easy is the next step; one remedy added to the gate, not a stack.

This refines the inert-gate note's conjecture rather than flatly refuting it: the
gate does help once reached (`miss` 4→1), but easy is gated upstream by the
stall, so the gate alone moves no pass.
