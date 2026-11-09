# Preregistration — the one-pass exit-gate vs the architect loop, on the real ladder

**Written before the run.** The [one-pass note](2026-11-08-one-pass-vs-architect-loop.md)
is a stack of scratch screens: one agent in a single pass, an external held-out
acceptance test re-dispatched at settle, and a live-server guard, together reach
18/18 on medium where the architect-split plan loop ran 300+ requests. The skill
is explicit — a screen is a lead; a comparative claim is decided by a
preregistered run through the real harness (`ladder/`), not a scratch driver.
This fixes the arms, n, scoring and rule before that run.

## Correction (2026-11-09) — the faithful arm, after two config missteps

The first draft of Arm A below was wrong twice, both caught on a single smoke rep
before any verdict rep was scored. Recorded here, not deleted, per the SDD rule.

1. **Stripped too much.** The first draft ran the shipped prompt at
   `--thinking high` with the scratch's prompt-remedies removed as "scaffolding".
   Rep 1 FAILed: the worker over-reasoned and its final turn truncated
   (`stop_reason=length`) at 91 requests, even though the held-out gate fired 9
   times. Reduced thinking and those remedies are a **measured lever**, not
   scaffolding — the 18/18 depended on them.
2. **The held-out gate fought the shipped prompt.** The second draft added back
   reduced thinking and the remedies but kept the test *held out* (via
   `mellum-verify`, no visible test). The shipped worker prompt (v11) says "you
   make one failing test pass — read the failing test"; with the test held out,
   `tests/` is empty, so the worker stopped early without building `models.py`
   and the gate errored importing it (`No module named 'models'`).

**The corrected Arm A uses the ladder's native exit-gate**, which is the
canonical M.11 form and matches the shipped prompt: `--acceptance-test
test_medium.py` places the complete test *visibly* in the workspace baseline and
the `existing_tests_kept` scorer **freezes** it (the worker cannot weaken it —
unweakenable), the task becomes "make `tests/test_medium.py` pass", and
`--redispatch 5` re-runs the frozen test and re-hands each failure to a fresh
worker on the same workspace (the gate). Reduced thinking (`--thinking low`) and
the measured remedies (`no-live-server`, `name-the-layout`, `python-developer`,
`verify-the-spec`, `exists`) ride along. Validated by one smoke rep: **PASS at 90
requests, `stop=stop` (clean exit)**. This replaces the held-out `mellum-verify`
wiring in the Arm A invocation below; everything else (n, rung, Arm B, cost) holds.

**Scoring note.** The ladder's `result` is PASS/FAIL on the hidden oracle (all
four phases), not a /18. The rule below reads on the **PASS-rate** across the
three reps, not a median /18.

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

Arm A (one pass + native frozen exit-gate + reduced thinking + measured remedies),
as corrected above:

```
uv run python -m ladder.run_ladder --mode direct --rung 13 --repeat 3 \
  --acceptance-test $REPO/ladder/fixtures/acceptance/test_medium.py --redispatch 5 \
  --guards --thinking low --deadline 2400 \
  --pi-extension $REPO/remedies/guard/no-live-server.ts \
  --pi-extension $REPO/remedies/prompt/name-the-layout.ts \
  --pi-extension $REPO/remedies/prompt/python-developer.ts \
  --pi-extension $REPO/remedies/prompt/verify-the-spec.ts \
  --pi-extension $REPO/remedies/guard/exists.ts \
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
