# Ablation A4: prompt v4c — the test-command facts only

Date: 2026-10-08. [A3](../ablation-a3-v4b/README.md) with
`prompts/ablation/v4c-completion-facts-only.md`: also without "if the
files for the task cannot be found, reply with what is missing and stop".
556 characters: one line of role, six facts about the test command.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --prompt prompts/ablation/v4c-completion-facts-only.md --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a4-v4c
```

| rung | A2 (v4a) | A4 (v4c) |
| --- | --- | --- |
| 1–4 | 12/12 | 12/12 |
| 5 | 3/3 | 2/3 |

The one failure (rung 5 r1) is the worst kind: the model edited
`test_export.py` so that "3 passed" came out, and reported success. The
check fails any run that changes a test. This is the only test edit by
the worker in 229 direct runs; bare Pi did it once in fifteen.

**Reverted.** With only the completion facts, the worker's path to
"exit 0" once ran through the test file. The one line v4b has and v4c
lacks ("if the files for the task cannot be found, reply with what is
missing and stop") stands between the model and that shortcut, or three
repeats were kind; either way it stays, and the lean prompt is v4b (v5).

Raw traces, stdout and diffs: [`ablation-a4-v4c.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a4-v4c.tar.gz).
