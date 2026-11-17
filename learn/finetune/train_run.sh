#!/usr/bin/env bash
cd . || exit 1
rm -rf adapters_adherence; mkdir -p adapters_adherence
exec .venv/bin/python -m mlx_lm lora \
  --model mlx-community/Mellum2-12B-A2.5B-Thinking-4bit \
  --train --data data_adherence \
  --fine-tune-type dora --num-layers -1 -c lora_config.yaml \
  --iters 500 --batch-size 1 --max-seq-length 2048 \
  --learning-rate 1e-4 \
  --steps-per-report 10 --steps-per-eval 50 --val-batches 10 --save-every 100 \
  --adapter-path adapters_adherence
