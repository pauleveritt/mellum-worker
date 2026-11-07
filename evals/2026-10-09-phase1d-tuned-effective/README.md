# Phases 1c and 1d: the profiles, this time in effect

Date: 2026-10-08/09. The redo of phase 1 after the external review found that
every earlier run had been sampled at Pi's defaults (`temperature 1, top_p
0.95, top_k 20, max_tokens 16384, no penalty`) regardless of the server
profile, because oMLX lets request values override the model profile and Pi
sends them on every request. Here the runner writes a temporary `models.json`
whose `samplingParams`/`maxTokens` carry the profile, and the scorer records
what was actually sent as `effective_params`. The runner refuses to continue
if the first request disagrees with the profile.

Both phases are greedy by design (`temperature 0, top_p 1, top_k 0, min_p 0,
seed 42`): the question is what the cap, the penalty, and the server-side
thinking budget do, not what sampling variance does. Direct mode, prompt v3,
guards on with the nudge capped at one, three repeats, 600 s deadline.

| phase | request cap | presence penalty | server thinking budget | tool-result cap |
| --- | --- | --- | --- | --- |
| 1c `baseline` | 4,096 | 0 | off | off |
| 1d `tuned` | 16,384 | 0.5 | 4,096 per block | 4,000 tokens |

```bash
uv run python -m ladder.run_ladder --mode direct --guards --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase1c-baseline-greedy
uv run python -m ladder.run_ladder --mode direct --guards --profile tuned    --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase1d-tuned-effective
```

## Result

| rung | 1c baseline (cap 4,096) | 1d tuned (cap 16,384, penalty 0.5) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 2/3 | 2/3 |
| 5 | 2/3 | 3/3 |
| total | 13/15 | 14/15 |

| measure (15 runs each) | 1c | 1d |
| --- | --- | --- |
| requests per run, mean / max | 13.5 / 26 | 13.1 / 20 |
| tool errors (runs with any) | 12 (6) | 11 (6) |
| `length` stops | 1 | 0 |
| nudges fired / recovered | 2 / 2 | 1 / 1 |
| empty final text | 0 | 1 |
| thinking re-entries | 0 | 0 |
| loop breaker would block | 0 | 0 |
| largest prompt, chars | 51,676 | 60,157 |
| wall seconds per run, mean (untrusted) | 54 | 51 |

Full columns in each phase's `table.md`.

## The failures, one by one

- **1c rung 4 r1, `length`.** The first request after reading the three files
  spent all 4,096 output tokens thinking and was cut off; Pi's text block is
  a copy of the thinking, so `final_text_chars` is 14,443 and the diff is
  empty. This is the request cap, not the model: the same decision in 1d had
  room and completed. A 4,096 cap is too small for this model's thinking on a
  three-file change.
- **1c rung 5 r3, honest.** Fifteen requests, two tool errors, final text
  reports the tests still failing. The three-file change by symptom alone is
  the rung the worker does not reliably solve on its own.
- **1d rung 4 r3, empty turn, twice.** After editing `totals.py` the model
  decided in its thinking to edit `render.py`, emitted an empty text block,
  and stopped (401 output tokens). The nudge fired; the model continued,
  listed files, read `pyproject.toml`, ran the tests, then did it again:
  2,587 tokens of thinking ending in "We'll use edit tool on render.py",
  empty text, `stop`. The nudge cap of one had been spent; the run ended with
  a partial fix. See [its stdout](rung4-tuned-direct-guards-r3/stdout.txt).

## Reading

**The cap matters; the penalty does not show.** Going from 4,096 to 16,384
removed the one `length` stop. Nothing else moved outside the noise of three
repeats: pass count 13 vs 14, requests 13.5 vs 13.1, tool errors 12 vs 11.
The presence penalty of 0.5 produced no measurable change in either
direction; nor did the 4,000-token tool-result cap (no run hit it: the
largest tool result in either phase was 2,639 characters). The server-side
thinking budget never forced a `</think>` (`thinking_reentries` 0 in all 30
runs), so it was not exercised. Recommendation: cap 16,384 from the model
card, penalty off, budget off; the "tuned" extras are harmless and unproven.

**Greedy is not reproducible here.** With `temperature 0` and `seed 42`,
the three repeats of rung 1 in 1d took 8, 8 and 7 requests to reach the
same diff, and the rung 4 repeats diverged entirely. oMLX's batched MLX decoding is not bit-stable across requests,
so repeats remain a gate, not a determinism check.

**The residual pathology is the empty turn.** Across the direct phases the
nudge has now been allowed to act on six empty turns: phase 2, five fired,
one recovered and one thrashed for 31 requests; 1c, two fired, both
recovered with the tests going green afterwards; 1d, one fired and
recovered, and a second lapse in the same run went uncaught. Four of six
recoveries, one thrash. A cap of one is both too small (1d) and not a bound
(phase 2). The next measurement is a bounded nudge: cap 3 with the loop
breaker enabled, under these 1d settings.

**Versus the sampled runs.** Phase 0b (sampled, prompt v3, no guards) was
15/15; phase 2 (sampled, guards) 12/15. Greedy with the caps in effect is
13–14/15. The difference is within three-repeat noise, and the settings
question the external review raised is answered: none of the server-side
knobs beyond the request cap has a measurable effect on this ladder.

## Caveats

Three repeats; greedy decoding that is not actually deterministic; a single
model build (Q6 MLX) on one server version (oMLX 0.6.4).

Raw traces, stdout and diffs: [`phase1d-tuned-effective.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase1d-tuned-effective.tar.gz).
