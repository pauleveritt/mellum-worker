# Portable rig and the Vanilla floor — design

**Cycle:** LC.39 (infrastructure). **Date:** 2026-11-05.
**Inputs:** [baselines and remedies audit](../research/2026-11-05-baselines-and-remedies-audit.md),
[preregistration](../research/2026-11-05-portable-floor-preregistration.md).

**Dated decision, 2026-11-05.** The first draft kept the LC.33 Docker
containment, with the controller on the Mac. The user then dropped Docker
from the rig. The controller moves to the inference host and runs natively.
Isolation comes from a disposable machine, an unprivileged session user and a
sweep between sessions. This document describes the design after that change.

## Intent

Every comparison the project wants next stands on a Vanilla Pi floor that
does not exist on the current rig. The audit found no Vanilla-only cohort
scored on the usable rule, so the acceptance screens LC.34–LC.38 have no
floor beneath them. The obvious fix, another cohort on the M5 Max, is too
slow to repeat. The rented GPUs that would make it fast (Runpod, Vast.ai)
cannot promise the same card twice.

This cycle therefore builds a rig that lets a session run on any qualified
machine and still count. Then it collects the floor on it. The rig rests on
one idea: **pin the software, qualify the hardware, and stop letting speed
decide outcomes.**

- **Pin the software.** The pin card fixes one llama.cpp build, one weights
  file, one set of server flags and sampling, and one tool bootstrap. That
  bootstrap covers Node, Pi, uv, Python, the dependency venv and the
  checkers. The card also fixes one acceptance package, all by hash or
  exact version.
- **Qualify the hardware.** Any allowlisted GPU may serve, if it passes a
  conformance check on that rental before any counted session. The result is
  a host card that every run record links to. The GPU becomes a recorded
  covariate, not a control.
- **Stop letting speed decide outcomes.** Sessions are limited by provider
  requests and output tokens, enforced at a local proxy. Wall clock is a
  safety net only, and hitting it makes a session invalid, not failed.

**Why this works, as a hypothesis.** We sample at temperature 1.0, so
trajectories diverge between sessions even on one host. The contained H100
cohort had twelve identical first payloads and different later trajectories.
Floating-point differences between GPUs are plausibly small next to that
noise. Speed is the difference that matters, because the old 600-second
deadline gave a fast host more turns. The floor tests the hypothesis on two
GPU generations (§7).

## Goals

1. One **pin card** that every host serves and bootstraps from. It replaces
   the two pin sources that disagree today:
   - `scripts/baseline/pins.env` (A6000, vLLM-era, Pi 1.3.0);
   - the Runpod freeze `config.json` (b11669, Pi 1.4.0).
2. A **native bootstrap** that installs the pinned tools on a fresh Linux
   pod. The bootstrap replaces the contained image.
3. A **conformance check** that writes a host card per rental.
4. **Session budgets** enforced at a local inference proxy, replacing the
   wall-clock deadline as what ends a session.
5. **Native isolation**: an unprivileged session user, a separate grading
   user, and a sweep between sessions.
6. **Renting by approval**: the rig never rents; Runpod's MCP does, on the
   user's yes per rental.
7. **The Vanilla floor**, under the
   [preregistration](../research/2026-11-05-portable-floor-preregistration.md).

## Non-goals

- Docker anywhere: in the package, in the rig, or on the pod.
- Concurrent sessions on one host. Parallelism comes from more rentals.
- Any worker, preset or remedy arm. The thin-worker arm is the next cycle on
  this rig.
- Changing the model, quant, sampling, per-request output limit, context, the
  acceptance package or the hidden oracle.
- Medium or hard suites, or rewriting LC.31–LC.38 records, whose timing and
  budgets stay incomparable with this floor.

## Anti-goals

This cycle fails, even if every check passes, if any of these happens:

- A host that failed conformance contributes a counted session.
- A session's outcome depends on how fast its host was. Any session that
  ends on wall clock and is counted as a model failure is such a case.
- A session can reach anything of the user's: a file, process, port or
  credential.
- A per-host difference is pooled away without being reported.
- Any instruction, unit or package names a suite answer.

## Constraints

- **The controller runs on the inference host.** Pi, the tools, the proxy,
  the acceptance probe and grading run natively on the same machine as
  llama-server, so no tunnel carries inference. The repository is checked
  out on the host at the cohort's pinned commit. On the Mac host it is this
  checkout.
- **Unchanged:** Pi 1.4.0, the 180-second open-tool-call cutoff, the
  recorder, relay-reconciled accounting, and acceptance package
  `af4122164322e6446b5cb12728693ca32749fdaec2606aa35e1bcaf9e41e3dd9`. Its
  `checker.py` and manifest are untouched, so the hash holds. Only the probe
  that runs candidate code moves from a container to a native user.
- **Test-first**, with every test shown failing first. Qualification uses the
  existing fake provider.
- **Measured-settings rule.** Two changes are recorded here and in the
  preregistration, and apply only to cohorts collected under this design:
  - budgets replace the wall-clock deadline;
  - native isolation replaces containment.

## The design, as decided

### 1. Pin card

One machine-readable file. Changing any value makes a new rig, not a
replicate.

- **Weights.** HF revision `4159d684ffdb09ba89dc2a58feb3e75c54eef036`,
  `Mellum2.1-12B-A2.5B-Thinking-Q4_K_M.gguf`, SHA-256
  `ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755`.
- **Build.** llama.cpp b11669, commit `620d2225c`. Metal on the Mac. CUDA
  for every allowlisted generation, with `GGML_NATIVE=OFF`.
- **Server flags.** The frozen set used in LC.34–LC.38:
  - `-c 100000 -np 2 --no-kv-unified --jinja --cont-batching`;
  - `-b 512 -ub 512 -ctk q8_0 -ctv q8_0 -ngl 999 -lv 4`;
  - 50,176 tokens per slot; threads are recorded, not pinned.

  One change: `-fa auto` becomes `-fa on`, because `auto` may resolve
  differently per GPU and the quantized V cache depends on it. Two slots stay
  pinned so the server matches the frozen set, though only one session uses
  them at a time.
- **Client.** `[tool.mellum]` as today: temperature 1.0, top-p 0.95,
  top-k 20, `max_tokens` 16,384.
- **Bootstrap.** These are the versions the contained image pinned:
  - Node 24.22.1, by per-platform SHA-256;
  - uv 0.11.6 and Python 3.14.2;
  - Pi `@earendil-works/pi-coding-agent@1.4.0`;
  - the frozen dependency project, the Easy suite's `pyproject.toml` and
    `uv.lock`, synced with `--frozen`;
  - ruff 0.16.3, complexipy 8.3.0, pyrefly 1.2.0, and pytest at the suite's
    pinned version;
  - `procps`, `lsof` and `git` from the distribution.
- **The acceptance package and the hidden oracle**, by hash.
- **Allowlist.** CUDA compute capability 8.0 or newer, one GPU, a driver
  floor matching the build's CUDA, Linux x86_64. Memory is not pinned. The
  conformance check proves both slots hold full context.

`pins.env` and its vLLM baseline stay as they were, with a pointer to the
new card.

### 2. Conformance check and host card

The check runs on every rental and on the Mac, before any counted session
there and again after the last one. It writes `host-card.json`. A host that
fails any item contributes nothing.

- **Identity.** The server reports the pinned build, model hash and flags,
  and its chat template hash matches.
- **Capacity.** Both slots hold a full-context request.
- **Protocol.** A tool-call round trip and the reasoning split work, and
  `max_tokens` is honoured as sent. LC.31 found native Pi clamping it on
  eight requests.
- **Numerics.** Perplexity from the same build over a fixed text, within a
  tolerance of the reference host. This catches a wrong quant, template or
  kernel without demanding bitwise equality, which GPUs cannot give.
- **Throughput.** Prefill and decode tokens per second, recorded, not gated.
- **Stability.** A short back-to-back burst returns zero resets and zero 5xx
  responses.
- **Tooling.** Every bootstrap version reads back as pinned.
- **Isolation.** The session user cannot do any of the following:
  - signal the server or the controller;
  - read the server's files, the controller's files or any credential;
  - write outside its own home.

  After a sweep, no session-user process or listener remains.

The card also records the GPU name, VRAM, driver, CUDA, provider, region,
rental id and price, and the stopped state once the rental ends.

### 3. Session budgets and the proxy

The relay keeps its host half and gains a **proxy mode**. It listens on a
loopback port for the session and forwards to llama-server. The proxy adds
exactly one field to a forwarded request, `stream_options.include_usage`, and
records that it did. It changes nothing the model reads, and it forwards
response bytes unaltered. Per session it counts provider requests and output
tokens, and it refuses to forward once either limit is reached. A refused
session ends with completion class **`budget`**.

| Limit | Value | Why this value |
| --- | ---: | --- |
| Provider requests | 120 | above every observed single-attempt session; max seen 102 |
| Output tokens, all requests | 64,000 | roughly what 600 s bought on the M5 Max (G1: 61,071 in 600.7 s) |
| Per-request `max_tokens` | 16,384 | unchanged pin |
| Open tool call | 180 s | unchanged; runs where the session runs |
| Wall clock | 3,600 s | safety net only; hitting it makes the session **invalid** |

A request whose usage never arrives counts as 16,384 toward the budget. It is
reported as unknown, never zero.

**Bypass is detected, not prevented.** Without a network namespace, a session
could call llama-server's port directly. The existing reconciliation compares
server-log generations with proxy-created requests. Any generation the proxy
did not create makes the session **invalid**.

### 4. Native isolation

These rules apply on a pod:

- **The disposable machine is the main boundary.** A fresh pod holds nothing
  of the user's, which removes the November 3 failure mode.
- **Session user.** Each session runs as `mellum-session`, an unprivileged
  account with its own home. The run directory and workspace live there.
  llama-server, the proxy and the controller run as root. Pi starts through
  `Popen(user=…)`, so no sudo is involved.
- **Grading user.** The acceptance probe and the hidden grader run as
  `mellum-grade`, on a fresh copy of the workspace, never on the session's
  own tree.
- **Sweep.** After each session, and after each grading step, the sweep does
  three things:
  - kills every process the user owns, after the existing group and
    workspace sweeps;
  - checks that no listener remains;
  - deletes and recreates the user's home.

  A sweep that cannot clear the user stops the host before the next session.
- **One session at a time per host.** Two sessions would collide on the
  app's startup port.

The Mac is different. It has no second user, so sessions run as the
operator's account. A preflight fails the session if any listener the sweep
would touch already exists, and the existing sweeps run after it. Its
records are flagged `uncontained`. That is acceptable only because the Mac
is descriptive in the preregistration.

### 5. Running a cohort on a pod

The operator works from the Mac over SSH, in a visible Terminal tab, as the
mellum-dev skill requires. On each pod, in order:

1. Check out the repository at the cohort's commit.
2. Run the bootstrap, build llama.cpp and fetch the weights.
3. Start the server.
4. Run the conformance check, then the cohort.
5. Run the post-check.
6. Copy the batch back to the Mac.

The driver runs inside `tmux` on the pod, so a dropped SSH connection does
not stop a session. It appends its state to the batch, so `run` resumes
without recounting. The watcher follows the newest trace over SSH.

### 6. Renting, by approval

The user decided on 2026-11-05: **ask before each rental.** There is no
standing authority and no spend cap the rig may rent within.

- Before each rental, the operator states the GPU model, provider, region,
  price per hour, expected hours and which host it serves. The operator rents
  only on the user's yes in chat. A replacement after a lost instance is a new
  rental and needs its own yes.
- **Runpod through its MCP** is the orchestration path, with the same
  capacity, template, create, get, logs and stop calls as the
  [2026-11-03 setup](../research/2026-11-03-runpod-qualification.md). The
  MCP must be connected in the session that runs the cohort.
- **Stopping is part of the rental.** After the post-check and the copy back,
  the operator stops the pod and reads back its state. That state goes in the
  host card, along with any storage still billing. Terminating is the user's
  call.
- **Vast.ai** stays a fallback under the same rules, set up by hand.
  `scripts/baseline/baseline.py` is not generalised in this cycle.

### 7. The floor, and the portability reading

The floor is defined in the
[preregistration](../research/2026-11-05-portable-floor-preregistration.md).
It is Vanilla plus the recorder on Easy Phase 1, with n = 6 on each of two
CUDA generations and n = 3 on the Mac. It is scored by the acceptance package
in observe-only control mode, the way the selective arms of LC.34 and LC.35
were. Tables report per host first, then pooled.

Whether later cohorts may pool across hosts follows the preregistered rule.
Whatever it says, every later **comparison** runs its arms interleaved on
each host it uses, so host differences cancel within a host.

## Left to the builder

- File names and formats for the pin card, host card and batch state.
- How the proxy reads usage, from stream `usage` or `timings`, as long as it
  is reconciled against the server log afterwards.
- The perplexity text and tolerance. Both are set by calibration on the Mac
  and the first CUDA rental, and recorded before any counted session.
- How the bootstrap installs distribution packages on the pod's base image.
- How the native probe provisions the dependency venv for `mellum-grade`, as
  long as the venv is the frozen project and read-only to that user.

## Builder's calls, marked as such

These are defaults I chose, not the user's decisions:

- The budget values in §3, from the LC.34–LC.38 per-session distributions and
  the M5 Max's observed throughput.
- `-fa on` in place of `auto`.
- Perplexity as the numerics check, not greedy token agreement, which cascades
  after the first difference.
- The Mac as the perplexity reference, as the one host that never goes away.
- Bypass of the proxy detected by reconciliation rather than prevented.
- A host is a GPU model under one pin card, not a single rental; the
  preregistration has the rules for a lost rental.
- The driver in `tmux` on the pod, operated from a visible Terminal tab.
- Vast set up by hand, verified datacenter offers only.
