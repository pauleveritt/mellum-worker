#!/usr/bin/env bash
# screen_easy.sh <tag> <gguf> [remedy]: serve a GGUF exactly as the base was served, then Easy n=3.
set -u
TAG="$1"; GGUF="$2"; REM="${3:-preset:baseline-worker}"
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../../.." && pwd)"; LOGS="$HERE/../out/$TAG"; mkdir -p "$LOGS"
lsof -ti :8001 | xargs kill 2>/dev/null; sleep 2
llama-server -m "$GGUF" -a Mellum2.1-12B-A2.5B-Thinking --host 127.0.0.1 --port 8001 -c 50000 -np 1 \
  --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0 -ngl 999 > "$LOGS/llama-server.log" 2>&1 &
SRV=$!; trap 'kill $SRV 2>/dev/null' EXIT
for i in $(seq 1 90); do curl -s -m3 http://127.0.0.1:8001/health | grep -q ok && break; sleep 2; done
echo "EASY SCREEN [$TAG] $(basename "$GGUF") | $(llama-server --version 2>&1 | grep -m1 version) | remedy=$REM"
( cd "$REPO/learn/code" && uv run python harness.py run --suite easy --arm vanilla --remedy "$REM" --grade \
    --repeat 3 --deadline 600 --runs-dir "$REPO/runs/$(date +%Y-%m-%d)-$TAG-easy" )
echo "=== EASY SCREEN [$TAG] COMPLETE ==="
