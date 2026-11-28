---
phase: finetune
feature_cycle: learn/finetune
cycle: 1
lifecycle: active
---

# Teaching a 1.5B model tool calling through new tokens — plan

**Goal:** prove that tool calling can be added to a model that has none, by adding the tool-call markers as
real tokens and training only what they need. Model: DeepSeek-R1-Distill-Qwen-1.5B (no tool calling; its
template names DeepSeek tool markers its vocabulary lacks).

## Steps

1. **Add the tokens** (done, ae6af581). `learn/finetune/r1d/add_tokens.py` puts DeepSeek's nine tool markers
   in spare embedding rows 151665-151673 (no resize), each starting at the mean of its old pieces; every
   other row unchanged. Proven single tokens in the tokenizer, through transformers and in llama.cpp.
   `r1d/deepseek_tools.jinja` is the chat template (llama.cpp's DeepSeek R1 tool format, fixed).
2. **Build the supervised set** from passing Mellum/Tsunami runs, rendered in that template: one example per
   assistant act (context, then the act's thinking, text and calls), loss on the act only. Committed with a
   SOURCE.md, sectioned files under 45 MB.
3. **Train** LoRA on the layers plus the nine new embedding and output-head rows only; every existing row
   frozen. Record a MANIFEST.
4. **Prove it worked:**
   - before/after: how often the model emits the markers where a call belongs (before is ~0);
   - llama-server with `--jinja` returns parsed tool calls;
   - Easy screen, same harness settings as Mellum, before vs after;
   - plain prompts: answers without tools unchanged (the old rows were frozen).
5. **Speculative decoding (n-gram):** serve the trained model with `--spec-type ngram-mod` and measure tokens
   per second on recorded agent turns with and without it; confirm the outputs match (llama.cpp verifies
   each draft token, so only speed should change). This is the baseline the draft head has to beat.
6. **Train our own draft head** (the goal): a small speculative head on the trained 1.5B's hidden states
   (EAGLE-3 / DFlash style; llama.cpp serves both types), trained on the 1.5B's own outputs so it shares the
   new tokens. Test against n-gram on the same recorded agent turns: tokens per second, acceptance length,
   and identical outputs. Kept only if it beats n-gram.

## Out of scope (now)

DPO on the 1.5B's own runs (after it can call tools); a separate draft model; publishing.
