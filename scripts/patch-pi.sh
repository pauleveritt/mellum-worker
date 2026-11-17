#!/usr/bin/env bash
# Install the content-tool-call-assist extension into a Pi checkout.
#
# The extension imports @earendil-works/pi-ai/compat and
# @earendil-works/pi-coding-agent, which resolve only inside a Pi checkout, so
# Pi cannot load it from this repo directly — we copy it into the checkout's
# examples/extensions and load it from there. extensions/content-tool-call-assist
# in this repo is the canonical source (also mirrored to our Pi fork).
#
# Usage: scripts/patch-pi.sh [PI_DIR]   (PI_DIR defaults to $PI_DIR or ~/projects/pi)
set -euo pipefail

PI_DIR="${1:-${PI_DIR:-$HOME/projects/pi}}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO/extensions/content-tool-call-assist/index.ts"
DEST_DIR="$PI_DIR/packages/coding-agent/examples/extensions/content-tool-call-assist"

if [ ! -d "$PI_DIR/packages/coding-agent" ]; then
  echo "error: $PI_DIR is not a Pi checkout (no packages/coding-agent)" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
cp "$SRC" "$DEST_DIR/index.ts"
echo "patched: $DEST_DIR/index.ts"
echo "load it with:  pi -e $DEST_DIR"
echo "or point the ladder at it:  --pi-extension $DEST_DIR"
