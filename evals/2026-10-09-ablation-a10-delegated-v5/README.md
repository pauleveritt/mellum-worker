# Ablation A10: delegated confirmation of the worker as it ships (prompt v5)

Date: 2026-10-09. [A9](../ablation-a9-delegated-final/README.md) again after
the review pass: prompt v5 (the test-command facts and the missing-files
line, 643 characters), the guard extension at `.pi/mellum/` with the
corrected loop breaker and the stop-reason-gated nudge, the final
frontmatter. This is the file in the repository, unchanged.

```bash
uv run python -m ladder.run_ladder --mode delegated --profile baseline --guards --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/ablation-a10-delegated-v5
```

| rung | 3a (v3, full frontmatter, skill-less) | A9 (v4) | A10 (v5, ships) |
| --- | --- | --- | --- |
| 1 | 3/3 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 | 3/3 |
| 4 | 3/3 | 2/3 | 3/3 |
| 5 | 3/3 | 3/3 | 3/3 |
| total | 15/15 | 14/15 | **15/15** |

| measure (15 runs) | 3a | A10 |
| --- | --- | --- |
| child system prompt, chars | 3,580 | 2,711 (v5 + pi-subagents' intercom block) |
| child tools offered | the seven | the seven |
| runs that delegated / re-dispatched | 15 / 0 | 15 / 0 |
| children that "produced no output" | 3 | 0 |
| child requests per run, mean | 11.0 | 11.1 |
| child tool errors / anchor failures | 2 / 2 | 7 / 1 |
| whole-file writes to existing files / shrinking | 0 / 0 | 2 / 0 |
| `loop_breaker_would_block` | 0 | 0 |
| brief length, mean chars | 1,260 | 1,087 |
| parent ran the tests itself | 15 | 15 |
| wall seconds per run, mean (untrusted) | 62 | 54 |

## Reading

The worker as it ships passes the delegated ladder 15/15 with no
re-dispatch and no empty child turn, at 61% of the original prompt's
length and with the Pi-side configuration that phase 3 started from minus
four frontmatter lines, the skill, and the tool descriptions. The empty
turn did not occur this time; it occurred in 3 of 15 runs in 3a and A9
each, so its absence here is luck at n = 15, not a property of v5. The
recovery for it in delegated mode remains the parent's re-dispatch.

This closes the lean-down: [ablation-summary.md](../ablation-summary.md).

Raw traces, stdout and diffs: [`ablation-a10-delegated-v5.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a10-delegated-v5.tar.gz).
