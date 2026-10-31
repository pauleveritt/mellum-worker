#!/usr/bin/env bash
# Start the local Mellum server and Pi, pointed at this repo.
#
# install.sh hands off here once the tools are in. Next time, just: bash run.sh
# The first run downloads the ~8 GB Q4_K_M model (with a progress bar); after
# that it is quick.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"
export PATH="$HOME/.local/bin:$PATH"

# llama.cpp's -hf downloads the GGUF into the Hugging Face hub cache; the blob
# grows there while it downloads. TOTAL_MB is the Q4_K_M size, so the bar is
# approximate — health, not size, decides when the server is actually ready.
MODEL_BLOBS="$HOME/.cache/huggingface/hub/models--JetBrains--Mellum2.1-12B-A2.5B-Thinking-GGUF/blobs"
TOTAL_MB=7700

blob_mb() {
    local f
    f="$(ls -S "$MODEL_BLOBS"/* 2>/dev/null | grep -v '\.lock$' | head -1)"
    [ -n "${f:-}" ] && [ -f "$f" ] || { echo 0; return; }
    echo $(( $(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0) / 1048576 ))
}

draw_bar() {   # $1 done MB, $2 total MB
    local done=$1 total=$2 width=36 pct fill i s=''
    (( total < 1 )) && total=1
    pct=$(( done * 100 / total )); (( pct > 99 )) && pct=99
    fill=$(( pct * width / 100 ))
    for (( i = 0; i < width; i++ )); do (( i < fill )) && s+='#' || s+='-'; done
    printf '\r  [%s] %3d%%  %d/%d MB ' "$s" "$pct" "$done" "$total"
}

start_server() {
    # Already serving? Go straight to Pi.
    if curl -s -m 3 http://127.0.0.1:8002/health 2>/dev/null | grep -q '"status":"ok"'; then
        echo "[OK] the Mellum server is already up."
        return 0
    fi
    # Not healthy — clear the decks before starting, so a stray llama-server or
    # something squatting on 8002 (e.g. a leftover uvicorn from a lesson) can't
    # block the bind. This is why a re-run used to fail with "server did not start".
    local squatters
    uv run scripts/backend.py stop >/dev/null 2>&1 || true
    pkill -f llama-server 2>/dev/null || true
    squatters="$(lsof -ti tcp:8002 2>/dev/null || true)"
    [ -n "${squatters:-}" ] && kill $squatters 2>/dev/null || true
    sleep 1
    local have=0
    (( $(blob_mb) >= TOTAL_MB * 9 / 10 )) && have=1
    if (( have )); then
        echo "Starting the Mellum server..."
    else
        echo "Starting the Mellum server. The model (~8 GB Q4_K_M) downloads once:"
    fi
    # backend.py start downloads (if needed), launches the server and waits for
    # health; run it in the background so we can show progress while it works.
    # --wait-seconds is generous: the first run must cover the whole download
    # plus the model load, not just the load (the default is too short and the
    # start would "fail" while the server kept downloading in the background).
    uv run scripts/backend.py start --wait-seconds 1800 >/dev/null 2>&1 &
    local pid=$! mb
    while kill -0 "$pid" 2>/dev/null; do
        mb="$(blob_mb)"
        if (( mb >= TOTAL_MB )); then
            printf '\r  loading the model into memory...%*s' 20 ''
        elif (( mb > 0 )); then
            draw_bar "$mb" "$TOTAL_MB"
        else
            printf '\r  preparing...%*s' 24 ''
        fi
        sleep 1
    done
    printf '\n'
    wait "$pid"
}

if ! start_server; then
    echo "[ERROR] the server did not start; see learn/getting-started/troubleshoot." >&2
    exit 1
fi
uv run scripts/backend.py status || true

# Pi, pointed at this repo's profile (which targets the local server). The
# mellum-worker harness (/mellum) comes from the plugin install.sh set up.
# --no-skills keeps the author's own ~/.agents/skills out of the learner's run,
# so the course runs on the repo's extensions alone (lessons, remedies,
# think-tags) and nobody's global skills leak in. Extensions and AGENTS.md stay.
export PI_CODING_AGENT_DIR="$REPO_DIR/learn/code/profile"
export PI_SKIP_VERSION_CHECK=1   # stay on the pinned 1.4.0; hide the update nag
echo
echo "Starting Pi. Put the worker on a job with:  /mellum <task>"
exec pi --no-skills
