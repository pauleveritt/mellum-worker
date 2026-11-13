# Ablation A12: strip earlier turns' thinking from each request

Date: 2026-10-09. [A3](../ablation-a3-v4b/README.md)'s settings (direct,
greedy, cap 16,384, prompt v5 in replace mode, nudge cap 3 + loop breaker)
plus `ladder/strip-thinking.js`, a `before_provider_request` handler that
removes `reasoning_content` from every assistant message in the outgoing
payload. Motivation: in a late rung 5 request, 70% of the payload was the
model's own earlier thinking replayed to it (`preserve_thinking: true`).

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --strip-thinking --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a12-strip-thinking
```

The strip was effective: 0 assistant messages carrying `reasoning_content`
across all 191 recorded requests (A3: 1,684).

| rung | A3 (thinking replayed) | A12 (stripped) |
| --- | --- | --- |
| 1–3 | 9/9 | 9/9 |
| 4 | 3/3 | 2/3 |
| 5 | 3/3 | 3/3 |

| measure (15 runs) | A3 | A12 |
| --- | --- | --- |
| prefill, k chars per run | 308 | **133** |
| largest single request, k chars | 67 | 31 |
| requests per run, mean / max | 14.3 / 27 | 12.7 / 17 |
| output tokens per run, mean | 5,344 | **9,270** |
| nudges / empty finals | 2 / 0 | 6 / 1 |
| tool errors / anchor failures | 17 / 3 | 13 / 3 |
| wall seconds per run, mean (untrusted) | 54 | **87** |
| wall by rung | 18 / 36 / 21 / 87 / 108 | 15 / 73 / 38 / 124 / 184 |

## Reading

**Reverted. Prefill halved and the run got 60% slower.** Without its
earlier reasoning in context the model re-derives it: output tokens per
run rose 73%, and on rung 5 the wall time went from 108 to 184 seconds.
Empty turns tripled (six nudges in 15 runs, one final still empty, the one
failure). The replayed thinking is the model's working memory across tool
calls, not dead weight.

**Why the saving was illusory.** Prefill on oMLX is 86% cache hits, so the
175k characters removed per run cost little to send; the 4,000 extra
generated tokens per run cost real seconds. For a small model served
locally, generation is the expensive side and context is the cheap side,
as long as the prefix is stable and cached.

**Consequence for the in-session mode and the budget hook.** A filtering
hook must leave `reasoning_content` alone. The remaining lever on thinking
cost would be per-turn: a request-level `thinking_budget`, which Pi never
sends ([A5](../ablation-a5-thinking-medium/README.md)) and which, measured
next, oMLX did not enforce for this model ([A13](../ablation-a13-budget-medium/README.md)).

Raw traces, stdout and diffs: [`ablation-a12-strip-thinking.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a12-strip-thinking.tar.gz).

*2026-10-13: the ladder code this phase used (`strip-thinking.js`, `--strip-thinking`) was removed as rejected; it last exists at commit `44e1b0b`. The launch line above is history.*
