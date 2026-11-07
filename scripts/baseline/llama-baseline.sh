#!/usr/bin/env bash
# Vanilla baseline on llama.cpp — the server the learner actually runs.
#
# Serves N llama-server instances for one GGUF quant, then runs the eval suites
# (easy/medium/hard) at n reps, vanilla Pi + recorder only (the `bare` arm),
# spreading the suites across the servers so they run in parallel. Collects the
# run records; promote the kept ones into evals/baseline/ afterwards.
#
# Runs anywhere llama-server + uv + pi are on PATH: this Mac, or a rented GPU
# box over ssh. It does NOT provision the box — rent/ssh/fetch stays the rig's
# job; this is the serve-and-measure core, on llama.cpp, never vLLM.
#
# Options (all have defaults):
#   --quant   q4|q8|bf16   GGUF quant to serve           (default q4)
#   --servers N            parallel llama-servers         (default 3)
#   --suites  "easy medium hard"  suites to run           (default all three)
#   --repeat  N            reps per suite (the n)          (default 3)
#   --deadline S           per-session deadline, seconds   (default 1800)
#   --stall   S            stall cutoff, seconds           (default 120)
#   --ngl     N            GPU layers (999 = all)          (default 999)
#   --ctx     N            context per server              (default 50000)
#   --port-base N          first server port               (default 8002)
#   --out     DIR          collect runs here      (default runs/baseline-<quant>-<stamp>)
#   --dry-run              print the plan and exit
#
# VRAM fit on a 48 GB A6000: Q4 ~7.5 GB (3 servers ✓), Q8 ~12 GB (3 ✓, tight),
# BF16 ~24 GB (1 server only — pass --servers 1 --quant bf16).
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

quant=q4; servers=3; suites="easy medium hard"; repeat=3
deadline=1800; stall=120; ngl=999; ctx=50000; port_base=8002; out=""; dry=0
while [ $# -gt 0 ]; do
  case "$1" in
    --quant) quant="$2"; shift 2 ;;
    --servers) servers="$2"; shift 2 ;;
    --suites) suites="$2"; shift 2 ;;
    --repeat) repeat="$2"; shift 2 ;;
    --deadline) deadline="$2"; shift 2 ;;
    --stall) stall="$2"; shift 2 ;;
    --ngl) ngl="$2"; shift 2 ;;
    --ctx) ctx="$2"; shift 2 ;;
    --port-base) port_base="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --dry-run) dry=1; shift ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$quant" in
  q4)   hf="JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M" ;;
  q8)   hf="JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q8_0" ;;
  bf16) hf="JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:BF16" ;;
  *) echo "unknown quant: $quant (q4|q8|bf16)" >&2; exit 2 ;;
esac
alias_name="Mellum2.1-12B-A2.5B-Thinking"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
[ -n "$out" ] || out="runs/baseline-${quant}-${stamp}"
suites_dir="learn/code/suites"
work="$(mktemp -d)"
pids=()

echo "== llama.cpp baseline =="
echo "  quant:    $quant  ($hf)"
echo "  servers:  $servers  (ports ${port_base}..$((port_base+servers-1)))"
echo "  suites:   $suites   repeat (n): $repeat"
echo "  budget:   ngl=$ngl ctx=$ctx deadline=${deadline}s stall=${stall}s"
echo "  out:      $out"
[ "$dry" = 1 ] && { echo "(dry run)"; exit 0; }

cleanup() { for p in "${pids[@]:-}"; do kill "$p" 2>/dev/null || true; done
            pkill -f "llama-server .*${alias_name}" 2>/dev/null || true
            rm -rf "$work"; }
trap cleanup EXIT INT TERM
mkdir -p "$out"

# 1. Start the servers and wait for health.
for i in $(seq 0 $((servers-1))); do
  port=$((port_base+i)); log="$out/server-${port}.log"
  echo "starting llama-server on :$port ..."
  llama-server -hf "$hf" -a "$alias_name" --host 127.0.0.1 --port "$port" \
    -ngl "$ngl" -c "$ctx" -np 1 --jinja -fa auto -b 512 -ub 512 \
    -ctk q8_0 -ctv q8_0 >"$log" 2>&1 &
  pids+=($!)
done
echo "waiting for health (first run downloads the GGUF)..."
for i in $(seq 0 $((servers-1))); do
  port=$((port_base+i))
  for _ in $(seq 1 1800); do
    curl -s -m 3 "http://127.0.0.1:$port/health" 2>/dev/null | grep -q '"status":"ok"' && break
    sleep 1
  done
  curl -s -m 3 "http://127.0.0.1:$port/health" 2>/dev/null | grep -q '"status":"ok"' \
    || { echo "server :$port never became healthy — see $out/server-$port.log" >&2; exit 1; }
  echo "  :$port up"
done

# 2. A Pi profile per server (same pins, different baseUrl/port).
make_profile() {   # $1 port -> echoes the profile dir
  local port="$1" dir="$work/profile-$port"
  cp -R learn/code/profile "$dir"
  rm -rf "$dir/sessions" "$dir/bin" "$dir/auth.json" "$dir/trust.json" 2>/dev/null || true
  uv run python - "$dir/models.json" "$port" <<'PY'
import json, sys
p, port = sys.argv[1], sys.argv[2]
m = json.load(open(p))
for prov in m.get("providers", {}).values():
    prov["baseUrl"] = f"http://127.0.0.1:{port}/v1"
json.dump(m, open(p, "w"), indent=2)
PY
  echo "$dir"
}

# 3. Run each suite on a server (round-robin), in parallel.
run_pids=(); i=0
for suite in $suites; do
  port=$((port_base + (i % servers))); i=$((i+1))
  profile="$(make_profile "$port")"
  echo "running $suite x$repeat on :$port ..."
  ( uv run python learn/code/harness.py run \
      --suite "$suite" --suites-dir "$suites_dir" --arm bare --grade \
      --repeat "$repeat" --deadline "$deadline" --stall "$stall" \
      --profile "$profile" --runs-dir "$out" \
      >"$out/${suite}.log" 2>&1
    echo "=== $suite done ===" ) &
  run_pids+=($!)
done
wait "${run_pids[@]}"

# 4. Summary.
echo; echo "== results ($quant) =="
for suite in $suites; do
  echo "--- $suite ---"; grep -hE "^(easy|medium|hard):|passed|requests|turns|wall" "$out/${suite}.log" 2>/dev/null | tail -8
done
echo; echo "records under: $out   (promote the kept ones into evals/baseline/)"
