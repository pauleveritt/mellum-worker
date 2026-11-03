# Runpod inference setup and configuration freeze

**Date:** 2026-11-03
**What is measured:** one allocated GPU, its runtime identity, the container
configuration, weight hash, two-slot synthetic requests and tool-call protocol.
**What is conjecture:** full-session reliability and any benefit to evaluation
throughput. No counted sessions have run.

## Scope and decision

Qualify one inference host before collecting the Vanilla baseline or Worker
comparison. Retain the same GPU class, backend revision, weights, precision,
per-session context, sampling, and serving settings for both arms. Changes to
those inputs require another setup check and an explicit comparability decision;
do not substitute an available GPU silently.

The requested concurrency-two pilot is an infrastructure screen. The approved
Easy collection remains six sequential sessions with fresh Pi contexts,
600-second deadlines and a 180-second open-tool-call cutoff. Two server slots
do not authorize overlapping counted sessions. No harness implementation or
suite collection is part of this setup work.

## Evidence so far

- Runpod MCP authentication succeeded; `list-pods` was empty before allocation.
  Earlier RTX 4090 and RTX PRO 4500 create calls failed with a capacity error.
  A later capacity read and create succeeded. Availability is not allocation.
- `get-pod` read-back confirms Secure Cloud, EU-RO-1, one RTX PRO 4500 Blackwell,
  20 GB container disk, a 50 GB persistent `/workspace`, and only `22/tcp` in
  the requested exposed-port configuration. The API reports $0.72/hour for
  the running Pod; storage charges are not independently quantified here.
- SSH `nvidia-smi` confirms 32,623 MiB VRAM, driver 595.91.07, and compute
  capability 12.0. `/usr/local/cuda/bin/nvcc` reports 12.8.93. The CUDA toolkit
  is absent from the SSH shell's default PATH, so the build adds it explicitly.
- The official `runpod-torch-v280` template resolves to
  `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`. Container boot logs report
  digest `sha256:0a360022e8de4375af99430f84e8b38951acc397252163a37ceac7204d01be35`.
- Hugging Face repository revision
  `4159d684ffdb09ba89dc2a58feb3e75c54eef036` resolves the non-MTP
  `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf` to 8,071,295,264 bytes and SHA-256
  `ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755`.
  The remote download passed `sha256sum --check`.
- Source tag b11669 resolves to
  `620d2225cc436ab0b001e3200e590e3b286ef9ab`, matching the Mac's llama.cpp
  revision. CUDA Release build configuration selects architecture 120a;
  `GGML_NATIVE=OFF`. The completed binary reports build 11669, commit 620d2225c.

## Qualification result and freeze (2026-11-03)

The [shared configuration](2026-11-03-runpod-qualification/config.json) is frozen
for the infrastructure screen. It records exact runtime checksums, model hash,
hardware, build options and effective client settings. The adjacent build and
launcher scripts preserve the executed recipe. This does not start collection
or change the approved sequential evaluation design.

Two slots processed requests simultaneously in both a short pair and a long
pair. Each long request reported 47,034 prompt tokens and generated 64 tokens,
ending at the intentionally small output limit; the pair completed in 10.134 s.
The short pair generated 80 and 93 tokens with normal stops. A required
`read_file` tool call returned valid arguments. Post-probe health was `ok`, with
both slots idle. One-second GPU samples peaked at 9,042 MiB of 32,623 MiB.
This is a sampled peak, not an allocation upper bound.

The requested context is 100,000 total with two separate KV slots; runtime
rounding produces 100,352 total, 50,176 per slot. The client context remains
50,000. Input and output share this budget. Production max output is 16,384;
the probes used limits of 512 and 64, so they do not qualify sustained maximum
generation. Effective request sampling was observed as temperature 1, top-p
approximately .95, top-k 20, min-p 0 and neutral penalties. Server defaults
differ; every production request must supply the client overrides.

No coding quality, speedup, full Pi lifecycle, streaming/cancellation or
deadline-contention claim follows from this screen. Start with concurrency two
for further pilot work rather than increasing slots on memory headroom alone.
Keep counted-run concurrency identical across comparison arms.

## Setup execution notes

The first CMake generation on the network-mounted `/workspace` took 88.4 s.
It was interrupted before producing a server. The completed build uses a clean
local clone at `/tmp/mellum-llama`, with the same revision and CUDA flags plus
`CMAKE_BUILD_RPATH=$ORIGIN`; runtime binaries and checksums are copied back to
`/workspace/mellum/llama.cpp/build/bin/`. The source, weights and final runtime
remain on persistent storage. The interrupted log is retained separately.

The shallow clone needed explicit build-number/commit metadata to match the
local binary's reported identity. CMake receives architecture 120 and resolves
120a. The image's nginx already owns Pod port 8001, so inference binds only to
Pod loopback 18001. The qualification SSH tunnel maps Mac loopback 8002 to it;
only SSH is requested for public exposure. The server runs under tmux.

The repository document-cap checks pass. An unrestricted `npm test` run
reports 633/634 passing; the existing kill-by-name test at
`tests/backend-lifecycle.test.mjs:98` reports no matching test processes and
also fails in isolation. No product/test source was changed in this setup.
This is retained as an unresolved instrument check, not reported as a clean
suite or used as model evidence. The first sandboxed suite attempt additionally
hit local-socket and uv-cache permission errors; that attempt is not a product
regression result.

Raw setup logs, model metadata, scripts and completed probe responses are kept
under ignored `runs/2026-11-03-runpod-qualification/` and on the Pod under
`/workspace/mellum/`. Never commit raw traces, stdout or patches.

## Sources and interpretation

- Runpod MCP `list-pods`, `get-capacity`, `get-template`, `create-pod`,
  `get-pod`, and `stream-pod-logs`, accessed 2026-11-03: allocation, image,
  pricing and configuration observations above. SSH provides the independent
  hardware/toolkit checks. These are setup facts, not model-quality evidence.
- [Mellum GGUF repository metadata](https://huggingface.co/api/models/JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF?blobs=true),
  JetBrains / Hugging Face, accessed 2026-11-03: revision, file size and LFS hash.
- [Pinned llama.cpp source](https://github.com/ggml-org/llama.cpp/tree/620d2225cc436ab0b001e3200e590e3b286ef9ab),
  ggml-org, accessed 2026-11-03: backend source identity. Installed build help
  and runtime slot information must verify context allocation; current-master
  documentation alone is insufficient to qualify this pinned binary.

## What would falsify this

A weight/build identity mismatch, unexpected CPU offload, a smaller per-slot
context, failure to process both slots simultaneously, or failed long-prompt
requests on reuse would invalidate this infrastructure qualification.

## Risks

This is one host and a synthetic infrastructure screen, not an Easy-suite
comparison or a concurrency speedup measurement. GPU contention can change
deadline outcomes. The Mac already has an unrelated listener on port 8001;
qualification uses a loopback SSH tunnel on port 8002. Counted collection must
verify its endpoint rather than accidentally using the existing local server.
The Pod bills while running. Stopping releases the GPU; resuming or replacing
it requires checking identity and configuration before reusing the baseline.
