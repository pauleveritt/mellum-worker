# Local five-remedy screen: selective task injection

All three fresh sequential Easy Phase 1 sessions passed the four hidden checks,
code health and completion. Vanilla Pi plus recorder loaded the same five
explicit remedy names as the hosted screen. Layout and verification guidance
now arrive as separate, once-per-task `Injected` messages; the developer role
stays in the system prompt. No worker extension was loaded.

| Run | Hidden | Health | Completion | Requests | Output tokens | Actual seconds |
| --- | --- | --- | --- | --- | --- | --- |
| fa0f5a | 4/4 | pass | settled | 24 | 13,151 | 104.164 |
| 6aac6c | 4/4 | pass | settled | 21 | 9,442 | 77.700 |
| fe2bf9 | 4/4 | pass | settled | 35 | 10,538 | 104.570 |

**Total: 80 inference requests, 33,131 output tokens and 286.434 execution
seconds (4m46s).** Medians: 24 requests, 10,538 tokens and 104.164 seconds.
No attempts were replaced. There were no provider/relay errors, stalls or
compactions. Independent server/relay accounting matches native usage exactly:
86 completed generations = six uncounted qualification probes + 24 + 21 + 35.
The earlier compaction recorder defect is not repaired or re-exercised here.
[Full accounting](backend-budget.json), [summary](summary.json), [records](records.json).

## What the actual feed showed

Every agent request retained one tagged layout instruction and one tagged
verification instruction. Each session persisted exactly two visible `Injected`
entries, with the original user brief unchanged. The developer role appeared
once, in the system message. All requests sent the 16,384 output ceiling and
sampling 1/.95/20, min-p 0, presence penalty 0 and repetition penalty 1.
Generated reasoning can quote instructions; tagged-message uniqueness does not
promise literal text uniqueness.

All three read the roadmap. Run 1 recovered from an empty test run and a syntax
error in its self-authored AST test, then passed two tests. It created a premature
`models.py`, recorded separately as outside this phase's layout. Its `uv.lock`
read was visibly trimmed. Run 2 first found no tests, then created and passed one
home-page test and wrote within the phase layout.

Run 3 exercised the home page and navigation with in-process TestClient commands.
It eventually ran pytest, which exited 5 because it had created no tests; it did
not obtain a passing pytest suite. Its final reply described the endpoint checks
without claiming pytest passed. The external hidden grade passed 4/4, and its
files stayed within the phase layout. Its broad `find / ...` searched the private
container, not the Mac, and produced a second visibly trimmed result. Neither
the verification prompt nor correct hidden behavior guarantees efficient
exploration or a passing self-authored test suite.

There were 77 native tool attempts and 13 native error results. The ordinary
recorder hooks report 76 calls and 12 errors: one guard interception bypassed
those hooks, but native start/end events account for it. It remains counted as
one refusal, without double counting. [Commands, errors and delivery audit](observations.json).

## The guard refusal was a false positive

The sole refusal was:

```sh
python -c "import uvicorn, sys; print(uvicorn.__file__)"
```

This inspects a module location; it does not start a server. The guard's broad
server-name matcher misclassified it. The ordinary `tool_call` hook did not fire
because the guard intercepted first; native events and the later provider feed
retain the attempted command and refusal. This explains the initial audit's
correlation failure. It is not evidence that a foreground hang was prevented.
The model continued and passed the hidden grade, but this is another guard
false positive to repair before more remedy experiments. The earlier targeted
qualification proves help/version allowance, a real server refusal and trimming;
it did not cover this diagnostic import.

## Quality and budget in context

| Screen | Hidden + health + completion | Recorded agent requests | Full output tokens | Median seconds |
| --- | --- | --- | --- | --- |
| Hosted five-unit, previous delivery | 3/3 | 67 | unknown | 46.892 |
| Local layout injection only | 2/3 | 75 (+4 compaction) | 50,624 | 61.223 |
| Local five-unit, selective injection | 3/3 | 80 | 33,131 | 104.164 |

The hosted screen's two complete output records were 8,171/6,836 tokens; its
third remains unknown. The new screen matches the hosted screen's observed
quality, with more recorded requests (80 vs 67; median 24 vs 17). It does not
establish better token efficiency. Hardware and delivery differ, so this is not
a causal delivery comparison or comparative rate estimate. Local layout-only
used the same backend but a different remedy stack: its failure consumed much
of the cohort's budget. All are n=3 exploratory Phase 1 screens, narrower than
whole-phase acceptance; no preset or default is promoted.

The new screen's native uncached/cached input totals were 29,105/849,949 tokens;
cache writes were zero. Full prompt tokens summed to 879,054 across requests;
these include repeatedly supplied cached context. Peak prompt: 25,527.
[Per-run cache scope and backend counters](backend-budget.json).

## Qualification, provenance and shutdown

Inference ran on the M5 Max GPU with Pi tools/grading in temporary Docker
containment. No Runpod GPU was started. The previous local GGUF/path/hash,
llama.cpp 11669/620d2225c Metal binaries and dependencies, hardware/OS,
server argv, effective client profile/settings and checker versions all match
([comparison and post-run identity proof](post-identity-verification.json)).
The image changed intentionally for implementation `7b70d09`; its 27 boundary
checks and the actual contained five-unit interaction probe passed.
The standalone actual-Pi verification probe passed 12 checks/20 requests.
Eight new regressions failed first; the focused 47 checks, full 653-test suite,
document caps and documentation build passed after refreshing a generated remedy
page. Independent code review found no issues.

Two short and two 47,034-token simultaneous synthetic requests, tool calling and
SSE requalified the backend. Collection stayed sequential under one freeze.
Source/image/runtime identity and weights were reverified afterward. All 29
layers and KV buffers were on MTL0; each of two slots had 50,176 effective context.
The 600-second deadline and 180-second open-tool cutoff stayed fixed.

The local server and its literal-identity shutdown guardian stopped. Port 8002
has no listener; no owned container or volume remains ([shutdown](shutdown.json)).
Raw evidence is credential-scanned and retained locally; no archive was uploaded,
as requested. [Archive manifest](raw-evidence.json),
[protocol/outcome](../../docs/superpowers/research/2026-11-04-local-selective3.md).
The next concrete repair is the diagnostic guard false positive; a controlled
delivery comparison would require old/new delivery on the same local stack.
