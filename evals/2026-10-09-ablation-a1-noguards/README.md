# Ablation A1: no guards extension

Date: 2026-10-08. [A0](../ablation-a0-replace/README.md) with the guard
extension not loaded: no nudge, no loop breaker. Everything else identical.

```bash
uv run python -m ladder.run_ladder --mode direct --profile tuned --prompt-mode replace --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a1-noguards
```

| rung | A0 (guards) | A1 (no guards) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 2/3 |
| 4 | 3/3 | 3/3 |
| 5 | 3/3 | 2/3 |
| total | 15/15 | 13/15 |

Both failures are the empty turn: rung 3 r2 ends after four requests with
thinking that says "First, edit rows.py" and no tool call; rung 5 r3 after
seventeen with "We'll use edit tool again". Requests, errors, and
whole-file writes all fell (13.1 vs 14.9 requests, 10 vs 17 errors, 4 vs 11
writes), which is what dropping two recoveries looks like, not an
improvement.

**Reverted.** The nudge is load-bearing: it is the only thing in the worker
that answers the empty turn, and the empty turn is the model's one
residual pathology. The dormant guards (new-file-only `write`, step budget)
stay dormant; the extension stays.

Raw traces, stdout and diffs: [`ablation-a1-noguards.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a1-noguards.tar.gz).
