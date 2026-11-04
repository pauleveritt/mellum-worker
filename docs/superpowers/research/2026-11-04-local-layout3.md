# Local Metal task-scoped layout screen

**What is measured:** qualification and three fresh sequential Easy Phase 1
sessions on the M5 Max, Vanilla Pi 1.4.0 plus recorder and only
`prompt/name-the-layout`, using the new once-per-task injected delivery.
At protocol writing, results were pending; the dated outcome is below.
**What is conjecture:** that local inference will make
iteration convenient, or that this one remedy will improve quality.

The user approved this screen on 2026-11-04. Freeze the exact GGUF hash,
llama.cpp revision, Metal runtime, server/client settings and contained tool
runtime before collecting. Preserve the previous two-slot context allocation;
collection concurrency is one. Each session has a 600-second deadline and
180-second open-tool cutoff. Retain all model failures and mixed recovered
transport errors. No favorable replacements; missing usage remains unknown.

Read the four hidden checks, code health, completion and their conjunction.
Prioritize provider requests/model turns, output including reported reasoning,
input/cache usage, tool calls/errors and peak context. Actual elapsed time is
secondary. Audit the provider feed for exactly one instruction per request,
the unchanged task brief, and which specification files were read.

The H100 cohorts remain historical references. CUDA-to-Metal trajectories may
differ even with matching settings; this is neither a comparative rate estimate
nor a decision to change a default. A direct local comparison needs new local
reference arms. No Runpod GPU is started; stop the local server after the screen.

Sources: implementation contract
[`2026-11-04-task-prompt-design.md`](../specs/2026-11-04-task-prompt-design.md),
current source at `f6d511e`, and the forthcoming local run records. Raw evidence
belongs outside Git; compact provenance and results belong under `evals/`.

## What would falsify this

Duplicate/missing instructions, changed briefs, source/runtime drift, failed
containment or backend identity checks invalidate collection. Low hidden scores
or repeated stalls would weaken the case for this remedy alone. Three runs
cannot establish general reliability.

## Risks

The hidden oracle covers four checks, less than the entire phase specification.
Sampling and host load can change trajectories; 50k context includes output.
The short qualification does not exercise a full 16,384-token response.

## Outcome — 2026-11-04

All three planned sessions ran sequentially under one qualified local freeze;
none was replaced. Hidden/health/completion jointly passed 2/3. The failure
returned HTTP 422 and stalled on a foreground server; health alone passed 3/3.
The successful attempts used 21/18 requests and 8,110/7,765 output tokens.

**Budget correction:** the agent recorder missed four compaction requests and
10,826 generated output tokens in the failure. Server and relay reconciliation
establishes 79 whole-session requests and 50,624 output tokens, rather than the
recorder's 75 and 39,798. Original records remain unchanged. The four additional
requests' API payloads/usage are unavailable; server generation timing counters
supply the supplement. No provider/relay error or missing completion occurred.

**Injection qualification:** one tagged instruction per agent request and one
visible persisted injection per task held, including after compaction. Literal
text uniqueness did not: reasoning quoted the rule repeatedly, and a generated
summary repeated it as the split turn's “Original Request” in three requests.
The summary retained the actual task in Goal. The protocol's duplicate check
therefore distinguishes duplicate injected messages from generated quotations;
the latter remain evidence, not silently stripped context.

The Mac is suitable for routine exploratory screens, with moderate confidence
from this n=3 screen. Layout guidance alone did not guarantee completion or
correctness. Before deciding a comparative budget claim, repair/reconcile
compaction accounting and collect common local reference arms. Next remedy
candidate: layout plus foreground guard; trim output is a separate lever.

The [compact record](../../../evals/2026-11-04-local-layout3/README.md) contains
quality, full and agent-only budgets, cache scope, commands, backend provenance,
qualification and shutdown. Raw traces/session/workspaces stay outside Git.
The local server and guardian stopped; no owned containers/volumes remain.
No Runpod GPU was started. This finding selects no default.
