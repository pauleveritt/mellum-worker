#!/usr/bin/env bash
# delegate.sh — the bridge: a primary (Claude here, or any caller) farms ONE narrow,
# test-driven task to the local Mellum worker, which runs headlessly on the local
# llama-server (:8001) and edits files in the given workspace. Local tokens, not the
# primary's. The primary owns exploration and verification; this runs the implementation.
#
#   bash scripts/delegate.sh <workspace-dir> "<brief>"
#
# The brief is the handoff packet in one line: what to build and the test command to
# make green. Keep it narrow — the layout and the failing test are the primary's job,
# handed over in <workspace-dir> before calling this.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

if [ "$#" -lt 2 ]; then
    echo "usage: bash scripts/delegate.sh <workspace-dir> \"<brief>\"" >&2
    exit 2
fi
WS="$1"; shift
BRIEF="$*"

[ -d "$WS" ] || { echo "[delegate] no such workspace: $WS" >&2; exit 1; }
curl -s -m 3 http://127.0.0.1:8001/health 2>/dev/null | grep -q '"status":"ok"' \
    || { echo "[delegate] the Mellum server is not up on :8001 — run bash run.sh first" >&2; exit 1; }

# The worker runs on the local Mellum profile; -e loads the worker so /mellum exists in
# any cwd. Lean by default: no remedies (the primary supplied the brief and the test).
export PI_CODING_AGENT_DIR="$REPO_DIR/learn/code/profile"
export PI_SKIP_VERSION_CHECK=1
# This IS the worker doing the implementation, so it must not offer the delegate tool
# itself — mark it a child, same as the tool's own spawn does.
export MELLUM_WORKER_CHILD=1
cd "$WS" || exit 1
# --no-approve is essential headless: without it the worker's write/edit/bash calls
# wait for an approval that never comes, and it produces nothing.
exec pi -p --no-approve --no-skills --no-prompt-templates --no-themes \
    -e "$REPO_DIR/extensions/mellum-worker.ts" "/mellum $BRIEF"
