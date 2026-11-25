# Rebuilding a tuned Mellum model

Everything a tune depends on is pinned here or in its `models/<name>/MANIFEST.json`. A rebuild from the same
inputs follows these steps.

## 1. The base models (pinned by checksum)

| Role | Source | Revision | SHA-256 |
|---|---|---|---|
| Training base (MLX 6-bit, gates 8-bit) | `pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit` | `4b8ed3894b9ebb8e4579d5b6b0356f187e65aea1` | `model-00001-of-00002.safetensors` `4c563ab1ea93eb1c2c12bf5258e27ad7b3ceac88f07f825899c6e27e44d1b492`, `model-00002-of-00002.safetensors` `475afd1005efa2cc78c68f01c8337d658ff766fef8942b7b25aff5c5bec75568` |
| Screening base (GGUF Q4_K_M) | `JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF`, file `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf` | `4159d684ffdb09ba89dc2a58feb3e75c54eef036` | recorded in each screen's run records |

```bash
uv run --no-project --with huggingface_hub hf download pauleveritt/Mellum2.1-12B-A2.5B-Thinking-mlx-6bit \
  --revision 4b8ed3894b9ebb8e4579d5b6b0356f187e65aea1 --local-dir .models/Mellum2.1-12B-A2.5B-Thinking-6bit
shasum -a 256 .models/Mellum2.1-12B-A2.5B-Thinking-6bit/model-0000*.safetensors   # must match the table
```

The training base lives on someone else's account; a private backup of these two files keeps a rebuild possible
if it moves.

## 2. The training data

Every training set is committed under `learn/finetune/data_dpo_*/` with a `SOURCE.md` saying how it was built.
A set is never rebuilt in place: `build_dpo_phases.py` refuses an existing `--out`, so a rebuild is a new,
versioned folder. Rebuilding a set from scratch needs the recorded runs in `runs/` (git-ignored); keep a backup.

## 3. Train, gate, convert and screen

```bash
cd learn/finetune
nohup bash pipeline/train_model.sh <name> data_dpo_<set> > out/<name>.log 2>&1 < /dev/null &
tail -F out/<name>.log
```

`train_model.sh` pins every setting (IPO beta 10, lr 2e-5, 4 pairs per update, 2048-token chunks, 1 epoch,
LoRA rank 8 scale 2.0 on 16 layers, seed 0) and the trainer's packages (`mlx-lm==0.32.2`,
`mlx-lm-lora==5.10.2`). It saves weights and optimizer state after every update; after a crash, rerun it with
`--resume` as the third argument to continue with exactly the remaining batches. It then:

1. writes `models/<name>/MANIFEST.json`: code commit and dirty flag, data and base checksums, adapter checksums,
   settings, every logged update and held-out eval, package versions;
2. stops unless the final held-out margin is above zero;
3. builds the GGUF with `pipeline/build_gguf.sh` (llama.cpp's converter pinned to commit `cd959bae9`, b12110,
   `remap_experts.py` to slice the stacked experts, `llama-quantize` to Q4_K_M) and adds its checksum and the
   `llama-quantize` version to the manifest;
4. screens it on Easy n=3 with `pipeline/screen_easy.sh`, served exactly as the base is.

## 4. What is not in git

- `adapters_<name>/` (about 325 MB) and the GGUF (about 7.5 GB): checksums are in the manifest; keep a backup.
- `runs/` (the recorded traces every training set is built from).
- `out/<name>/` (logs; the manifest carries the training log's numbers).
