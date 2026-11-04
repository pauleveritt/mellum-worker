# Contained measurement and transport diagnostics

## Intent

Implement the containment and instrumentation fixes requested after the
[baseline analysis](../research/2026-11-03-baseline-deep-analysis.md). Prevent
model-written commands and application code from reaching the Mac or another
attempt, and retain enough transport/accounting evidence to diagnose failures.
No counted inference, remedy, model retuning or acceptance expansion belongs here.

## Decisions

The requested scope is host/run containment plus transport and context reporting.
The implementation choice is per-attempt Linux containers on the Mac; inference
continues on the existing Runpod backend. This is a new execution environment,
requiring a new reference; the original batches and grader stay unchanged.
The user accepts Docker for tonight only, not as the long-term solution. Keep
this an explicit temporary collection backend; the installed worker gains no
Docker dependency. A replacement must qualify the same boundary guarantees.
Existing educational native runs remain explicitly unconfined. The trusted
baseline command fails closed without the contained runner and qualification.

## Boundary

- An immutable, recorded Docker image provides Pi 1.4.0, Node 24.22.1, Python
  3.14.2, uv 0.11.6, frozen suite dependencies and pinned checkers.
- Each attempt has a separate container, private writable scratch, PID namespace
  and loopback network. Use `--network none`, no host mounts, no Docker socket,
  read-only image, non-root agent, dropped capabilities, no privilege escalation,
  and bounded memory/PIDs. Never fall back to native execution.
  Scratch uses a uniquely labeled, 1 GiB tmpfs-backed Docker volume; it has no
  host bind mount. Record ownership before creation and remove the volume with
  its container. This permits paused export, which direct `--tmpfs` does not.
- Only the attempt's prepared workspace/profile and instrument reach the agent.
  Hidden grader source is supplied only after model execution has stopped, in a
  separate grading container with the same boundary. Grading imports model code
  and therefore requires containment too.
- A host-controlled relay forwards only the pinned inference API over Docker
  exec stdin/stdout to a private container loopback listener. It does not expose
  the host network, credentials, arbitrary destinations, CONNECT or admin routes.
  Model payload bytes and SSE bytes are forwarded without retries or sampling
  changes. No macOS Unix-socket-sharing assumption is required.
- Export only regular files/directories; reject links and special files before
  host materialization, bound export size, and omit runtime caches/virtualenvs.
  Pause model processes before export; extract into a fresh staging directory
  with traversal/duplicate/collision checks, promoting only workspace and native
  evidence destinations. Host control/relay records are never replaced from
  an export. Remove the model container before grading.
  Host code never imports or executes exported application code.
- Persist exact container identity before execution; remove the whole owned
  container on exit, stall, deadline and recovery. PID/workspace sweeps do not
  establish containment. An interrupted attempt remains pending review.
  The host enforces execution/checker timeouts even if inner processes stop.

## Qualification and provenance

Before collection, qualify the exact image and policy with an unrelated host
sentinel file, process and HTTP service. Reading/writing the file, reaching the
service, signaling the process and crossing into a sibling attempt must fail;
an inherited secret environment variable must also remain absent. Container
environments are explicit allowlists, never copies of the host environment;
the sentinels must survive. Also prove ordinary workspace edits, subprocesses,
Python tests, loopback within one attempt, inference relay streaming and isolated
grading work. No inference is needed for these checks: use a local fake backend.
An unavailable Docker daemon or failing probe blocks collection.

Record image ID, platform, actual runtime versions, policy/source hashes, relay
topology, qualification results and per-attempt container identity. Reference
matching and resume must reject boundary/runtime drift and old native references.
Do not silently regenerate or reuse an earlier qualification with different inputs.

## Instrumentation

Observe native Undici diagnostics without replacing fetch, changing payloads,
reading response bodies, adding retries or swallowing application errors.
Associate transport requests with recorder request IDs when available. Retain
request creation, response headers/status, completion and error boundaries, safe
cause names/codes and timing. Never record authorization, cookies, arbitrary
headers, URL queries, free-form error messages or request/response bodies in these
additional diagnostics. Diagnostic sink failures must not change provider behavior;
they must be visible and make a trusted qualification/attempt unverifiable.

The relay separately retains a correlation ID, upstream response/stream boundaries
and safe failure codes. It returns its correlation ID as response metadata so
native client and host relay evidence can be joined. Failure injection covers
connection refusal, reset before headers, truncated SSE and valid streaming.
Transport changes are instrumented; historical error root cause remains unknown.

`context` becomes maximum full observed prompt usage, preferring associated raw
provider `prompt_tokens`, otherwise native `input + cacheRead + cacheWrite`.
Keep maximum uncached input separately. Missing/invalid evidence stays unknown;
never add already-inclusive raw prompt tokens to cache counts, combine components
from different requests, treat initialized error zeros as measured context, or
revise immutable historical records. Output completeness rules remain unchanged.
If any dispatch lacks usage, the session maximum is unknown; retain the maximum
native uncached input as a separately labeled observation.

Relay frames are limited to 2 MiB, request bodies to 16 MiB, four live requests,
64 KiB stream chunks and bounded pipe backpressure. Malformed frames, duplicate
IDs, over-limit queues and loss of the container cancel upstream work. Use a
600-second request ceiling, no retry and no caller-selected destination.

## Acceptance

Containment is implemented only when the real sentinel and functional probes pass
on this Mac, including grading and interrupted-container recovery. Instrumentation
needs failing-first regressions and an uncounted fake-provider integration check.
All repository checks pass, FIXES and changelog reflect landed changes, and a
fresh review checks the boundary before further collection. No new reference or
comparison sessions are launched by this implementation task.

## Limits

This boundary relies on Docker Desktop's VM/container isolation, not protection
against kernel or Docker vulnerabilities. Resource limits do not establish model
completion. A container platform change can affect timing and tool behavior;
it must be shared across future arms and cannot be compared as a pure remedy.
