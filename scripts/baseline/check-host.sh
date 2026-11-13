#!/usr/bin/env bash
# Refuse to run the baseline on a host that does not match the pinned GPU.
# Prints the host's GPUs either way; exits 1 on a mismatch.
#
# Usage (on the box):  ./check-host.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=pins.env
source "${here}/pins.env"

command -v nvidia-smi >/dev/null || { echo "check-host: no nvidia-smi; the baseline needs ${BASELINE_GPU_COUNT}x ${BASELINE_GPU_NAME}" >&2; exit 1; }

gpus="$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits)"
echo "GPUs on this host:"
echo "${gpus}" | sed 's/^/  /'

count="$(echo "${gpus}" | grep -c .)"
matching="$(echo "${gpus}" | awk -F', ' -v n="${BASELINE_GPU_NAME}" -v m="${BASELINE_GPU_MEMORY_MIB}" '$1 == n && $2 == m' | grep -c . || true)"
if [ "${count}" != "${BASELINE_GPU_COUNT}" ] || [ "${matching}" != "${BASELINE_GPU_COUNT}" ]; then
  echo "check-host: MISMATCH — the baseline is pinned to ${BASELINE_GPU_COUNT}x ${BASELINE_GPU_NAME} (${BASELINE_GPU_MEMORY_MIB} MiB)." >&2
  echo "  A run here is not a replicate of the baseline. Rent the pinned GPU (README.md)." >&2
  exit 1
fi
old="$(echo "${gpus}" | awk -F', ' -v d="${BASELINE_MIN_DRIVER_MAJOR}" '{split($3, v, "."); if (v[1] + 0 < d + 0) print $3}' | head -1)"
if [ -n "${old}" ]; then
  echo "check-host: driver ${old} is older than ${BASELINE_MIN_DRIVER_MAJOR}; the pinned image (CUDA 13.0) will not start." >&2
  exit 1
fi
echo "check-host: OK — ${BASELINE_GPU_COUNT}x ${BASELINE_GPU_NAME} (${BASELINE_GPU_MEMORY_MIB} MiB)"
