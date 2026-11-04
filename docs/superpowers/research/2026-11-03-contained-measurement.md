# Temporary contained measurement qualification

**What is measured:** 25 real Docker boundary/functional checks on this Mac,
using a local fake provider; native Pi launch identity verified for both arms.
**What is conjecture:** historical connection-error causes and the effect of
containment on model quality or timing. No counted inference ran here.

The [forensic analysis](2026-11-03-baseline-deep-analysis.md) found actual
host-service interference. The fix is an explicit temporary measurement backend,
accepted for tonight. It adds no Docker dependency to the installed worker and
changes no remedy, grader, model setting or historical result.

## Qualified boundary

The retained [proof](2026-11-03-contained-measurement/qualification.json) records
the image ID, all source hashes, actual runtime versions, engine and policy.
The image is `sha256:3f4b3a59f4160b7fca580ffae3a65d38396afcffa38b17ce06deb8ebec6c0495`;
Docker Engine 29.9.2, Linux/aarch64, Node 24.22.1, Pi 1.4.0, Python 3.14.2,
uv 0.11.6; checkers ruff 0.16.3, complexipy 8.3.0, pyrefly 1.2.0, pytest 8.3.4.

Each attempt has private files, processes and loopback; network none, non-root,
read-only image, no host mounts/socket, dropped capabilities, no-new-privileges,
CPU 4, memory 4GiB, PIDs 256. Scratch is a uniquely owned 1GiB tmpfs-backed Docker
volume plus a 1GiB temporary directory. The host relays only fixed inference
routes over exec pipes, preserving payload/SSE bytes without retries.

All model processes are paused before safe bounded export. Host extraction
rejects traversal, links, specials, duplicates and collisions and excludes
runtime caches. Host controls live outside exported artifacts. The whole
container and volume are removed before a separate container imports model code
for grading. Host watchdogs bound inner execution and checker processes.

## Observed checks

| Probe | Result |
| --- | --- |
| Host sentinel read/write, signal and HTTP access | Blocked; file/process survived |
| Sibling private file and service | Inaccessible; sibling service survived |
| Host secret environment | Absent |
| Own edit, child process, private loopback | Worked |
| Fake streaming, pre-header reset, truncation, refusal | Correct boundaries retained |
| Native client cause codes and relay correlation | Retained |
| Native Pi Vanilla and worker | Settled; collector launch checks passed |
| Isolated known-good / known-broken grader fixtures | Accepted / rejected |
| Stopped inner process / hanging checker | Host timeout; container and volume removed |
| Host runner killed with SIGKILL | Durable ownership recovered; container and volume removed |

Local raw qualification directories `runs/2026-11-03-contained-qualification-01`
through `-04` retain failures as well as the final proof. First failures exposed
Docker archive writes to a read-only rootfs and paused exports from direct tmpfs;
trusted exec seeding and a bounded tmpfs-backed named volume solved those.
The third attempt found a relative-path bug in the recovery probe; absolute
qualification paths fixed it. The fourth passed all 25 checks. None used Runpod.

The fresh review identified four material issues: missing host watchdog,
recursive trust in exported control filenames, late relay frames after an
upstream error, and duplicate reply IDs hiding missing usage. Each received a
failing-first regression and fix. Deferred minor: the internal contained session
helper runs health checks even when `grade_run=False`; trusted collection always
uses `True`, and no educational contained CLI is exposed.

## Reuse

From the repository root, build with `uv run learn/code/containment.py build`.
Qualify using `uv run learn/code/containment.py qualify --image SHA256_IMAGE_ID
--output runs/NEW_QUALIFICATION_DIRECTORY` (one shell command). The output
directory must be new. Source, image, engine or policy drift requires a matching
new proof; collection rechecks inputs between attempts.

Once the Runpod backend has restarted and passed its independent preflight,
the baseline command accepts `--isolation-image SHA256_IMAGE_ID` and
`--isolation-qualification runs/NEW_QUALIFICATION_DIRECTORY/qualification.json`.
Collect a fresh contained Vanilla reference first, then worker with `--reference`
pointing to its completed batch. Old native batches remain historical evidence.
Do not compare native and contained timing as a pure worker/remedy effect.

Pod `adwa2g95zg24vx` was stopped through Runpod MCP and read back as `EXITED`
during this work. GPU billing stopped; the 50 GB `/workspace` disk remains and
continues storage billing. Restart may change SSH mapping or lack GPU capacity;
recheck the frozen inference configuration before collection.

Docker references: [network none](https://docs.docker.com/engine/network/drivers/none/),
[tmpfs](https://docs.docker.com/engine/storage/tmpfs/),
[volumes](https://docs.docker.com/engine/storage/volumes/).

## What would falsify this

Any host/sibling probe succeeding, mutable export, wrong runtime/source identity,
missing transport boundary, unbounded inner execution or surviving owned resource
invalidates qualification and blocks collection.

## Risks

Docker Desktop's VM/container isolation is the boundary; kernel/Docker exploits
are outside this qualification. The Linux environment changes tool behavior and
timing and needs a fresh shared reference. Docker is temporary, and its future
replacement must pass the same probes. Historical transport causes remain unknown.
