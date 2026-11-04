# A40 replacement for contained Phase 1 collection

**What is measured at registration:** an A40 Pod was created and its actual GPU,
driver and CUDA toolkit read over SSH. No new counted inference has started.
**What is conjecture:** baseline quality/budget and the bundled remedy's effect.

## Authorized change before collection

The original stopped Pod could not reacquire its host GPU. Paul authorized a
replacement, then explicitly requested another attempt on cheaper hardware after
32 GB placement requests failed and an A100 at $1.79/hour was proposed.

Fresh Secure Cloud catalog reads showed an A40 in EU-SE-1 at $0.59/hour. Pod
`icrpuerli5mgih` was created and read back RUNNING with that GPU, the same
`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` image, 20 GB container disk,
50 GB `/workspace`, SSH only and Jupyter disabled. SSH reported NVIDIA A40,
46068 MiB VRAM, driver 595.91.07, GPU UUID 251b506d-9a94-da67-924c-41d9524f4aa5,
and CUDA toolkit 12.8.93. Runpod allocated 9 vCPUs and 50 GB host memory.

The old Pod `adwa2g95zg24vx` remains stopped and its files are retained. The
replacement is rebuilt from the pinned public sources/weights; nothing is
deleted or falsely described as copied from the inaccessible old volume.

## Shared protocol

The [registered 6+6+1 study](2026-11-03-contained-phase1-study.md) is unchanged
except Pod/host/GPU/backend build target and its newly observed runtime hashes.
Build llama.cpp 620d2225c / 11669 for A40 CUDA architecture 86, with native CPU
tuning disabled. Retain the same GGUF revision/hash, two serving slots with
50k context each, cache types, sampling, configured/native output semantics,
600s deadline, 180s open-call cutoff, Pi 1.4.0, concurrency 1 and fixed oracle.

Freeze and qualify the actual new backend before any counted session, then use
it for six Vanilla, six thin Worker and one Vanilla + foreground-server/verify
prompt screen. The contained image remains
`sha256:a53fb9f0058d14e93fe3f0eb478a53ee61524034ed6a0656d73eafe70b63e7c5`,
whose 27 fake-provider qualification checks passed. No timing comparison with
the old Blackwell cohorts is a pure worker/remedy effect.

The replacement has its own shutdown guard: stop on workflow completion or a
blocking failure, or after 90 compute minutes including setup. Keep `/workspace`;
storage charges continue after stop. Do not start the old Pod or another GPU.

## What would falsify this

Unqualified hardware/runtime/weight/server drift, unexpected extensions, altered
grader, unverified cleanup or dishonest usage invalidates the affected run.

## Risks

Setup consumes the 90-minute ceiling. Capacity and throughput differ from the
original Blackwell host. The n=1 two-unit screen cannot attribute an effect or
establish a success rate. The four hidden checks do not cover the whole phase.
