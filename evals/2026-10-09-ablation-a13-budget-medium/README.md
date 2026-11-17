# Ablation A13: a request-level thinking budget at "medium"

Date: 2026-10-09. [A3](../ablation-a3-v4b/README.md)'s settings plus
`ladder/thinking-budget.js`, a `before_provider_request` handler that maps
Pi's thinking level to oMLX's top-level `thinking_budget` field (medium →
2,048 tokens; the server resolves request value > model setting). This is
the measurement [A5](../ablation-a5-thinking-medium/README.md) could not
be, because Pi sends no thinking control to this provider.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --thinking medium --budget-hook --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a13-budget-medium
```

The hook worked at the wire: every request carried `thinking_budget: 2048`
and the scorer records it in `effective_params`.

| rung | A3 | A13 |
| --- | --- | --- |
| 1–5 | 15/15 | 15/15 |

| measure (15 runs) | A3 (no budget) | A13 (budget 2,048) |
| --- | --- | --- |
| output tokens per run, mean | 5,344 | 4,923 |
| prefill, k chars per run | 308 | 246 |
| requests per run, mean / max | 14.3 / 27 | 13.7 / 20 |
| tool errors / nudges | 17 / 2 | 12 / 2 |
| assistant turns with more than ~2,048 tokens of thinking | 5 of 215 | **4 of 205** |
| longest thinking block, chars | 13,136 | **16,918** |
| forced `</think>` (thinking re-entries) | 0 | 0 |
| wall seconds per run, mean (untrusted) | 54 | 58 |

## Reading

**The server did not enforce the budget.** The same share of turns ran
past 2,048 tokens of thinking as without it, the longest block was longer,
every long block ends in a natural sentence, and no forced close appears.
The 8% fewer output tokens and 20% less prefill are inside the band two
identical runs showed in A5 (27% on output tokens).

**Why, as far as the source says.** oMLX's scheduler attaches the
`ThinkingBudgetProcessor` only when the request needs a `<think>` prefix
or the model's output parser declares a thinking-end text. The model's
admin settings carry no reasoning-parser configuration, so the processor
is never built and the budget, request-level or profile-level, is inert.
That also explains why the "tuned" profile's 4,096-token budget never
fired in 30 runs (phases 1/1d). The scheduler further notes an
intermittent alignment bug that can drop the processor even when it is
built.

**Decision:** the hook stays in the ladder as a flag with this record; it
is correct on the client side and will matter if the model is served
with a reasoning parser that exposes its think-end token. Until then
there is no working per-turn cap on Mellum's thinking through oMLX, and
the earlier finding stands: thinking is best left alone, since removing
it from context (A12) made runs slower.

Raw traces, stdout and diffs: [`ablation-a13-budget-medium.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a13-budget-medium.tar.gz).

*2026-10-13: the ladder code this phase used (`thinking-budget.js`, `--budget-hook`) was removed as rejected; it last exists at commit `44e1b0b`. The launch line above is history.*
