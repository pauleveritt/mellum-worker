# data_sft_v2: tool-calling examples for DeepSeek-R1-Distill-Qwen-1.5B, both thinking modes

Built 2026-11-28 by `r1d/build_sft_v2.sh` (the exact command). Sources and teacher: `r1d/DISTILL.md`.

- **Source:** teacher batch `runs/2026-11-28-teacher-v2`: Mellum 2.1 on the lab (vLLM), in the student's harness
  shape (`preset:baseline-worker,context/trim-tool-output,context/narrow-tools,prompt/think-briefly`), over 24
  `tools-train`, 12 `py-features-train` and 6 Satyrn training tasks, 3 repeats each. Nothing from the AgentClinic
  family or the Python eval tasks (refused by name in the builder).
- **What a row is:** one teacher step whose own call succeeded, from any run (passing or not, ADR 0010; `passed`
  says whether its phase passed), rendered with `r1d/deepseek_tools.jinja`, once per thinking mode (`mode`):
  - `on`: prompt ends `<｜Assistant｜><｜think▁on｜><think>\n`; completion = the teacher's thinking, `</think>`,
    then its text and calls;
  - `off`: prompt ends `<｜Assistant｜><｜think▁off｜><think>\n\n</think>\n\n`; completion = the same text and calls.
  History never carries thinking (the template drops it). Tool results are exactly as the harness recorded them
  (already trimmed by `context/trim-tool-output`, the same shape the student is served with; no extra cut).
- **Filters:** a step whose own call failed (non-bash error or a malformed shell command) is skipped; examples
  over 24,576 tokens dropped; validation is every 10th run, held out whole.

Build output:

    examples: {'failed-step-skipped': 233, 'ok': 5838, 'misaligned': 3}
    train 5104 examples, 26742975 tokens
    valid 734 examples, 4899520 tokens

Train: 2,552 steps x 2 modes; median 4,304 tokens (on) / 3,856 (off); 4,882 rows end in a tool call; 56% from
phases that passed. Sources: 2,840 tools-train, 1,474 py-features-train, 790 Satyrn.
