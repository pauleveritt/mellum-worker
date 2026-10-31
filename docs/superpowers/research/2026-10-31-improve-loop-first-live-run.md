# The improvement loop's first live run — it runs, but carries nothing yet (2026-10-31)

## What is measured / What is conjecture

**Measured.** `learn/code/improve.py` on the local M3 (Metal, cached Q4), suite `easy`, 5
iterations, shipped worker (`--arm worker`, facts on), each rep's lessons distilled into the
carried `## Mellum` section for the next rep. Recorded on the scoreboard as `arm:worker`.

| iter | result | turns | wall | why it failed |
|---|---|---|---|---|
| 1 | FAIL | 25 | 104 s | home miss (`miss=4`) |
| 2 | PASS | 42 | 208 s | — |
| 3 | FAIL | 49 | 165 s | `miss=0`, but wrote `check_jinja.py` and `test_home.py` outside the layout |
| 4 | FAIL | 29 | 119 s | home miss (`miss=4`) |
| 5 | FAIL | 42 | 234 s | `miss=0`, but left the workspace contaminated |

1/5. **The loop ran end-to-end and recorded every rep — the plumbing works live, not just in
`--dry-run`.** But it improved nothing: the distiller printed *"nothing new to carry forward"*
on all five iterations, the carried `## Mellum` never grew past the suite's own base facts, and
the turn-count stayed flat and noisy (25, 42, 49, 29, 42) with no downward trend.

**Why it carried nothing (measured — corrected).** The first reading of this run blamed
`mellum-learn`'s pattern vocabulary; that was wrong. The real cause is upstream: the loop's
records file was **empty** — zero records across all five reps. The shipped worker writes its
mode record only inside a clean mode-off *deactivation* (`mellum-worker.ts` `writeRunRecord`,
called when the worker turns off), and the harness `--arm worker` run exits without that
transition, so no record is ever appended to `MELLUM_MODE_RUNS`. `mellum-learn` therefore had
**no input**, not a vocabulary mismatch. Each rep started from the same base facts as the last;
the loop was, in effect, five independent runs.

So the distiller fed from the mode-record channel cannot work in the harness. The reliable
per-rep artifact the harness always writes is `run.json`, and it carries exactly the verdicts
these runs failed on — `out_of_layout` (iter 3: `check_jinja.py`, `test_home.py`, pathology #10)
and `contaminated` (iter 5, pathology #4). The fix is to distil the carried facts from those
verdicts, not from the empty mode-record file.

**Conjecture.** That extending `mellum-learn` to the failures the worker actually hits on easy —
a bullet when a run writes outside `app.py`/`models.py`/`templates/`/`tests/`, and when it edits
or adds a test (contamination) — would give the carry something to teach, and only then could
the loop show whether carrying it forward pulls the turn-count down. Until that lands, the loop
is a correctly-wired mechanism with nothing to say.

## Second live run — the extended distiller (added 2026-10-31)

With the distiller now learning from `run.json` verdicts, the loop was re-run on easy, same
arm, 5 iterations:

| iter | result | turns | wall | failure | carried after |
|---|---|---|---|---|---|
| 1 | PASS | 39 | 177 s | — | — |
| 2 | FAIL | 30 | 212 s | `contaminated` + home miss | **"Do not: add, edit or delete tests"** |
| 3 | FAIL | 28 | 102 s | home miss | — |
| 4 | FAIL | 46 | 176 s | home miss | — |
| 5 | PASS | 40 | 241 s | — | — |

2/5 (vs 1/5 before), `arm:worker` now 3/10 cumulative on the board. **The carry grew for the
first time**: iter 2 was contaminated, the distiller folded "do not edit tests" into the facts,
and **contamination did not recur** — iters 3–5 were all `contaminated=False`. That is weak
(n=1) but real evidence the carried fact landed and stopped a repeat mistake.

**But it did not lift the pass rate, and the reason is the point.** The failures that remained
(iters 3, 4) are **home-misses** — the worker did not build the home page — and a home-miss is
not a carryable "do not" rule; it is "build the thing". No fact teaches it. The config that
*does* fix a home-miss on easy is `acceptance · ncm · nonblock` (6/6, 17 turns), and it fixes it
not with a reminder but with the **gate that re-runs the contract and redispatches** the miss.
The plain-worker loop, however much it carries, cannot reach that — a fact reminds, a gate
enforces (pathology #14).

**Decision.** The distiller extension is sound and the mechanism now carries real lessons from
the channel the harness writes. Its ceiling on the plain worker is the home-miss, which only the
acceptance gate closes. The next step to make the loop *improve* is to carry the remedy that
enforces — run it on the winning stack, so the gate handles the home-miss and the carried facts
handle the one-off slips (contamination) on top. Carrying advice helps at the margin; carrying
the gate is what moves the rate.

## Third live run — on the winning stack (added 2026-10-31)

The fair test: carry on top of the gate. Run the loop with `--arm worker` (the only arm that
injects the carried facts) plus the easy record stack — `nonblock + acceptance + ncm` — 5
iterations on easy.

| iter | result | turns | wall | miss |
|---|---|---|---|---|
| 1 | FAIL | 17 | 99 s | 4 |
| 2 | FAIL | 40 | 117 s | 4 |
| 3 | PASS | 30 | 143 s | 0 |
| 4 | PASS | 50 | 196 s | 0 |
| 5 | PASS | 43 | 214 s | 0 |

3/5, recorded as `arm:worker · acceptance · ncm · nonblock`. Two findings, both against the
carry hypothesis:

- **The carry was inert.** The distiller said "nothing new to carry forward" on all five reps —
  no rep hit a carryable failure (no `out_of_layout`, no `contaminated`), so there was nothing
  to carry. The fail→pass pattern (iters 1–2 fail, 3–5 pass) is run-to-run variance of the
  gate, not learning: the carried facts never changed between reps.
- **Forcing the facts channel degrades the gate.** The stack scores **6/6** on `--arm bare`
  but only **3/5** here on `--arm worker`. The gate fired (iter 1's trace shows ~5 `mellum-ncm`
  redispatches, the `NCM_MAX` ceiling) yet the worker still settled at `miss=4` — on the worker
  arm it could not build the home page even across five redispatches, where the bare worker
  could. The carry channel (worker/facts) and the best gate performance (bare) are in tension.

**Decision — the improvement loop does not improve easy.** It is a correctly-wired, recorded
mechanism, and it *can* carry a lesson that sticks (the contamination fact in the second run).
But on easy it has little to carry (the dominant failure, the home-miss, is not a carryable
"do not" rule), and the one arm that reads the carry is a worse worker than bare. The lever on
easy is the gate, run bare (`acceptance · ncm · nonblock`, 6/6) — not carried facts. Keep the
loop as a tool; do not adopt it as an easy remedy. Where it would earn its place: a task on
which the worker *repeats* a carryable mistake, or a loop that carries the *remedy to add*
(a guard) rather than a reminder — the pathology-#14 reading, still unmeasured.

## What would falsify this / Risks

- **A richer distiller still does not help.** A carried fact is a reminder, not an enforcement
  (pathology #14: a rule in every request was ignored at n=3). The worker may read "do not write
  outside the layout" and do it anyway, in which case the fix is a **guard**
  (`guard/stay-in-workspace`), not a fact — and the loop should carry *which remedy to add*, not
  advice.
- **Small, noisy n.** Five reps; the two `miss=0` failures (layout, contamination) may be the
  flaky quality trips that `+ quality` already addresses on easy, not a stable signal.
- **Wrong arm for the question.** This ran the bare shipped worker, which is 1/5 on easy anyway;
  the easy *record* is `acceptance · ncm · nonblock` at 6/6, 17 turns. Carrying learnings on top
  of the winning stack (not the plain worker) is the fairer test of whether the loop adds
  anything the stack does not already get.
