#!/usr/bin/env bash
# train_model.sh <name> <data dir> [--resume]: train, write the manifest, gate on the held-out margin,
# build the Q4_K_M GGUF and screen it on Easy. Run detached; a crash loses one update (rerun with --resume).
#   nohup bash learn/finetune/pipeline/train_model.sh mix120 data_dpo_mix120 > learn/finetune/out/mix120.log 2>&1 &
set -uo pipefail
NAME="$1"; DATA="$2"; RESUME="${3:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"; FT="$(dirname "$HERE")"; REPO="$(cd "$FT/../.." && pwd)"
BASE="${MELLUM_MLX_BASE:-$REPO/.models/Mellum2.1-12B-A2.5B-Thinking-6bit}"
OUT="${MELLUM_MODELS:-$HOME/models/mellum-ours}"; LOGS="$FT/out/$NAME"; mkdir -p "$LOGS"
SETTINGS='{"beta": 10, "lr": 2e-5, "accum": 4, "step": 2048, "epochs": 1, "eval_every": 15, "rank": 8, "scale": 2.0, "num_layers": 16, "seed": 0}'
cd "$FT"
echo "=== TRAIN START $(date +%H:%M:%S) [$NAME on $DATA] ==="
uv run --with mlx-lm==0.32.2 --with mlx-lm-lora==5.10.2 python dpo_native_train.py --data "$DATA" --model "$BASE" \
  --out "adapters_$NAME" --beta 10 --lr 2e-5 --accum 4 --step 2048 --epochs 1 --eval-every 15 $RESUME 2>&1 \
  | tee -a "$LOGS/train.log"
grep -q "\[done\] saved" "$LOGS/train.log" || { echo "TRAIN FAILED"; exit 1; }
MANIFEST="$FT/models/$NAME/MANIFEST.json"
uv run --with mlx-lm==0.32.2 --with mlx-lm-lora==5.10.2 python run_manifest.py --name "$NAME" --data "$DATA" \
  --base "$BASE" --adapter "adapters_$NAME" --log "$LOGS/train.log" --settings "$SETTINGS" --out "$MANIFEST"
M=$(grep "\[eval\]" "$LOGS/train.log" | tail -1 | sed -E 's/.*margin (-?[0-9.]+).*/\1/')
echo "final held-out margin $M"
awk -v m="$M" 'BEGIN{exit !(m>0)}' || { echo "=== HELD-OUT MARGIN NOT POSITIVE ($M): not converting ==="; exit 0; }
bash "$HERE/build_gguf.sh" "$NAME" || { echo "BUILD FAILED"; exit 1; }
GGUF="$OUT/$NAME-Q4_K_M.gguf"
EXTRA="{\"llama_cpp_convert_commit\": \"cd959bae9\", \"llama_quantize\": \"$(llama-quantize --version 2>&1 | grep -m1 version | tr -d '"')\"}"
uv run --with mlx-lm==0.32.2 --with mlx-lm-lora==5.10.2 python run_manifest.py --name "$NAME" --data "$DATA" \
  --base "$BASE" --adapter "adapters_$NAME" --log "$LOGS/train.log" --settings "$SETTINGS" --gguf "$GGUF" \
  --extra "$EXTRA" --out "$MANIFEST"
bash "$HERE/screen_easy.sh" "$NAME" "$GGUF"
echo "=== ALL DONE $(date +%H:%M:%S) ==="
