# Phase 1c: baseline profile, greedy, request parameters in effect

Date: 2026-10-08. Paired with phase 1d; the joint record, result tables and
reading are in [phase1d-tuned-effective/README.md](../phase1d-tuned-effective/README.md).

Result: 13/15. One `length` stop (rung 4 r1: 4,096 output tokens of
thinking), one honest failure (rung 5 r3, "tests still failing"), two nudges
fired and both recovered with the tests going green afterwards.

```bash
uv run python -m ladder.run_ladder --mode direct --guards --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase1c-baseline-greedy
```

Raw traces, stdout and diffs: [`phase1c-baseline-greedy.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase1c-baseline-greedy.tar.gz).
