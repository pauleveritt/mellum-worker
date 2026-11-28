#!/usr/bin/env bash
# Product (mode) — the shipped worker (Mellum Mode: guards + facts + the 7-tool
# set) on a rung, as it actually runs. The companion to scripts/screen.sh; use
# these two, don't hand-assemble ladder flags.
#
# Usage:
#   scripts/product.sh <rung> [acceptance-test] [out-dir]
#
# Fixed:  --mode mode --profile tuned --repeat 3 (guards + facts forced on by Mode).
# Knobs:  rung, optional acceptance-test (hand Mode a frozen test to pass),
#         out (default: runs/<date>-product-rung<N>).
#
# NEEDS the omlx provider in ~/.pi/agent/models.json, or Pi fails with
# "model not found" (direct mode wires its own; Mode reads the profile):
#   cp templates/pi/models.omlx.json ~/.pi/agent/models.json
#
# Watch it live in another tab:  python ladder/scripts/watch_ladder.py
set -euo pipefail
cd "$(dirname "$0")/.."                       # repo root

RUNG="${1:?usage: scripts/product.sh <rung> [acceptance-test] [out-dir]}"
ACC="${2:-}"
OUT="${3:-}"

if ! grep -q '"omlx"' "${HOME}/.pi/agent/models.json" 2>/dev/null; then
  echo "WARNING: no omlx provider in ~/.pi/agent/models.json — Mellum Mode will fail 'model not found'." >&2
  echo "  fix:  cp templates/pi/models.omlx.json ~/.pi/agent/models.json" >&2
fi

[ -z "$OUT" ] && OUT="runs/$(date +%F)-product-rung${RUNG}"
[ -n "$ACC" ] && { [ -f "$ACC" ] || { echo "acceptance test not found: $ACC" >&2; exit 1; }; }

echo "Product (mode): rung ${RUNG}"
echo "  out: ${OUT}"
echo "  watch live in another tab:  python ladder/scripts/watch_ladder.py"
cd ladder
args=(--mode mode --profile tuned --repeat 3 --rung "${RUNG}" --out "../${OUT}")
[ -n "$ACC" ] && args+=(--acceptance-test "../${ACC}")
exec uv run python -m ladder.run_ladder "${args[@]}"
