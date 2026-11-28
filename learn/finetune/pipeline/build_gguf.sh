#!/usr/bin/env bash
# build_gguf.sh <name>: fuse adapters_<name> into the 6-bit MLX base, slice the stacked experts into the
# per-expert tensors llama.cpp's Mellum converter wants, convert to f16 GGUF and quantise Q4_K_M.
# llama.cpp's converter is pinned to the commit every published tune was built with.
set -euo pipefail
NAME="$1"
HERE="$(cd "$(dirname "$0")" && pwd)"; FT="$(dirname "$HERE")"; REPO="$(cd "$FT/../.." && pwd)"
BASE="${MELLUM_MLX_BASE:-$REPO/.models/Mellum2.1-12B-A2.5B-Thinking-6bit}"
OUT="${MELLUM_MODELS:-$HOME/models/mellum-ours}"
LLAMACPP_COMMIT=cd959bae9   # llama.cpp b12110
LC="${LLAMACPP_DIR:-$HOME/.cache/mellum-llamacpp-$LLAMACPP_COMMIT}"
if [ ! -f "$LC/convert_hf_to_gguf.py" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ggml-org/llama.cpp "$LC"
  git -C "$LC" sparse-checkout set --no-cone /convert_hf_to_gguf.py /gguf-py /conversion /requirements
  git -C "$LC" checkout -q "$LLAMACPP_COMMIT"
fi
[ "$(git -C "$LC" rev-parse --short=9 HEAD)" = "$LLAMACPP_COMMIT" ] || { echo "llama.cpp is not at $LLAMACPP_COMMIT"; exit 1; }
mkdir -p "$OUT"; cd "$FT"
uv run --with mlx-lm==0.32.2 python -m mlx_lm fuse --model "$BASE" --adapter-path "adapters_$NAME" --save-path "$OUT/fused-$NAME" --dequantize
uv run --no-project --with torch --with safetensors --with numpy python "$HERE/remap_experts.py" "$OUT/fused-$NAME"
PYTHONPATH="$LC/gguf-py" uv run --no-project --with torch --with safetensors --with numpy --with transformers \
  --with sentencepiece --with protobuf --with pyyaml python "$LC/convert_hf_to_gguf.py" "$OUT/fused-$NAME" \
  --outtype f16 --outfile "$OUT/$NAME-f16.gguf"
llama-quantize "$OUT/$NAME-f16.gguf" "$OUT/$NAME-Q4_K_M.gguf" Q4_K_M
rm -rf "$OUT/fused-$NAME" "$OUT/$NAME-f16.gguf"
echo "GGUF: $OUT/$NAME-Q4_K_M.gguf"
