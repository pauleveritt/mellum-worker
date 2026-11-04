# M5 Max: task-scoped name-the-layout, three Phase 1 sessions

Two of three fresh sequential Easy Phase 1 sessions passed all four hidden
checks, code health and completion. The other returned HTTP 422 and stalled on
its foreground server. This is a local Metal exploratory screen of Vanilla Pi
plus recorder and **only** `prompt/name-the-layout` with its new injected
once-per-task delivery. It is not a new Vanilla reference or a preset decision.

| Run | Hidden | Health | Completion | Agent / all requests | All output tokens | Actual seconds |
| --- | --- | --- | --- | --- | --- | --- |
| e97e22 | 0/4 | pass | stalled | 36 / 40 | 34,749 | 596.885 |
| 8cd4d7 | 4/4 | pass | settled | 21 / 21 | 8,110 | 58.174 |
| 304502 | 4/4 | pass | settled | 18 / 18 | 7,765 | 61.223 |

**Full inference budget: 79 requests and 50,624 generated output tokens.**
Median: 21 requests, 8,110 tokens and 61.223 seconds. Execution time totals
716.282 seconds (11m56s), excluding setup/qualification/grading. The failed
session used 68.6% of output and 83.3% of execution time. All attempts remain
counted; no replacements, native provider errors or relay failures.

## Budget accounting correction

The original [agent scorecard](scorecard.md) records 75 requests and 39,798
output tokens. It misses four requests and 10,826 output tokens during the
first run's three compaction attempts. Those agent records remain unchanged;
they are incomplete as whole-session inference budgets.

The [backend supplement](backend-budget.json) reconciles every completed server
generation with the HTTP relay: 85 completions = six uncounted qualification
probes + 40 + 21 + 18 coding-session completions. All relay responses were HTTP
200 and completed. In both runs without compaction, backend generation counts
and output tokens exactly match native usage. The supplement uses server timing
counters for the four additional completions; their API usage and full prompt
payloads were not captured by the recorder. This is a measured harness gap,
not missing usage caused by a recovered provider error.

| Run | Full prompt tokens, summed | Evaluated prompt tokens | Agent uncached / cached input | Peak prompt |
| --- | --- | --- | --- | --- |
| e97e22 | 396,960 | 125,508 | 119,055 / 271,322 | 46,282 |
| 8cd4d7 | 149,550 | 6,574 | 6,574 / 142,976 | 12,874 |
| 304502 | 134,977 | 5,056 | 5,056 / 129,921 | 12,204 |

Server prompt counters include compaction. Native input/cache counters cover
agent requests only; cache writes were reported as zero. Summed prompt tokens
count repeated context on each request; they are not unique source tokens.
There were 73 tool calls and 10 tool errors. Pi clamped two requests in the
first session to 7,917 and 7,118 output tokens as context grew; the other 73
agent requests sent the configured 16,384 ceiling. Sampling remained 1/.95/20,
min-p 0, presence penalty 0 and repetition penalty 1. Generated output includes
thinking; no separate trustworthy thinking-token total is inferred.

## What the actual feed and grader showed

Every agent request had exactly one tagged injected instruction, and each
session persisted exactly one visible `Injected` entry. The original task
brief was unchanged. No worker extension, other prompt fragment, foreground
guard or trim remedy was loaded. The first run's assistant reasoning repeatedly
quoted the instruction; its generated compaction summary also quoted it in
three outgoing requests and labelled it the split turn's “Original Request.”
One tagged injection does **not** guarantee the instruction text appears only
once after model-generated quotations. The real task remained in the summary's
Goal. This qualification limits the literal one-copy claim.

All three read `specs/roadmap.md`. Run 1 wrote the expected files, read `uv.lock`,
and accumulated a 46k prompt with three compaction attempts. Its own test
already exposed HTTP 422. It left the route's `request` parameter untyped, then
launched `.venv/bin/python app.py`; the 180-second open-tool cutoff fired.
All four hidden checks genuinely ran and failed. Health passed, showing why
health and functional acceptance must remain separate. The inner process sweep
listed descendants; removing the whole private container completed cleanup.

Run 2 also initially returned 422, repaired its request annotation and passed
its self-authored test and all four hidden checks. It attempted two foreground
server commands, but absent global `uvicorn`/`python` executables made them
fail immediately. That environmental accident is not a guard or a general
completion guarantee. It also wrote an extra `models.py`, recorded separately
as out of this phase's layout. Run 3 ran its tests successfully, passed the
hidden grade and wrote within the phase layout. Neither run compacted.

The four hidden checks cover less than the entire phase specification. The
observed 2/3 conjunction does not certify complete Phase 1 acceptance or a
reliable remedy. [Commands, errors and prompt audit](observations.json).

## Local qualification and shutdown

Inference ran on the **Mac's M5 Max GPU**, with temporary Docker isolation for
Pi tools and separate grading. No Runpod Pod was started. Pinned GGUF hash
`ecc4d5b8…fa2755`, Q4_K_M, llama.cpp build 11669 / `620d2225c`, Metal runtime and
dependencies were hashed. Logs prove all 29 layers and KV buffers on MTL0.
Two independent slots each had 50,176 effective context; collection concurrency
was one. Two short and two 47,034-token synthetic requests, required tool calls
and SSE passed. The rebuilt image passed all 27 boundary checks and the
actual-Pi layout interaction probe. [Freeze](backend-config.json),
[boundary proof](boundary-qualification.json), [interaction proof](interaction-qualification.json).

Default verbosity first hid offload details; verbosity 4 exposed the accelerator
as `MTL0`, requiring correction of the proof's expected label. Both refused
qualification attempts and their clean shutdowns remain in raw setup evidence;
no coding run occurred during them. All three counted sessions then used one
unchanged freeze. Sources/image/runtime were verified before and after runs.

The task-owned local server exited cleanly, port 8002 has no listener, and no
owned container or volume remains ([shutdown](shutdown.json)). A separate
3,500-second shutdown guardian was bound to this literal server identity and
was stopped during final cleanup. All 647 repository tests passed before
collection. H100 cohorts remain historical references: no causal cross-device
speed or quality comparison is claimed.

The local machine is practical for routine iteration. Before a budget comparison,
fix or supplement whole-session compaction accounting, then run all compared
arms under this local freeze. A useful next screen is layout plus the existing
foreground guard; oversized reads are a separate trim lever. Neither remedy is
silently enabled here. [Protocol/outcome](../../docs/superpowers/research/2026-11-04-local-layout3.md),
[summary](summary.json), [records](records.json), [raw evidence](raw-evidence.json).

Raw evidence is retained locally in the credential-scanned archive named in
`raw-evidence.json`; publication of this new archive awaits explicit approval.
