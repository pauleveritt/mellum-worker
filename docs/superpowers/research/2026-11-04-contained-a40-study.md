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

## 2026-11-04 correction before resumed collection

The first A40 Vanilla attempt stalled after 199.338s on foreground Uvicorn
(14 requests, 2,221 output tokens). Its checker binaries could not launch:
Docker's `/tmp` defaulted to `noexec` while uv's cached native binaries lived
there. The prior 27-check proof checked the hidden oracle but failed to require
health-checker launch. No quality score was accepted. This attempt remains
retained in `vanilla-easy-20261104T130425Z-4162a7`, separate from the corrected
cohorts; its model stall is not erased or described as a model success.

The Pod was stopped and read back EXITED at the blocker. A failing unit
regression demonstrated the false-positive qualification gate, and a real
Docker reproduction showed mount flags and checker exit126. The corrected gate
requires all three health checkers to launch on both fixtures; it rejected the
old policy. Explicit `exec` on private `/tmp` lets uv run its cached binaries;
non-root, no network/host mounts, read-only root, nosuid/nodev and resource
bounds remain. A real Docker recheck passed for both fixtures.

The corrected image is
`sha256:4079657911571b9a008b2ce97a0195c4c827f6cadc88289605df15e927291d56`.
Its [replacement qualification](2026-11-04-contained-a40-study/qualification.json)
passed all27 checks, now including checker launch in the grader check. Use this
image for a fresh six Vanilla, six thin Worker and one bundled remedy screen;
do not mix the interrupted old-policy attempt into their rates. The original
proof remains historical and is superseded for collection. The A40 backend
freeze is [retained separately](2026-11-04-contained-a40-study/backend-config.json).

## What would falsify this

Unqualified hardware/runtime/weight/server drift, unexpected extensions, altered
grader, unverified cleanup or dishonest usage invalidates the affected run.

## Risks

Setup consumes the 90-minute ceiling. Capacity and throughput differ from the
original Blackwell host. The n=1 two-unit screen cannot attribute an effect or
establish a success rate. The four hidden checks do not cover the whole phase.
