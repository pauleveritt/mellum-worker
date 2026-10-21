#!/usr/bin/env bash
# Halve (re-quantize) an MLX model to a lower bit depth, to measure how far a
# cheaper worker holds up on the ladder. "Halve" a 6-bit model = 3-bit (half the
# bits per weight); 4-bit is the gentler option.
#
# Usage:
#   scripts/halve-model.sh <source-model-dir> [bits] [group-size]
#
#   <source-model-dir>  an MLX model dir, e.g. .models/Mellum2.1-...-6bit
#   bits                target bits per weight (default 3)
#   group-size          quantization group size (default 64)
#
# Output: .models/<name>-<bits>bit  (the source basename with its -Nbit suffix
# swapped, so .models/Mellum...-6bit -> .models/Mellum...-3bit).
#
# CAVEAT — read before trusting a result. Re-quantizing an already-quantized
# model is lossy-on-lossy: a quality drop may be the double-quant, not the
# smaller size. For a fair "halved" comparison, convert from the original
# fp16/bf16 weights instead. When the source is already quantized this tool
# dequantizes to fp16 first (the least-bad re-quant path) — still not a clean
# single quantization. The ladder run that uses the output must say so.
#
# Needs: uv. mlx-lm is pulled into an ephemeral uv env; nothing is installed
# globally.
set -euo pipefail

SRC="${1:?usage: scripts/halve-model.sh <source-model-dir> [bits] [group-size]}"
BITS="${2:-3}"
GROUP="${3:-64}"
[ -d "$SRC" ] || { echo "no such model dir: $SRC" >&2; exit 1; }

base="$(basename "${SRC%/}")"
if [[ "$base" =~ -[0-9]+bit$ ]]; then
  out_name="${base%-*bit}-${BITS}bit"
else
  out_name="${base}-${BITS}bit"
fi
OUT=".models/${out_name}"
[ -e "$OUT" ] && { echo "output already exists: $OUT (remove it first)" >&2; exit 1; }

convert() { uv run --with mlx-lm python -m mlx_lm convert "$@"; }

echo "halving ${SRC} -> ${OUT}  (${BITS}-bit, group ${GROUP})"
if grep -q '"quantization"' "${SRC%/}/config.json" 2>/dev/null; then
  echo "source is already quantized; dequantizing to fp16 first (lossy-on-lossy)"
  TMP=".models/.${out_name}-fp16-tmp"
  rm -rf "$TMP"
  convert --dequantize --hf-path "$SRC" --mlx-path "$TMP"
  convert --quantize --q-bits "$BITS" --q-group-size "$GROUP" --hf-path "$TMP" --mlx-path "$OUT"
  rm -rf "$TMP"
else
  convert --quantize --q-bits "$BITS" --q-group-size "$GROUP" --hf-path "$SRC" --mlx-path "$OUT"
fi
echo "done: ${OUT}"
du -sh "$OUT"
