# data_sft_v1: supervised tool-calling examples for DeepSeek-R1-Distill-Qwen-1.5B

Built 2026-11-28 by `r1d/build_sft_v1.sh` (the exact command), which runs `r1d/build_sft.py`.

- **What a row is:** one assistant step from a phase that passed its hidden tests in a recorded Mellum 2.1 run
  (base and its tunes). `prompt` is the conversation up to that step, rendered with `r1d/deepseek_tools.jinja`
  and ending in `<｜Assistant｜><think>\n`; `completion` is the step's thinking, `</think>`, its text and its tool
  calls in DeepSeek's markers (the tokens `r1d/add_tokens.py` adds). Train on the completion only.
- **Sources:** the 92 run folders in `sources_base_runs.txt` (as for `data_dpo_raw_v4`), plus
  `2026-11-26-ours-mix120-medium`, `2026-11-26-tools-medium`, `2026-11-27-tools15-medium`,
  `2026-11-27-tools15-medium2`, `2026-11-27-tools2-medium`; all phases of `2026-11-24-mint-satyrn` and the two
  `pyfeat-train` folders.
- **Filters:** phase 1 never enters (the Easy screen is phase 1); contaminated runs out unless the trace never
  shows the grader canary; a phase counts as passed by its own replayed grade where one exists, and fails if it
  broke an earlier phase; a step whose own call failed (non-bash error, or a malformed shell command) is
  skipped; tool results capped at 400 head + 200 tail characters; examples over 24,576 tokens dropped.
- **Validation:** every 10th run, held out whole.

Build output:

    examples: {'contaminated-no-trace-or-grade': 120, 'failed-step-skipped': 183, 'ok': 3577, 'misaligned': 9}
    train 3208 examples, 25353853 tokens
    valid 369 examples, 2504362 tokens

Train set: median 7,619 tokens, 90th percentile 12,181, longest 19,577; 3,058 rows end in a tool call, 150 in
a final answer; 2,865 come from the medium suite.
