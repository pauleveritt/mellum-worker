# Ablation A3: prompt v4b — no tool descriptions

Date: 2026-10-08. [A2](../ablation-a2-v4a/README.md) with
`prompts/ablation/v4b-no-procedure-no-tools.md`: the five "tools, stated
exactly" lines removed as well, on the argument that Pi's tool schemas
already say what each tool does. 643 characters.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --prompt prompts/ablation/v4b-no-procedure-no-tools.md --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a3-v4b
```

| rung | A2 (v4a) | A3 (v4b) |
| --- | --- | --- |
| 1–5 | 15/15 | 15/15 |

| measure (15 runs) | A2 | A3 |
| --- | --- | --- |
| requests per run, mean / max | 12.3 / 19 | 14.3 / 27 |
| tool errors / anchor failures | 11 / 0 | 17 / 3 |
| nudges | 0 | 2 |
| `loop_breaker_would_block` | 0 | **2** (rung 4 r2: `export.py` read seven times in a window of twenty) |

Passes hold. At the time, the `loop_breaker_would_block` column went
0 → 2 (rung 4 r2 re-read `export.py` seven times, twice after editing it),
and the step was reverted under the rule. The whole-branch review then
found the breaker counted re-reads after an edit as repeats, which is not a
loop; corrected (repeats forgotten after any edit, write, or bash call) and
replayed over all runs, the column is zero everywhere, including here. The
remaining movements (nudges 0 → 2, anchor failures 0 → 3) are inside the
floor A5 measured between identical runs.

**Kept, after the correction: v4b became prompt v5, confirmed delegated in
A10.** The tool facts were not load-bearing; Pi's tool schemas carry them.

Raw traces, stdout and diffs: [`ablation-a3-v4b.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a3-v4b.tar.gz).
