# Ablation A2: prompt v4a — no procedure block

Date: 2026-10-08. [A0](../ablation-a0-replace/README.md) with
`prompts/ablation/v4a-no-procedure.md`: v3's six-step procedure removed,
its one fact ("if it fails, read the failure, change the code, and run it
again") moved under the test-command facts. 1,134 characters instead of
1,569.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --prompt prompts/ablation/v4a-no-procedure.md --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a2-v4a
```

| rung | A0 (v3) | A2 (v4a) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 3/3 | 3/3 |
| 5 | 3/3 | 3/3 |

| measure (15 runs) | A0 | A2 |
| --- | --- | --- |
| requests per run, mean / max | 14.9 / 34 | 12.3 / 19 |
| tool errors / anchor failures | 17 / 6 | 11 / 0 |
| nudges | 1 | 0 |
| whole-file writes to existing files | 11 | 6 |
| wall seconds per run, mean (untrusted) | 58 | 45 |

**Holds, and is the cleanest 15-run phase of the night**: fewest requests,
no anchor failure, no nudge needed. The procedure block was not
load-bearing; "restate the task", "grep for identifiers", "smallest
change" and "reply with files changed and test output" were rules of
conduct the model did not need. **Kept: v4a becomes the worker prompt
(`prompts/mellum-worker.md`, v4).**

Raw traces, stdout and diffs: [`ablation-a2-v4a.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a2-v4a.tar.gz).
