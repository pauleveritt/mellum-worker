#!/usr/bin/env bash
# Run the lab teacher (Mellum on vLLM) over the training tasks in the student's harness shape.
#   r1d/teacher_batch.sh <batch-name> <repeats> <parallel>
# Each (task, repeat) is one harness session, run <parallel> at a time. Runs land in runs/<batch-name>/<task>/.
# Record every batch in r1d/DISTILL.md before its data is used.
set -u
NAME=${1:?batch name}; REPEATS=${2:-3}; PAR=${3:-4}
REPO=/Users/mac/projects/mellum-worker; CODE=$REPO/learn/code; OUT=$REPO/runs/$NAME; LOGS=$REPO/learn/finetune/out/teacher/$NAME
SHAPE="preset:baseline-worker,context/trim-tool-output,context/narrow-tools,prompt/think-briefly"
mkdir -p "$LOGS"
jobs=()
for dir in suites/tools-train suites/py-features-train suites-local/satyrn-train; do
  for t in $(ls "$CODE/$dir"); do
    [ -f "$CODE/$dir/$t/expected.json" ] || continue
    case "$t" in satyrn-selfhost-preflight-quiet|satyrn-selfhost-speed-probe) continue;; esac  # known-good fix fails its own check
    for k in $(seq 1 "$REPEATS"); do jobs+=("$dir $t $k"); done
  done
done
echo "=== TEACHER BATCH $NAME: ${#jobs[@]} sessions, $PAR at a time, $(date +%H:%M:%S)"
printf '%s\n' "${jobs[@]}" | xargs -P "$PAR" -L 1 bash -c '
  dir=$0; t=$1; k=$2
  cd '"$CODE"' && uv run python harness.py run --suites-dir "$dir" --suite "$t" --arm vanilla --remedy "'"$SHAPE"'" \
    --profile profile-lab --grade --repeat 1 --deadline 1200 --runs-dir "'"$OUT"'/$t" > "'"$LOGS"'/$t-$k.log" 2>&1
  echo "$(date +%H:%M:%S) $t #$k: $(grep -E "^$t(:| \[)" "'"$LOGS"'/$t-$k.log" | tail -1 | cut -c1-140)"'
echo "=== TEACHER BATCH $NAME COMPLETE $(date +%H:%M:%S)"
