# Preregistration: the empty-final nudge on llama.cpp, easy then medium

Date: 2026-10-24, written before the run. The first arm of the Lessons re-base:
the track's evidence moves to the backend Getting Started teaches, and the
oMLX citations are retired from the pages, not from `evals/`.

**What is measured.** The shipped worker against itself with the nudge turned
off, on the suites the Getting Started track teaches. Not a comparison with
oMLX: those numbers stay in `evals/` as their own backend's record and
are no longer cited by a lesson.

- Backend: `llama-server` 0.7.0 (build 11669), Mellum 2.1 `Q4_K_M`,
  `-c 50000`, `127.0.0.1:8002`, started by `uv run scripts/backend.py start`.
- Sampling: the learner's profile, `learn/code/profile` — `temperature 1`,
  `top_p 0.95`, `top_k 20`, `max_tokens 16384`, context 50,000. Not the
  ladder's greedy block: this arm measures the path the learner runs.
- Runner: `learn/code/harness.py run --suite <suite> --repeat 5 --arm <arm>
  --grade`.
- Arms, and only one column between them:
  - `worker`: prompt v5, Pi's seven tools, nudge capped at 3, loop breaker on.
  - `no-nudge`: the same, with `MELLUM_GUARDS='{"loopBreaker":true}'`.
- n: 5 sessions per arm per suite. Easy is one prompt, so its five sessions
  are one task five times; medium is four prompts, so twenty sessions.

**Staircase.** Easy first, both arms. Medium only if the `worker` arm passes a
majority of easy (3 of 5). Hard only if `worker` passes a majority of medium.
Hard is additionally skipped when medium shows no headroom, because the
45-session record has hard at 0/9 for every arm: a suite nothing passes
cannot separate two arms.

**Reading.** Per arm and suite: passes out of n; then the nudge fires, taken
per run from the worker's own record (`worker-runs.jsonl`, field `nudges`),
the mean requests, the tool errors and the wall. The fire count is the
reading that distinguishes "the guard was needed" from "the guard had
nothing to do", so an arm table without it is void, not merely thinner.

**Decision rules, fixed now.**

1. `no-nudge` at least matches `worker`, and `no-nudge` records no empty
   final: the nudge is not load-bearing on llama.cpp easy. Recorded as
   neutral, and the guard is **not** removed — a guard change needs a
   re-baseline, and this arm does not ask for one.
2. `worker` beats `no-nudge`, and the extra passes are runs where the fire
   count is above zero: the nudge is load-bearing here. Recorded with the
   fire count beside the passes.
3. `worker` fires and the run still fails: recorded as the case the lesson
   has to name — a guard answering an empty turn does not tell us the model
   knows when it is done.
4. A failure whose final turn carries `stop` other than `stop` (for example
   `length`) is reported as a separate pathology. The guard requires `stop`,
   so those are **not** nudge misses and must not be counted as such.

**What is conjecture.** That one suite at n = 5 settles a direction. Easy is
a single prompt; a 3/5 against 5/5 there is one task, not a rate. The arm's
purpose is to decide whether the lesson may speak about llama.cpp at all, and
in which words, not to publish a percentage.

**What would falsify this.** A run whose environment shows a different arm
(any `MELLUM_GUARDS` value other than the arm's), a run whose fire count
cannot be read from the worker record, a run under a different Pi version
than the one recorded here, or a contaminated workspace. Any of these makes
that session invalid; it is excluded and named.

**Risks.** The checkout's Pi is 1.1.0 and the 45-session record does not name
its version, so the two are comparable only if the harness path is unchanged;
the record says so rather than implying comparability. llama.cpp may surface
the empty turn differently from oMLX — the reference run's one failure was
`length`, not an empty `stop` — and if easy records no empty finals in either
arm, the nudge's transfer question stays open at this n and moves to medium.

**Raw evidence.** `trace.jsonl`, `stdout.txt` and `diff.patch` per run go to a
`research-2026-10-24` release after review, never into git.
