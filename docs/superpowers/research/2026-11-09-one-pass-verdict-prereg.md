# Preregistration — the one-pass exit-gate vs the architect loop, on the real ladder

**Written before the run.** The [one-pass note](2026-11-08-one-pass-vs-architect-loop.md)
is a stack of scratch screens: one agent in a single pass, an external held-out
acceptance test re-dispatched at settle, and a live-server guard, together reach
18/18 on medium where the architect-split plan loop ran 300+ requests. The skill
is explicit — a screen is a lead; a comparative claim is decided by a
preregistered run through the real harness (`ladder/`), not a scratch driver.
This fixes the arms, n, scoring and rule before that run.

## What is measured

Whether **one agent in a single pass, gated by a held-out acceptance test**
(Arm A) beats the **architect-split plan loop** (Arm B) on the medium four-phase
rung, on the hidden oracle's score and on request cost — run through
`run_ladder`, the shipped path, not a script.

## Arms

Both run `--rung 13` (`agentclinic-plan`: implement all four phases from `specs/`),
scored by the rung's own hidden oracle `check_agentclinic(4)` (/18), on the
llama-server backend serving `Mellum2.1-12B-A2.5B-Thinking` (Q4) at
`127.0.0.1:8001`. Nothing about either arm is tuned to the oracle.

- **Arm A — one pass + held-out exit-gate + live-server guard.** `--mode direct`
  (a single worker on the whole spec, no architect, no split), the shipped worker
  prompt and guard set (`--guards`), plus two extensions loaded with
  `--pi-extension` so they are measured without shipping: `mellum-verify` (the gate
  — at settle it re-runs the held-out `test_medium.py`, which is **not** placed in
  the workspace, and while red re-dispatches the failing test names, up to
  `VERIFY_MAX=5`) and `guard/no-live-server` (refuse the server-start + curl
  spiral). The task stays the four-phase spec; the test is held out via the gate's
  `PYTHONPATH=cwd`, so the worker cannot see or weaken it.
- **Arm B — the architect-split plan loop.** `--mode plan` (the `/mellum`
  architect splits the spec into step docs, a fresh worker builds each), at the
  model's shipped sampling, as the ladder already runs it. No acceptance test, no
  gate — the plan loop's own structure against the same hidden oracle.

**What this is not.** Arm A is the shipped prompt + guard set + the two
extensions, not the scratch stack (which also carried `name-the-layout`,
`python-developer`, `verify-the-spec`, `exists`, and a hand-written single-pass
preamble). The verdict measures the path that could actually ship, not the
exploratory scaffolding. Adding those remedies back is a later arm, not this one.

## n, scoring, cost

- **n = 3** repeats per arm (6 runs). A first decisive pass: the screened effect
  is large on both axes, so n=3 separates it; if the score bands overlap, n grows
  before any claim.
- **Score:** `check_agentclinic(4)` /18, the hidden oracle, recorded per run in
  the arm's `table.md` / `run.json`. Primary.
- **Cost:** total model requests — Arm A from the run's trace, Arm B from the
  delegate profile (architect + worker + total). The screened gap is ~80–100 vs
  300+.
- **Guard:** `--deadline 2400` (Arm A) / `3000` (Arm B) is a loose hang-guard, not
  a budget; a run that hits it is censored, not scored. Wall is informational.

## The rule (decided before the run)

- **Arm A wins the cost axis** if its mean total requests is below Arm B's with no
  overlap across the three reps. The screen says ~a third or less; the rule asks
  only for a clean, non-overlapping gap.
- **Arm A holds the score** if its median is at or above Arm B's on the /18 oracle
  — the cheaper arm must not buy its saving with a worse build. A full 18/18 is not
  required for the verdict; not losing ground is.
- **A censored (deadline) rep is replaced, not scored**, up to two replacements per
  arm; past that the arm is reported as not converging, which is itself a result.
- **This decides a lead, not a default.** A win here promotes "one pass + held-out
  gate beats the plan loop on medium" from screen to a recorded ladder result; it
  does not retire the plan loop, whose case is the spec too large for one context —
  a rung past four phases this run does not reach.

## The exact invocations

Arm A (one pass + held-out gate + guard):

```
VERIFY_TEST=$REPO/ladder/fixtures/acceptance/test_medium.py VERIFY_MAX=5 \
uv run python -m ladder.run_ladder --mode direct --rung 13 --repeat 3 \
  --guards --deadline 2400 \
  --pi-extension $REPO/extensions/mellum-verify.ts \
  --pi-extension $REPO/remedies/guard/no-live-server.ts \
  --provider llamacpp --base-url http://127.0.0.1:8001/v1 \
  --model llamacpp/Mellum2.1-12B-A2.5B-Thinking --profile tuned \
  --out runs/2026-11-09-one-pass-verdict/A-direct-gate
```

Arm B (architect-split plan loop):

```
uv run python -m ladder.run_ladder --mode plan --rung 13 --repeat 3 \
  --deadline 3000 \
  --provider llamacpp --base-url http://127.0.0.1:8001/v1 \
  --model llamacpp/Mellum2.1-12B-A2.5B-Thinking --profile tuned \
  --out runs/2026-11-09-one-pass-verdict/B-plan
```

`ladder/scripts/watch_ladder.py` follows each run's newest `trace.jsonl` on
screen. Raw `trace.jsonl` / `stdout.txt` / `diff.patch` are stripped before any
record lands in `docs/ladder/`; the result updates
[the one-pass note](2026-11-08-one-pass-vs-architect-loop.md).
