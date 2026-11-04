# Foreground guard alone: three fresh Phase 1 sessions

Vanilla + recorder + only `guard/foreground-server` blocked one foreground
server start in each of three fresh Easy Phase 1 sessions. All three settled
and passed code health; none passed all hidden checks. This exploratory screen
selects no default and establishes no comparative rate or causal speedup.

| Run | Hidden | Health | Completion | Requests | Output tokens | Actual seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1a7570 | 2/4 | pass | settled | 25 | unknown | 43.816 |
| db0bb4 | 1/4 | pass | settled | 19 | 4,626 | 35.593 |
| a7d996 | unavailable: missing app module | pass | settled | 19 | unknown | 30.427 |

Total: 63 requests and 109.836 execution seconds; medians: 19 requests and
35.593 seconds. Full output usage is unknown; only one complete total is known.
Its peak prompt was 7,792 tokens. The other two recovered native 502 errors;
their full usage/context totals remain unknown. All attempts remain counted,
including the third's wrong-layout grader collection failure. No replacements.
Time excludes setup, qualification and grading.

## Feed and quality

The guard refused `uv run uvicorn app:app --reload`,
`uv run --frozen uvicorn app:app --reload --port 8000`, and
`uvicorn main:app --host 0.0.0.0 --port 8000`, respectively. Each refusal appeared
once in the native trace, once in the provider feed and once in the run counter.
Run 1 also issued a background server command, which the foreground guard
permits; cleanup removed the container. Help/version queries were permitted.
There were no stalls. A refusal does not establish how long an unblocked call
would have run.

All three read the tech-stack document, but none read the phase spec. Run 1
also read the mission; it missed the required tagline/navigation and placed a
self-authored test outside the specified layout. Its final pytest invocation
collected zero tests. Run 2's home page missed tagline/navigation and English
language metadata. Run 3 created `main.py` and `templates/home.html` rather than
the required layout; its self-authored test eventually passed, but the external
grader could not import `app`. This is a retained model failure, not a harness
infrastructure exclusion. Static health and normal exit are insufficient
acceptance signals. The four hidden checks themselves are narrower than full
Phase 1 acceptance.

[Feed audit](feed-audit.json): each initial provider payload is byte-equivalent
to the original Vanilla reference after JSON key sorting and literal run-ID
replacement. Only the guard and recorder loaded: no worker, three prompt
fragments, trim unit or context loader. All 63 requests sent sampling 1/.95/20
and `max_tokens: 16384`. No provider-visible trim note occurred. Recovered native
errors and relay ECONNRESET events remain in [observations](observations.json).

## Qualification and shutdown

All three ran sequentially against one frozen H100 Pod `bfnsf868qc593s`,
AP-IN-1, 81,559 MiB GPU memory, 28 vCPUs/251 GB host RAM. Inference used the Pod;
the Mac ran the harness and temporary contained tools. Same pinned llama.cpp
11669/620d2225c, CUDA 12.8 image, GGUF hash, two 50k slots and Pi 1.4.0 settings
as recorded in [configuration](backend-config.json). This is a new physical
host, separate from the earlier five-unit and Vanilla/Worker cohorts.
[Before](backend-live.json) and [after](backend-live-after.json) identity match.
Short and 47k-context pair probes each observed two simultaneous slots;
`ignore_eos:true` applied only to these synthetic probes.

The guard-only [actual-Pi interaction proof](interaction-qualification.json)
passed 10 observations; reused containment proof passed 27. All 641 repository
tests passed, and measured sources/image remained unchanged through collection.
No owned Docker container/volume, local inference process, controller or tunnel
remains. The guardian was bound to this literal Pod ID, stopped it on completion,
and a separate fresh [Pod read](final-pod.json) confirmed EXITED. The final
[account read](final-pods.json) shows all nine Pods EXITED. Their 450 GB of
persistent disk remains billable; no storage was deleted.

The guard performed its observed containment role. These outcomes do not show
that the guard alone supplies adequate coding guidance. A useful next single
unit screen is `prompt/name-the-layout`, motivated by the observed missing spec
reads and wrong paths; that is a hypothesis, not a measured remedy effect.
The earlier five-unit 3/3 result remains a separate screen, not a controlled
guard-only comparison on this host.

[Protocol and outcome](../../docs/superpowers/research/2026-11-04-guard-only3.md),
[scorecard](scorecard.md), [summary](summary.json), [records](records.json),
[verification](final-verification.json), [raw evidence](raw-evidence.json).

The raw archive is preserved locally and SHA256/critical bytes verified.
Public release upload was rejected by automatic approval review pending explicit
approval to disclose raw traces and workspace/checker data. The manifest's
`published_download_verified` remains false; no public asset is claimed.
