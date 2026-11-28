#!/usr/bin/env bash
# The exact command that built r1d/data_sft_v1 (run from learn/finetune).
set -eu
ARGS=$(grep -v mint-satyrn sources_base_runs.txt | sed "s#^#--source ../../runs/#" | tr "\n" " ")
SRC=""
for R in 2026-11-26-ours-mix120-medium 2026-11-26-tools-medium 2026-11-27-tools15-medium 2026-11-27-tools15-medium2 2026-11-27-tools2-medium; do
  SRC="$SRC --source ../../runs/$R"
done
uv run --no-project --with jinja2 --with tokenizers python r1d/build_sft.py $ARGS $SRC \
  --source-all-phases ../../runs/2026-11-24-mint-satyrn \
  --source-all-phases ../../runs/2026-11-26-pyfeat-train-base --source-all-phases ../../runs/2026-11-26-pyfeat-train-ours-mix120 \
  --tokenizer ~/models/r1d-1.5b/hf-tooltokens --out r1d/data_sft_v1
