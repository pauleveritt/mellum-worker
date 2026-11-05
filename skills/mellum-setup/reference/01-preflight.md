# Phase 1: Preflight

Checks, in order. Stop at the first failure and tell the user what it needs.

1. `llama-server --version` succeeds and the build is new enough for Mellum
   (llama.cpp learned the mellum architecture in build 9482; the repo was
   tested on 11669). `uv run scripts/backend.py status` will also say when the
   build is too old. If `llama-server` is missing, point the user at
   [`docs/backends/llamacpp.md`](../../../docs/backends/llamacpp.md) to install
   it (on Linux/macOS/Windows), or run the repo's `bash install.sh`.
2. `node --version` is 24 or newer; the setup scripts and the CLI need it.
3. `uv --version` succeeds; the server helper runs through `uv`.
4. Free disk: `df -h ~ | tail -1`. The Q4_K_M weights are about 7.7 GB.

This path works on Linux, macOS and Windows. Done.
