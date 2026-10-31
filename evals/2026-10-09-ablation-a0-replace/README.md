# Ablation A0: the prompt as shipped (v3 alone, replace mode)

Date: 2026-10-08. Phases 0–2 ran direct mode with `--append-system-prompt`,
so the worker prompt sat under Pi's 2,969-character base prompt (4,572
characters together). The shipped agent file uses `systemPromptMode:
replace`, so the subagent sees v3 alone (1,569 characters). A0 measures the
shipped form under the phase 2b reference configuration and is the reference
for every later ablation step.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode direct --guards --profile tuned --prompt-mode replace --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a0-replace
```

## Result

| rung | 2b (append) | A0 (replace) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 3/3 | 3/3 |
| 5 | 3/3 | 3/3 |

| measure (15 runs) | 2b | A0 |
| --- | --- | --- |
| system prompt, chars | 4,572 | 1,569 |
| requests per run, mean / max | 16.5 / 36 | 14.9 / 34 |
| tool errors | 26 | 17 |
| nudges | 7 | 1 |
| whole-file `write` to an existing file / shrinking it | 2 / 0 | 11 / 0 |
| empty final | 0 | 0 |
| wall seconds per run, mean (untrusted) | 62 | 58 |

## Reading

**Holds.** 15/15 with fewer requests, fewer tool errors, and one nudge
instead of seven. The Pi base prompt was not load-bearing for the worker;
the agent file's `replace` was the right call, and the ladder now measures
what ships.

**One column moved: whole-file writes to existing files, 2 → 11.** Pi's
base prompt tells the model to prefer `edit`; without it, v3's own fact
("`write` … on an existing file replaces the entire content, so the content
must be the whole file") is what governs, and the model took it as
permission: all three rung 2 repeats rewrote `ledger.py` and
`test_ledger.py` whole, and rung 5 r3 rewrote four files. No write shrank a
file and every run passed, so this is the recorded `../local-ai-pi` risk,
not a failure. The dormant new-file-only `write` guard is the remedy if it
ever shrinks; the prompt steps (A2–A4) will show whether the tool facts
drive it.

**Decision:** `replace` stays. Reference for A1–A5 is this run.

Raw traces, stdout and diffs: [`ablation-a0-replace.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a0-replace.tar.gz).
