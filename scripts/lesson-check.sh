#!/usr/bin/env bash
# A lesson check: run one lesson's before line, then its after line, at the page's n, on the
# reference model, and print the two verdicts. The lines come from the lesson page (the /lesson
# tutor's parser), so the page is the only source. Arms run one after the other, with port 8000
# checked free before each: sessions may start servers on this machine.
#
# Usage:
#   scripts/lesson-check.sh <lesson number> [--profile DIR] [--dry-run] [--foreground]
#
# Default profile: scripts/baseline/lan-profile (the 6-bit on the LAN vLLM host, LC.28).
# Detaches by default (nohup, HUP ignored), so closing a terminal tab cannot kill a check; the
# log is runs/<slug>-check-<ts>-<sha>/check.log. Runs land in runs/ (git-ignored); record a kept
# check under docs/ladder/<date>-<slug>-check/ with the raw stripped.
set -uo pipefail
cd "$(dirname "$0")/.."

NUMBER="${1:?usage: scripts/lesson-check.sh <lesson number> [--profile DIR] [--dry-run] [--foreground]}"
shift
PROFILE="$PWD/scripts/baseline/lan-profile"
DRY=0
FOREGROUND=0
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) PROFILE="$(cd "$2" && pwd)"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --foreground) FOREGROUND=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ -x .baseline/pi-1.3.0/bin/pi ]; then
  export PATH="$PWD/.baseline/pi-1.3.0/bin:$PWD/.baseline/node-v22.19.0/bin:$PATH"
fi
export PI_SKIP_VERSION_CHECK=1

OUT="${LESSON_CHECK_OUT:-$PWD/runs/$NUMBER-check-$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)}"
LINES="$(node scripts/lesson-lines.mjs "$NUMBER" "$OUT" "$PROFILE")" || exit 1
if [ "$DRY" = 1 ]; then
  printf '%s\n' "$LINES"
  exit 0
fi

if [ "$FOREGROUND" = 0 ] && [ -z "${LESSON_CHECK_OUT:-}" ]; then
  mkdir -p "$OUT"
  LESSON_CHECK_OUT="$OUT" nohup "$0" "$NUMBER" --profile "$PROFILE" --foreground > "$OUT/check.log" 2>&1 &
  echo "lesson check $NUMBER running detached; follow it with: tail -f $OUT/check.log"
  exit 0
fi

trap '' HUP
mkdir -p "$OUT"
echo "lesson check $NUMBER into $OUT at $(git rev-parse --short HEAD), profile $PROFILE, started $(date -u +%H:%M) UTC"
ARM=before
while IFS= read -r LINE; do
  if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "port 8000 busy before $ARM:"; lsof -nP -iTCP:8000 -sTCP:LISTEN; exit 1
  fi
  echo "== $ARM at $(date -u +%H:%M) UTC: $LINE"
  eval "$LINE" < /dev/null 2>&1 | tee "$OUT/$ARM.log"
  ARM=after
done <<< "$LINES"
echo "== done at $(date -u +%H:%M) UTC"
grep -h "sessions passed\|: PASS\|: FAIL" "$OUT/before.log" "$OUT/after.log" | grep -v "\[" || true
