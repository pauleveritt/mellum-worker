# Reference run: llama.cpp, rungs 1–5

Preregistered in [the llama.cpp reference preregistration](../../superpowers/research/2026-10-20-llamacpp-reference-preregistration.md),
which fixed the arms, n, reading and decision rule before the run.

**What is measured.** The shipped worker, direct mode, profile `baseline`,
against llama.cpp on this machine: `llama-server` version: 0.7.0 (build 11669, commit 620d2225c),
Mellum 2.1 `Q4_K_M` at `-c 50000` on `127.0.0.1:8002`, worker
`0.1.8` (`v0.1.8-62-g16072e9`), prompt
`v5`, thinking `high`. Every
run's first request carried the greedy block (`temperature 0`, `top_p 1`,
`top_k 0`, `min_p 0`, `seed 42`, `max_tokens 4096`), checked in all 15 traces.
Not a comparison with oMLX: a different backend's numbers do not transfer.

Launch, from `ladder/`:

    uv run python -m ladder.run_ladder --mode direct --profile baseline --thinking high --prompt-mode replace --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --provider llamacpp --base-url http://127.0.0.1:8002/v1 --model llamacpp/Mellum2.1-12B-A2.5B-Thinking --context-window 50000 --out ../evals/baseline/2026-10-20-reference-llamacpp-rungs1-5

The first invocation was interrupted after rung 5 repeat 2 by the agent's
tool timeout, not by the ladder; the missing repeat was then run alone with
the same flags into a scratch directory and its `rung5-baseline-direct-r3`
was added here. Same arms, same n; nothing was changed after seeing results.

| rung | repeat | result | requests | tool errors | stop | wall s (untrusted) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | pass | 8 | 0 | stop | 7.3 |
| 1 | 2 | pass | 8 | 0 | stop | 11.4 |
| 1 | 3 | pass | 7 | 0 | stop | 8.7 |
| 2 | 1 | pass | 15 | 0 | stop | 29.9 |
| 2 | 2 | pass | 15 | 0 | stop | 30.4 |
| 2 | 3 | pass | 10 | 0 | stop | 35.0 |
| 3 | 1 | pass | 11 | 0 | stop | 18.3 |
| 3 | 2 | pass | 14 | 0 | stop | 18.2 |
| 3 | 3 | pass | 13 | 0 | stop | 16.6 |
| 4 | 1 | pass | 21 | 1 | stop | 81.7 |
| 4 | 2 | pass | 16 | 2 | stop | 79.4 |
| 4 | 3 | FAIL | 8 | 1 | length | 47.8 |
| 5 | 1 | pass | 18 | 2 | stop | 91.2 |
| 5 | 2 | pass | 25 | 4 | stop | 109.7 |
| 5 | 3 | pass | 16 | 2 | stop | 78.6 |

**Reading.** Rung 1: 3/3. Rung 2: 3/3. Rung 3: 3/3. Rung 4: 2/3. Rung 5:
3/3. Total: 14/15. The one failure is rung 4, repeat 3: the run stopped on
`length` after 8 requests and 1 tool error with an empty final reply — the
worker spent its `max_tokens` without answering. It is reported as it
happened, not explained away.

**What this cannot claim.** Nothing about oMLX, nothing about a 16 GB
machine, and little about capability: rungs 1–5 are small, so 14/15 says the
backend path works and the ladder can see it. Rungs 6–9 have not been run on
llama.cpp. The record is what a lesson cites as `reference-run`.

**Raw evidence.** `trace.jsonl`, `stdout.txt` and `diff.patch` for the 15
runs are **owed** as `reference-llamacpp-rungs1-5.tar.gz` on the
`research-2026-10-20` release; its SHA-256 goes here when published. They
are not in git.
