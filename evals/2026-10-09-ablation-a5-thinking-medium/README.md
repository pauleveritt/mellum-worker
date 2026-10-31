# Ablation A5: thinking medium — which turned out to be a repeat of A2

Date: 2026-10-09. [A2](../ablation-a2-v4a/README.md) with `--thinking medium`
instead of `high`.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --prompt prompts/ablation/v4a-no-procedure.md --thinking medium --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a5-thinking-medium
```

## The thinking level never reaches the server

The first request of A2 and A5, everything except messages and tools:

```
{'model': 'Mellum2.1-12B-A2.5B-Thinking-6bit', 'stream': True, 'max_tokens': 16384,
 'chat_template_kwargs': {'enable_thinking': True, 'preserve_thinking': True},
 'temperature': 0, 'top_p': 1, 'top_k': 0, 'min_p': 0, 'seed': 42, 'presence_penalty': 0.5}
```

Identical. Pi's thinking level for an `openai-completions` provider maps to
a reasoning-effort field this provider does not carry, and oMLX forces
`enable_thinking` on in any case. So `thinking: high` in the agent file and
`--thinking` on the command line are inert for Mellum on oMLX, and A5 is
A2 run a second time under identical settings.

## Result, read as a variance measurement

| measure (15 runs) | A2 | A5 (same settings) |
| --- | --- | --- |
| passes | 15/15 | 15/15 |
| requests per run, mean / max | 12.3 / 19 | 15.9 / 39 |
| tool errors / anchor failures | 11 / 0 | 21 / 9 |
| nudges | 0 | 5 |
| `loop_breaker_would_block` | 0 | 0 |
| whole-file writes to existing files | 6 | 3 |
| output tokens per run, mean | 4,433 | 5,627 |
| wall seconds per run, mean (untrusted) | 45 | 56 |

**This is the noise floor.** Greedy decoding with a fixed seed on this
server is not reproducible (phase 1d), and two runs of the same
configuration differ by 3.6 requests per run, nine anchor failures, and
five nudges, while the pass count does not move. Three repeats per rung
are a gate on passes; the secondary columns are not stable enough at this
sample size to rank configurations that all pass.

**Consequences for the earlier steps.** A3 was reverted because its
`loop_breaker_would_block` went 0 → 2; its other movements (nudges 2,
anchors 3) are inside this floor. The loop-breaker column stayed zero in
both A2 and A5, so that one signal stands, at n = 1. A1's reversion rests
on passes (13/15, two empty turns) and stands. A4's rests on a test edit,
which is a kind, not a count, and stands.

**Decision:** `--thinking low` is not run; it would be a third repeat.
The `thinking: high` line in the agent file is inert and is removed
(A6, continued).

Raw traces, stdout and diffs: [`ablation-a5-thinking-medium.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a5-thinking-medium.tar.gz).
