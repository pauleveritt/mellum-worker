#!/usr/bin/env bash
# Screen (direct, mediated) — the standard way to measure a worker on an
# AgentClinic rung. Everything is fixed but the rung and the model, so screens
# compare like-for-like. Don't hand-assemble ladder flags; use this.
#
# Usage:
#   scripts/screen.sh <rung 6-9> <model-id> [acceptance-test] [out-dir]
#
# Fixed:  --mode direct --profile tuned --repeat 3 --redispatch 5 --effort-ramp
#         --thinking off --guards, plus the default v7 prompt and tools.
# Knobs:  rung, model-id, acceptance-test (default: the committed frozen phase
#         test for the rung), out (default: runs/<date>-screen-<model>-rung<N>).
#
# Guards are ON (the loop breaker fails a stuck worker fast — see the run
# standard). Runs land in runs/ (git-ignored); record a kept run into
# docs/ladder/<date-topic>/ with the raw stripped (AGENTS.md, scripts/halve-model.md).
#
# Watch it live in another tab:  python ladder/scripts/watch_ladder.py
set -euo pipefail
cd "$(dirname "$0")/.."                       # repo root

RUNG="${1:?usage: scripts/screen.sh <rung 6-9> <model-id> [acceptance-test] [out-dir]}"
MODEL="${2:?usage: scripts/screen.sh <rung 6-9> <model-id> [acceptance-test] [out-dir]}"
ACC="${3:-}"
OUT="${4:-}"

if [ -z "$ACC" ]; then
  case "$RUNG" in
    6) phase=1 ;; 7) phase=2 ;; 8) phase=3 ;; 9) phase=4 ;;
    *) echo "rung $RUNG has no default frozen test; pass one as arg 3 (rungs 6-9 map to phases 1-4)" >&2; exit 1 ;;
  esac
  ACC="docs/ladder/2026-10-20-v7-ablation/acceptance/test_phase${phase}.py"
fi
[ -f "$ACC" ] || { echo "acceptance test not found: $ACC" >&2; exit 1; }

if [ -z "$OUT" ]; then
  safe_model="$(printf '%s' "$MODEL" | tr '/ ' '--')"
  OUT="runs/$(date +%F)-screen-${safe_model}-rung${RUNG}"
fi

echo "Screen: rung ${RUNG}, model ${MODEL}"
echo "  test: ${ACC}"
echo "  out:  ${OUT}"
echo "  watch live in another tab:  python ladder/scripts/watch_ladder.py"
cd ladder
exec uv run python -m ladder.run_ladder \
  --mode direct --profile tuned --repeat 3 \
  --acceptance-test "../${ACC}" --redispatch 5 --effort-ramp --thinking off --guards \
  --rung "${RUNG}" --model-id "${MODEL}" --out "../${OUT}"
