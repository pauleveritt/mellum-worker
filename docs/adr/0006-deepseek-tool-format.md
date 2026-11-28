# 0006: The 1.5B learns DeepSeek's tool markers, not Qwen's `<tool_call>`

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

The distill's vocabulary already has `<tool_call>` and `</tool_call>` as single tokens (from Qwen2.5), so the
cheapest path was Qwen/Hermes calls (`learn/finetune/r1d/toolcall.jinja`). The owner chose instead to give the
model DeepSeek's own markers as real tokens: adding a token to an existing model and proving it learns is the
more valuable result.

## Decision

- Format: DeepSeek R1 tool syntax (`<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>NAME` +
  JSON in a code fence + `<｜tool▁call▁end｜><｜tool▁calls▁end｜>`), which llama.cpp's DeepSeek R1 parser reads.
- Template: `r1d/deepseek_tools.jinja`, llama.cpp's DeepSeek R1 tool template with fixes (a turn with text
  keeps its calls; string arguments not encoded twice; each run of tool results its own block; content given
  as text parts accepted).
- The Qwen template stays in the repo as a fallback comparison only.

## Consequences

Nine new rows must be learned rather than reused, which is the point of the experiment.

## Evidence

`r1d/tests/test_deepseek_template.py` (fails on llama.cpp's stock template, passes on ours).
