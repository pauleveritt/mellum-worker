#!/usr/bin/env bash
# The exact command that built r1d/data_sft_v2 (run from learn/finetune).
set -eu
uv run --no-project --with jinja2 --with tokenizers python r1d/build_sft.py \
  --source-all-phases ../../runs/2026-11-28-teacher-v2 --all-runs --format deepseek \
  --tokenizer ~/models/r1d-1.5b/hf-tooltokens-v2 --out r1d/data_sft_v2
