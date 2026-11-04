# Local remedy comparison: neither arm meets the trust bar

Six fresh Easy Phase 1 sessions per arm alternated on one frozen M5 Max Metal
backend. The selective five-unit stack is the better next lead on the registered
quality/budget reading, but **neither arm meets the predeclared five-of-six bar**.
No preset or default is promoted. These are Phase 1 results, not a whole-workflow
baseline. Every attempt is retained; no replacements or infrastructure failures.

| Registered result | Layout only | Selective five units |
| --- | ---: | ---: |
| Sessions | 6 | 6 |
| All four hidden checks | 3/6 | 4/6 |
| Code health | 6/6 | 5/6 |
| Settled | 5/6 | 5/6 |
| Final changed paths within phase layout | 4/6 | 6/6 |
| External project pytest suite passes, at least one test | 2/6 | 4/6 |
| All registered stricter conditions together | **1/6** | **4/6** |
| All inference requests | 123 | 148 |
| All generated output, including thinking | 46,405 | 64,859 |
| Output per registered stricter pass, all attempts included | 46,405 | 16,214.75 |
| Requests per registered stricter pass | 123 | 37 |
| Median requests / output per attempt | 20 / 7,223 | 25.5 / 9,515.5 |
| Combined execution seconds | 592.436 | 554.707 |
| Median execution seconds | 72.419 | 83.360 |

The larger stack consumed about 40% more total output and 20% more requests,
but produced four registered stricter passes instead of one. Its observed output
per such pass was about 65% lower. This favors continuing with it as a lead;
it is not a reliability estimate or proof that any individual unit caused the
change. Six repetitions of one task cannot establish general effectiveness.
[Every attempt](scorecard.md), [summary](summary.json), [records](records.json).

## What the registered score means

The stricter score requires hidden behavior, health, completion, final path
compliance and an externally rerun project suite with at least one executed
test. A separate private container reran that suite after the model settled;
passing, failing and empty fixtures qualified this recheck. The tests themselves
were written by the model and can be weak. Final changed paths are not an
exhaustive temporal write history. Four hidden checks do not exhaust the spec.

The original [preregistration snapshot](preregistration.md) fixes arms, n,
alternation, reading and decision rule. Its result is **neither candidate**.
The supplementary audit below does not change these registered scores.

## Actual failures and guard behavior

- L1 settled with no tests; L2 passed the registered stricter score. L3 returned
  422 because its FastAPI request parameter lacked the required annotation; it
  also created an early `models.py`. L4 passed hidden/project tests but created
  that same out-of-phase placeholder. L5 also returned 422 and created no tests.
  L6 left `uv run --frozen python app.py` open; the 180-second cutoff ended the
  tool stall, with 240.024 seconds total execution. Its home route returned 422.
- S1 settled with syntax-corrupted `app.py` containing model/tool syntax and
  reasoning text, despite claiming completion. S2 ended with a peg-native
  output-format error. Both are counted failures of this model/backend pair.
  S3–S6 passed the registered stricter score.
- The repaired foreground guard refused three actual launch attempts across
  S5/S6: two uvicorn invocations and `uv run python app.py`. These were launches,
  unlike the previous cohort's diagnostic false positive. No diagnostic false
  positive was observed here. The guard remains a heuristic, not isolation.

Native accounting records 118/143 tool attempts and 15/34 error results for L/S.
The three refusals bypass ordinary tool hooks but remain in native events; the
unfinished L6 tool is retained explicitly. [Delivery, commands, errors and
refusals](observations.json), [counted-failure adjudication](adjudication.json).

## A separate specification/startup audit found more misses

After early outputs exposed a missing favicon and a broken reload startup,
a **post-registration diagnostic** checked 13 aspects of the saved output:
rendered home behavior, shared template use, HTML/language, viewport, Bootstrap
placement, favicon, default title, navigation, paragraph, main guard/reload and
actual script startup serving `GET /`. It was never visible to the model.

| Supplementary result | Layout only | Selective |
| --- | ---: | ---: |
| All 13 diagnostic checks | 1/6 | 3/6 |
| Required startup serves the home page | 1/6 | 3/6 |
| Registered stricter pass and all 13 diagnostics | 0/6 | 3/6 |

L2 and S3 passed hidden/project tests but used `uvicorn.run(app, reload=True)`.
The pinned uvicorn rejects that reload form: it requires an import string.
Their actual launch logs contain the warning and exit status; their registered
passes stay unchanged. L4 passes all 13 diagnostics but fails the registered
phase-layout condition. The three S outputs passing both layers still hard-code
the base title; page-specific title override is outside this diagnostic's
coverage. **A diagnostic pass is not exhaustive Phase 1 acceptance.**
[Results](supplementary-spec-results.json), [audit source](supplementary-spec-audit.py),
[additional coverage notes](manual-coverage-notes.json).

The first diagnostic incorrectly assumed every meta element had a name attribute.
A valid charset-plus-viewport fixture reproduced its false failure before the
optional-attribute fix. The corrected fixture passes all 13 checks; a missing
favicon and a broken reload launch are still rejected. All saved outputs were
then rechecked. Original invalid diagnostics and qualification failures remain
in the local raw archive; no inference was repeated or registered score changed.

## Complete inference budget and provenance

Backend timings, per-run relay boundaries and every available native response
usage reconcile: **271 coding generations and 111,264 output tokens**, plus six
separately excluded infrastructure probes (277 generations overall). No
compactions occurred. The earlier recorder compaction gap is not fixed by this
batch. Native S2 output usage remains unknown; its 17 backend generations total
6,292 output tokens, with successful responses cross-checked individually.
[Per-request backend counts and cache scope](backend-budget.json).

The backend counted full/evaluated prompts as 900,941/28,018 tokens for L and
1,312,562/38,779 for S. Repeated prompt/cache tokens are not new generated output
or a monetary billing claim. Native input/cache totals retain their own known
response scope. Combined execution was 1,147.143 seconds (19m07s), excluding
setup, qualification and grading.

Both arms used Vanilla Pi 1.4.0 plus recorder, no worker extension. L loaded only
`prompt/name-the-layout`; S added `prompt/python-developer`,
`prompt/verify-the-spec`, `guard/foreground-server`, `context/trim-tool-output`.
Every agent request preserved the brief and exactly one tagged message per task
instruction; S's developer role stayed in the system prompt. Each session
persisted one or two distinct `Injected` entries. No prompt text changed.

Implementation `2f2aade`, content-addressed image, model/hash, Metal libraries,
hardware/OS, server argv and effective profile were frozen. All 29 layers and
KV were on MTL0. Coding stayed sequential; two slots each had 50,176 effective
context. Sampling 1/.95/20, output ceiling 16,384, deadline 600s, open-tool cutoff
180s. The same previous local backend was requalified with short/47k two-slot
probes, tool calling and SSE. Boundary qualification passed 27 checks; actual
Pi interaction passed 11, including the formerly refused import diagnostic.
The source suite passed 658 tests; independent guard and accounting reviews found
no remaining important issue. [Verification](verification.json),
[pre/post identity](post-identity-verification.json).

## Decision and next work

Keep selective injection; it delivers the intended messages correctly. Keep the
repaired optional foreground guard. Do not equate either with reliable task
completion. The next behavior to measure is an external, complete, immutable
acceptance command with bounded failure redispatch, kept as an explicit additive
unit. A stronger checker must be qualified against the whole spec before it
selects a default. More prose reminders are not the current lead.

Inference stopped normally, its identity-checked guardian stopped, port 8002 has
no listener and no owned container/volume remains. No Runpod GPU was started.
[Shutdown](shutdown.json). Raw evidence is credential-scanned and held locally,
with **no upload**, as requested. [Archive manifest](raw-evidence.json).
