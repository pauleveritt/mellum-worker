# Vanilla Pi Easy reference — 2026-11-03

Six sequential Easy sessions, Vanilla Pi 1.4.0 plus the recorder only. Mellum
inference ran on Runpod's NVIDIA RTX PRO 4500 Blackwell (32 GB); Pi, generated
apps and post-run graders ran on the Mac (Apple M5 Max, 128 GiB). The Mac GPU
was not the inference backend for these sessions.

Four artifacts passed all hidden checks; all six passed code health. Two
sessions settled normally and four stalled. Only one session both passed all
hidden checks and settled. Read [the scorecard](scorecard.md) for all six outcomes.
Hidden-check success,
code health and session completion are independent facts. A correct artifact
can belong to a stalled session; normal settlement can leave an unusable app.
This is a local reference sample, not a worker comparison or a precise rate
estimate. No unsuccessful model attempt was replaced.

## Collection and provenance

The instrument was committed and verified at
[`e54b6f1`](https://github.com/pauleveritt/mellum-worker/commit/e54b6f1f40a9dceca6b35081428dbf43a57ce6d4)
before collection. The canonical command was:

```bash
caffeinate -dimsu uv run python learn/code/harness.py baseline
```

Full console output was retained. The collector paused after attempts 1 and 6 for
explicit review of recovered connection errors, then resumed the same batch
with `--resume`, `--count <run-id>` and the evidence-based `--reason` stored
in [batch.json](batch.json). This changed accounting only. No model, profile,
limits, suite, grading, worker or remedy changed during collection.

[batch.json](batch.json) freezes hashes of the instrument, recorder, suite,
grader, profile, Pi entry point, backend runtime libraries and weights. Its
attempt list is the final accounting record. The nested backend
`freeze.collection` is the earlier qualification snapshot, not a live counter.
[verification.json](verification.json) records per-run runtime, request settings,
profile checks, cleanup and native settlement. Per-run folders retain compact
records and complete checker output. [qualification.json](qualification.json)
records the Easy grader's known-good pass and known-broken failure.

The shared server used llama.cpp build 11669, commit `620d2225c`, Q4_K_M weights
(SHA256 `ecc4d5b8107fc219e23c494b2d107552137637b6c6002ee713e0ba8af7fa2755`),
q8_0 K/V cache, full GPU offload and two separate context slots (50,176 tokens
each). Counted sessions ran one at a time with cold context: fresh Pi history
and profiles, not a flushed backend prompt/KV cache. The server stayed running.
The client context was 50,000; output ceiling 16,384; temperature 1, top-p .95
and top-k 20. Input and output share the context budget. Native Pi further
clamps each request to `min(16384, max(1, 50000 - estimated_context - 4096))`.
Eight requests in attempt 2 used lower limits (3,363–8,176). All 91 requests
match that native calculation exactly; see
[native-max-tokens-verification.json](native-max-tokens-verification.json).
Its supplemental runtime hashes were captured after collection, not during
preflight. Later comparisons must preserve the same native Pi policy.
Model requests went through Mac loopback 8002
and SSH to Pod loopback 18001. The unrelated local server on 8001 was unused.

Actual runtime was Node 24.22.1; the path is retained in
[runtime-observations.json](runtime-observations.json). The only loaded extension
was a byte-identical copy of `extensions/mellum-recorder.ts`; context files,
skills, prompt templates and other extensions were disabled. Fresh workspaces
and private profiles were used. The deadline was 600 seconds and the cutoff
was a tool call open for 180 seconds, regardless of its output.

The legacy `run.json.nudges` diagnostic counts continued empty/error turns;
it does not establish that a nudge remedy was loaded. The launch records and
recorder hash establish the recorder-only configuration here.

Hidden graders were installed after execution and verified cleanup. Source
and tests establish that ordering; retained timestamps and supplemental live
absence observations support it. All owned workspace processes were gone
before grading and after collection. Checkers were Ruff 0.16.3 (F,E9),
Complexipy 8.3.0 (threshold 10), pytest 8.3.4 and advisory Pyrefly 1.2.0.

## Classification and limits

Attempt 1 recovered from two `Connection error.` responses (requests 6 and 16)
and reached native, non-aborted settlement without an added recovery remedy.
It passed all four hidden checks and code health. The exact transport cause
was not established; no backend failure was observed in the retained log.
The attempt counts and retains the errors. Its total output tokens are
**unknown** because the error responses lack trustworthy usage. A partial sum
is not a total, and no six-run total or mean output budget is claimed.

Attempt 6 recovered from a connection error on request 14, continued through
requests 15–20, then stalled on its foreground server call. It passed all hidden
checks and health. It also counts with **unknown** total output tokens. Neither
error-affected attempt was discarded or rerun.

Attempt 3 settled after creating `main.py` while omitting the required `app.py`.
The hidden checker launched but could not import the app; its four checks did
not run. This is a retained model failure, not a checker startup failure or a
proven infrastructure exclusion. Passing code health does not establish
functional correctness. Foreground-server stalls remain counted and were not
unblocked so that coding could continue.

All six attempts are counted; there are no excluded or replacement attempts.
Only Easy Phase 1, one model, one GPU/backend and this host/runtime are covered.
No claim is made about other suites, the worker, remedies or parallel full
sessions. The earlier two-slot synthetic pilot qualified protocol/memory only.

## Related cleanup verification

The existing workspace sweep reaped model-started servers outside Pi's own
process group; this collection verified no owned process or app-port listener
remained. Startup ownership recovery and shared locking add the interrupted-run
safeguard. The resolved backlog entry about missing those servers was removed.

The separate macOS backend test-fixture failure was reproduced: a relocated
`/bin/sleep` was killed before process lookup. Ad hoc signing only the temporary
fixture made the real backend lifecycle checks pass (11/11); production backend
code was unchanged. This does not resolve the older hosted-runner skip.

## Raw evidence and reuse

Raw traces, session logs, stdout and final workspaces stay outside Git. Their
research release, archive hashes and retrieval instructions are in
[raw-evidence.json](raw-evidence.json). Archives preserve the complete retained
batch, console, qualification evidence and instrument verification logs.
Virtual environments are included as retained artifacts; absolute paths and
symlinks mean they are not portable environments. Use the lockfiles and pinned
runtime/checkers to reproduce them.

Reuse this reference when changing only the worker/remedy. Before comparison,
verify compatible task, oracle, runtime, instrument, model/weight hash,
backend/build settings, limits, concurrency and relevant host environment
against the manifest. Same model ID alone is insufficient. Load and cache
state limit elapsed-time comparisons. These are independent sessions, not
paired trials, and the sample is too small for precise rate claims.
