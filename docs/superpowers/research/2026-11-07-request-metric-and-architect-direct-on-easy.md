# The cost unit is requests, not seconds — and architect-direct is a wash on easy

**What is measured:** a re-instrumented easy plan-arm screen (n=3 per arm, the
shipped loop driven through `pi -p`, the hidden phase-1 oracle scored out of 4)
comparing the default architect with `MELLUM_DELEGATE_ARCHITECT_DIRECT=1`, read on
a **request-count** cost axis instead of wall-clock. **What is conjecture:** that
counting requests (turns) rather than seconds is the reproducible cost unit; that
a loose hang-guard plus censored-rep handling removes the wall-deadline confound;
and that architect-direct, the measured *medium* win, has little to bite on when
the easy spec gives the architect almost nothing to re-derive.

## Why the method changed

A fixed wall-clock deadline is not a measurement — it is a guillotine. It is not
reproducible (wall depends on machine load, not the harness), it **confounds two
axes** (the same number caps cost *and* depresses score, because a truncated
workspace grades lower), and it invites tuning (move the deadline, get a nicer
number — coding to the measurement). The prior easy screen already showed the
damage: a rep graded 4/4 yet was recorded against the 480s wall because its
verification tail ran long
([2026-11-05](2026-11-05-plan-worker-direct-and-rethink.md), line "A long
verification tail").

The rig this note uses, preregistered before the run:

- **Primary cost = total requests (turns)**, read from the context profiler
  (`MELLUM_DELEGATE_PROFILE`, one JSON line per request tagged with the agent
  role). Requests are reproducible, machine-independent, role-splittable, and are
  what the loop actually bounds (`MELLUM_TURN_CAP`). They are countable even on a
  killed run. Wall is reported but never decides.
- **Score/4 is a guardrail**, not the headline — it must not regress.
- **The wall cap is a loose, non-binding hang-guard** (DEADLINE 1200s vs ~250s
  healthy; STALL 180s on no-progress), not a score parameter. Any rep that hits
  it is **censored**: flagged, reported, and excluded from the means. The
  convergence rate is itself a first-class outcome.

## Result (easy, n=3 per arm, score out of 4)

Win config both arms (the measured easy plan win): `preset:easy` + repeat-loops +
turn-cap + outside-workspace + exists, `MELLUM_TURN_CAP=25`,
`MELLUM_DELEGATE_WORKER_DIRECT=1`. Prompt `suites/easy/prompts/01.md`. Run on HEAD
with the fixed `guard/foreground-server` (see below).

| arm | arch req | total req | score | converged |
|-----|----------|-----------|-------|-----------|
| ctrl (arch-direct off) | 11 / 13 / 21 → **15.0** | 44 / 54 / 58 → **52.0** | 4·4·4 | **3/3** |
| adirect (`ARCHITECT_DIRECT=1`) | 11 / 16 / 12 → **13.0** | 44 / 114 / 56 → **71.3** | 4·4·4 | **3/3** |

What it shows:

1. **Architect-direct does not cut the architect's turns on easy.** 13.0 vs 15.0
   means with overlapping ranges, and ctrl's mean is inflated by a single 21-turn
   rep; drop that outlier and ctrl is ~12 against adirect's ~13. A wash. The
   nudge tells the architect to "read each spec file ONCE and write the plan
   directly," but the easy spec is a single phase it barely needs to re-read, so
   there is almost nothing for the nudge to remove.
2. **It raises total cost and variance.** Total requests went 52.0 → 71.3, and
   the spread widened from a tight 44–58 to 44–114 — driven by one adirect rep
   whose **worker** ballooned to 98 requests (ctrl workers were 33–41). Plausible
   mechanism: "write the plan directly, don't re-derive" can hand the worker a
   thinner step doc it then works harder against. One outlier at n=3, but it
   moves the wrong way.
3. **Score is unchanged** — 4/4 across all six reps. The nudge neither helps nor
   hurts correctness on easy.

The observation that motivated the run (the architect "thinks instead of does" —
~1:1 thought-to-action, a paragraph before every tool call, 11–21 turns for 4–5
step docs) is **real**. Architect-direct is simply not its fix on this tier.

## A validated win rode along: the guard fix

Both arms converged **3/3 with zero STALLs**. The prior easy screen (same loose
STALL, pre-fix guard) had a rep stall at 4/4: the `guard/foreground-server` unit
matched a server binary's *name* anywhere on the line, so `pip show uvicorn`,
`python -c "import uvicorn"` and `pip list | grep uvicorn` were all refused as
"you started a server" — nonsense for a pip query — and the worker, unable to
understand the block, churned variants into the deadline. The guard now matches
the **act, not the word**: a binary counts only in command position (segment
start, after a run-wrapper like `uv`/`poetry`/`pdm run`, `nohup`, `env`, or as a
`python -m` module). Real starts still block; naming one in an argument does not.
6/6 clean convergence here is the first evidence the fix holds end to end.

## Decision

- **Architect-direct is not an easy-tier lever** — a measured wash on architect
  turns and net-negative on total cost at n=3. It stays off by default (it
  already is). This is **not** evidence against it on *medium*, where it was
  adopted as part of the win and where a big multi-phase spec gives the re-read /
  re-derive churn something real to cut. The honest next test is the same rig on
  medium: ctrl vs adirect, architect requests as the axis.
- **Requests-as-cost with a loose hang-guard is the measurement rig going
  forward** — not wall-clock deadlines. Censored reps are reported, never
  averaged in.
- The `guard/foreground-server` fix is confirmed by 6/6 convergence; keep it.

## What would falsify this / Risks

- **n=3, one easy prompt, scratch driver** — a screen, not a `run_ladder` rate. A
  preregistered ladder run could move any of these means; the adirect-total
  result leans on a single 114-request outlier.
- **The architect-turn wash may be easy-specific.** If a medium ctrl-vs-adirect
  screen shows adirect clearly below ctrl on architect requests, then the nudge
  works where there is churn to cut and this note's "wash" is just the floor
  effect of a tiny spec — exactly as predicted, not a contradiction.
- **The worker blowup may be noise, not causation.** If repeated medium/easy runs
  never reproduce an adirect worker spike, the "thinner step doc" mechanism is
  unsupported and should be dropped.
- The request count treats every request as equal cost; a request with a larger
  prompt costs more wall. Requests are the reproducible unit, but total wall can
  still diverge from total requests — report both.
