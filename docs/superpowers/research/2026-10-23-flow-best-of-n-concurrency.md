# Flow best-of-N concurrency — what `--concurrency` actually buys

Date: 2026-10-23 (back-dated to when the throughput curve was measured and the
flags were wired; note written up 2026-10-26). Status: measured curve +
reasoned decision on how to spend it.

## What is measured

- **oMLX batched-engine aggregate throughput is sublinear in N.** On the M3 Max
  (48 GB), Mellum 2.1 6-bit, short 160-token requests: 127 tok/s at N=1 → 314 at
  N=8 (2.45×), with the knee at N=4–8 (beyond that latency rises fast for little
  extra throughput). The engine loads `engine: batched`, so concurrent requests
  share forward passes; a single request does NOT get faster. RSS ~9.5 GB for
  short requests; long generations grow the KV cache.
- **KV cost per request ≈ 6 MB per 64-token block** (ChunkedKV), so a 40k-token
  window is ~3.5 GB of KV per in-flight request. N is therefore KV-bounded:
  ~5–6 concurrent at a 40k window under a 40 GB oMLX ceiling; more at a smaller
  window.
- **The flags exist and are wired:** `flow_run --concurrency N`,
  `--retry-concurrency M`, and `round_concurrency(rnd, N, M)` — the first round
  runs at N, retry rounds (1+) escalate to M.

## What is conjecture (the reasoning on top of the curve)

- **best-of-N buys throughput, not latency.** One flow attempt is a dependent
  chain (plan → examine → code → review → test) that runs serially at the
  model's decode rate (~80 tok/s for both Mellum and Qwen3-Coder-4bit here).
  Concurrency runs N *independent* attempts of the same phase in parallel and
  takes the first that passes — it never shortens a single attempt.
- **4× concurrency ≈ 2–2.5× aggregate throughput, not 4×** (from the curve), so
  4 parallel attempts finish in roughly the time of ~2.
- **The wall-clock win is variance reduction on HARD phases only.** A phase that
  needs, say, 3 sequential retry rounds at N=1 can pass in ONE parallel round of
  4 — trading compute for wall-clock exactly where retries happen. A phase that
  passes first-try gets ZERO wall-clock gain; there, concurrency is pure wasted
  compute.
- **So the efficient config is escalate-on-retry:** `--concurrency 1
  --retry-concurrency N`. One cheap attempt first (most phases pass), best-of-N
  spent only on phases that actually retry (the hard ones). A flat
  `--concurrency N` wastes compute on every first-try pass.
- A separate observation: the larger speed lever was often the SMALLER context
  window (leaner KV per request, faster) rather than higher N.

## What would falsify this / Risks

- **Falsified** if hard phases do not actually benefit from best-of-N — i.e. if
  a phase fails for a deterministic reason (a grounding ceiling) rather than
  sampling variance, N parallel attempts all fail the same way and the compute
  is wasted with no wall-clock win. Watch whether retried phases pass more often
  under best-of-N than under sequential retries at the same total budget.
- The throughput curve is from short 160-token requests; long `code`-step
  generations may scale differently (more decode-bound, so the batched sharing
  may help less).
- The KV math assumes the full pinned window; realized KV depends on the context
  a phase actually reaches, so the practical N ceiling may be higher than the
  worst-case estimate.

The serve flags behind the curve are in `docs/backends/omlx.md`; the
`round_concurrency` / escalate-on-retry wiring is in `learn/code/flow_run.py`.
