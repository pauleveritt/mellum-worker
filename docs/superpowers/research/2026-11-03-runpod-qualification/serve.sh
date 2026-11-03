#!/usr/bin/env bash
set -euo pipefail
export LLAMA_CACHE=/workspace/mellum/cache
test -f /workspace/mellum/qualification/build-ok
test -f /workspace/mellum/qualification/weights-ok
exec /workspace/mellum/llama.cpp/build/bin/llama-server \
  -m /workspace/mellum/cache/Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf \
  -a Mellum2.1-12B-A2.5B-Thinking \
  --host 127.0.0.1 --port 18001 \
  -c 100000 -np 2 --no-kv-unified \
  --jinja -fa auto --cont-batching \
  -t 16 -tb 16 \
  -b 512 -ub 512 -ctk q8_0 -ctv q8_0 -ngl 999
