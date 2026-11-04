# Repaired five-remedy arm: three fresh Phase 1 sessions

The repaired five-unit arm passed all four hidden checks, health and completion
in all three fresh Easy Phase 1 sessions. This repeats the earlier single-screen
result on one newly qualified H100 host. It is an exploratory repeatability
screen; it selects no default and attributes no benefit to an individual unit.

| Run | Hidden | Health | Completion | Requests | Output tokens | Actual seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 399cf9 | 4/4 | pass | settled | 17 | 8,171 | 46.892 |
| b5e526 | 4/4 | pass | settled | 33 | unknown | 82.503 |
| 0a2c0c | 4/4 | pass | settled | 17 | 6,836 | 42.805 |

All three attempts remain counted; no replacements. Total: 67 requests and
172.200 execution seconds; medians: 17 requests and 46.892 seconds. Full output
for the cohort is unknown: the two complete runs sum 15,007 tokens. Peak full
prompt is 11,139 among two known maxima; the middle run's peak is unknown.
Time excludes setup/qualification/grading; this is a different host from the
older baseline cohorts, so timing differences are not causal remedy effects.

## What the actual feed showed

All sessions loaded Vanilla + recorder with the same ordered units:
`prompt/name-the-layout`, `prompt/python-developer`, `prompt/verify-the-spec`,
`guard/foreground-server`, `context/trim-tool-output`. No worker extension or
project context loader was added. All three prompt fragments arrived in each
initial provider payload. Every one of 67 requests sent `max_tokens: 16384` and
sampling 1/.95/20. Measured sources, image and backend identity were reverified.

There was no server/help command, native foreground refusal or provider-visible
trim note in any of the three trajectories. These runs show a repeated bundled
coding result, not a prevented foreground hang or an observed trimming benefit.
The [targeted actual-Pi interaction proof](interaction-qualification.json) from
the unchanged image separately exercises help/version, a real refusal counted
once, and trimming. Removing units requires a fresh contrast.

Run 1 tried an absent tests directory, then wrote and passed one test. Run 2
recovered from its own test syntax/import problems and an incorrect
Jinja2Templates import, then passed two tests; it also repaired a brittle
self-authored source-text assertion. Run 3 passed one self-authored test.
All wrote only the allowed layout. The external hidden grade passed 4/4 in
all three, but those four checks are narrower than whole-phase acceptance.

The middle run recovered from a native 502 on request 12, then continued to a
settled result. Its missing full usage is not zero or estimated. Relay stream
ECONNRESET events also exist in all three attempts; they are retained separately
from native errors. Native requests/replies provide complete usage for runs 1/3.
No transport event, ordinary tool error or debugging detour was discarded.
[Detailed commands, errors and boundaries](observations.json).

## Backend, qualification and shutdown

Pod `x40gf9pjw2gw09`, AP-IN-1, H100 81,559 MiB, 28 vCPUs/251 GB host RAM; same pinned
CUDA 12.8 image, llama.cpp 11669/620d2225c built for 90a, GGUF hash, two 50k slots and
client settings. All three sessions ran sequentially against this one freeze;
inference used only the Pod GPU, with tools in temporary local containment.
[Before](backend-live.json) and [after](backend-live-after.json) identity match.

The initial short concurrency probe undersampled subsecond responses through
the distant tunnel. Its failed observation is retained. Only synthetic probes
were extended with ignore_eos:true at 512/64 bounded tokens; both short and 47k
pairs then observed two active slots. Coding requests were unchanged. The setup
race and refused re-extraction are also retained in the raw setup logs.

All 641 repository tests passed; docs caps passed. No owned container/volume,
local inference process, controller or tunnel remains. The guardian retained
a stale Pod ID: automatic approval review rejected that stop, and the active
Pod was then stopped directly and independently [read back EXITED](final-pod.json).
This corrects the earlier statement that the mutable guardian target had been
updated. Future guardians must bind the actual literal Pod ID or reread it from
a file, rather than relying on cross-cell mutable store state. The final account read shows all eight Pods EXITED. Their 400 GB of persistent
disk remains billable; no storage was deleted.

[Protocol and setup observations](../../docs/superpowers/research/2026-11-04-remedy-repeat3.md),
[scorecard](scorecard.md), [summary](summary.json), [records](records.json),
[frozen configuration](backend-config.json), [raw evidence](raw-evidence.json).
The earlier [repair screen](../2026-11-04-guard-repair/README.md) and
[Vanilla/Worker comparison](../2026-11-04-contained-h100/README.md) stay unchanged.
The next informative contrast is the foreground guard alone against the
five-unit arm, holding one newly qualified backend across both; no such run is
claimed here.
