#!/usr/bin/env bash
# Serve the pinned model with the pinned flags, in the foreground. Run inside the
# pinned vLLM image (BASELINE_VLLM_IMAGE), which provides `vllm`. Refuses a vLLM
# other than the pinned version, and a host other than the pinned GPU.
#
# baseline.py copies this, check-host.sh and pins.env to the box and starts it.
# Usage (on the box):  ./serve.sh     # foreground; logs to the terminal
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=pins.env
source "${here}/pins.env"

"${here}/check-host.sh"

version="$(python3 -c 'import vllm; print(vllm.__version__)')"
if [ "${version}" != "${BASELINE_VLLM_VERSION}" ]; then
  echo "serve: vLLM ${version} is not the pinned ${BASELINE_VLLM_VERSION}; use ${BASELINE_VLLM_IMAGE}" >&2
  exit 1
fi

exec vllm serve "${BASELINE_MODEL_REPO}" \
  --revision "${BASELINE_MODEL_REVISION}" \
  --served-model-name "${BASELINE_SERVED_NAME}" \
  --dtype "${BASELINE_DTYPE}" \
  --max-model-len "${BASELINE_MAX_MODEL_LEN}" \
  --gpu-memory-utilization "${BASELINE_GPU_MEMORY_UTILIZATION}" \
  --seed "${BASELINE_SEED}" \
  --reasoning-parser "${BASELINE_REASONING_PARSER}" \
  --enable-auto-tool-choice --tool-call-parser "${BASELINE_TOOL_CALL_PARSER}" \
  --host 127.0.0.1 --port "${BASELINE_PORT}"
