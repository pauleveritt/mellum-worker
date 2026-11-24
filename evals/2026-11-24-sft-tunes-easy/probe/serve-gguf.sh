#!/usr/bin/env bash
# Serve a local GGUF with exactly backend.py's serve flags, swapping -hf for -m.
# The alias stays the profile's model id so learn/code/profile works unchanged.
# Usage: serve-gguf.sh <path-to.gguf>
set -euo pipefail
GGUF="${1:?usage: serve-gguf.sh <gguf>}"
[ -f "$GGUF" ] || { echo "no such gguf: $GGUF" >&2; exit 1; }
echo "serving: $GGUF"
exec llama-server -m "$GGUF" -a Mellum2.1-12B-A2.5B-Thinking \
  --host 127.0.0.1 --port 8001 -c 50000 -np 1 \
  --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0
