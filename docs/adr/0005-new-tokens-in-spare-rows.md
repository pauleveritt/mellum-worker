# 0005: Teach a new format by adding real tokens in spare rows, training only those rows plus LoRA

- **Date:** 2026-11-28
- **Status:** Accepted

## Context

DeepSeek-R1-Distill-Qwen-1.5B has no tool calling. Its template names DeepSeek's tool markers, but its
tokenizer splits each into about 11 ordinary tokens. Its embedding table and output head (not tied) are
151,936 rows while the tokenizer uses 151,665: 271 rows are spare.

## Decision

- Add the format's markers as special tokens in the spare rows (`learn/finetune/r1d/add_tokens.py`), so no
  resize; start each new row at the mean of its old pieces' rows.
- List every added token, old and new, in `added_tokens_decoder`: with a partial list, transformers' Qwen2
  tokenizer re-lays all special tokens, and the GGUF converter copies the damage.
- Prove the tokens in three places: the tokenizer, transformers with the real `config.json`, and llama.cpp's
  `/tokenize` on the converted GGUF.
- Train supervised: LoRA on every layer plus only the new rows (`r1d/rows.py` wraps both tables with a trainable
  delta; every other row frozen), loss on completions only, head run only on completion positions.

## Consequences

The rest of the vocabulary can't move, so plain behaviour is protected apart from what LoRA changes. 9.26M
trainable parameters; 11.2 GB peak on an M3 Max; about 44 seconds per update of 4 examples.

## Evidence

Smoke run, 40 examples: marker hit rate (is `<｜tool▁calls▁begin｜>` ranked first where a call starts) 0/10
before, 10/10 after 10 updates; validation loss 2.29 to 1.32. Tests in `learn/finetune/r1d/tests/`. Research
note `docs/superpowers/research/2026-11-28-tool-tokens-1-5b.md`.
