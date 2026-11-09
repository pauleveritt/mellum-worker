#!/usr/bin/env bash
# Runs on the pod, as root, from the copied checkout: install the pinned uv, then let learn/code/pod.py
# do the rest from learn/code/host/pod-pins.json. Safe to rerun; finished steps are skipped.
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
prefix="${MELLUM_POD_PREFIX:-/opt/mellum}"
uv_version="$(sed -n 's/.*"uv": "\(.*\)".*/\1/p' "$repo/learn/code/host/pod-pins.json")"
mkdir -p "$prefix/bin"
[ -x "$prefix/bin/uv" ] || curl -LsSf "https://astral.sh/uv/$uv_version/install.sh" |
  env UV_INSTALL_DIR="$prefix/bin" UV_NO_MODIFY_PATH=1 sh
export PATH="$prefix/bin:$PATH" UV_PYTHON_INSTALL_DIR="$prefix/python"
cd "$repo"
uv run python learn/code/pod.py setup --prefix "$prefix" --repo "$repo"
