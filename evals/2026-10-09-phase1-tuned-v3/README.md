# Phase 1: tuned profile, worker prompt v3

Date: 2026-10-08. Same launch, rungs, repeats, and prompt (v3) as
[phase 0b](../phase0b-baseline-v3/README.md); only the oMLX profile changed.

| setting | baseline | tuned |
| --- | --- | --- |
| `max_tokens` | 4,096 | 16,384 |
| `thinking_budget_enabled` / `_tokens` | off | on / 4,096 |
| `presence_penalty` | 0 | 0.5 |
| `max_tool_result_tokens` | unset | 4,000 |
| `chat_template_kwargs` / `forced_ct_kwargs` | unset | `{"enable_thinking": true}` / `["enable_thinking"]` |

The runner applied the profile through the admin API and verified the live
values before the first run; `versions.model_settings` in each `run.json`
records them. The profile was restored to baseline afterwards.

Command:

```bash
uv run python -m ladder.run_ladder --profile tuned --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase1-tuned-v3
```

## Result

| rung | baseline (phase 0b) | tuned (phase 1) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 3/3 | 2/3 |
| 5 | 3/3 | 2/3 |

13 of 15 against 15 of 15. Full columns in [table.md](table.md).

| measure (15 runs) | baseline | tuned |
| --- | --- | --- |
| mean requests per run | 14.3 | 15.1 |
| largest prompt, chars | 76,248 | 51,880 |
| thinking re-entries | 0 | 0 |
| empty final replies | 1 | 2 |
| deadline hits | 0 | 0 |
| mean wall seconds (untrusted) | 61 | 49 |

## Correction (external review, 2026-10-08)

The `max_tokens` and `presence_penalty` rows above were **not effective**.
Every request Pi sent carried `max_tokens: 16384` and `presence_penalty: 0`
(1,534 of 1,534 across all phases), and oMLX gives request values
precedence over the model profile; a message in the baseline phase reached
5,033 output tokens. The only settings that actually differed between
baseline and tuned were the server-side ones: thinking budget, tool-result
cap, and forced thinking. The clamp check below is therefore uninformative:
the request was short. Every run in every phase was sampled at
`temperature 1, top_p 0.95, top_k 20`, not greedy. A comparison with the
profiles applied at the request level is queued as a follow-up.

## Reading

**The server-side settings that did apply bought nothing the ladder can see
and may have cost two runs.** Both tuned failures (4 r1, 5 r3) are the empty-final stop: a partial
edit, a read, then `stopReason: stop` with no visible text — the same
pathology as the baseline's single empty final (3 r3, which happened to pass
because the work was already done). Three repeats cannot separate 13/15 from
15/15 with confidence; what they can say is that the profile did not rescue
anything, because there was nothing left to rescue after prompt v3.

What each setting did or did not do:

- **Thinking budget.** No run died inside thinking on either profile (every
  stop reason is `stop`). The `thinking_reentries` column stayed 0, but that
  column has no positive control: it counts assistant messages with more than
  one thinking block in Pi's stream, and whether oMLX's reasoning parser
  would surface a server-side `<think>` re-entry as a second block is
  unverified. Treat 0 as "not observed", not "did not happen". On the baseline
  profile the 4,096 output cap was also never hit in 15 runs. On these tasks
  the budget is insurance, not a fix.
- **16,384 output.** Unused headroom on these rungs.
- **`max_tool_result_tokens` 4,000.** Largest prompts were smaller
  (52k vs 76k chars), consistent with truncated tool results, with no
  effect on pass/fail.
- **Presence penalty 0.5.** Never applied (request precedence, above). The
  variant below therefore compares two effectively identical configurations
  and is a measurement of run-to-run variance, not of the penalty.

## Clamp check

With the tuned profile live, a chat request with `max_tokens: 20000` returned
HTTP 200, `finish_reason: stop` — oMLX clamps to the profile's cap rather than
rejecting, so the harness limits can stay at 16,384 regardless of profile.

## Variant: tuned without the penalty

See `../phase1b-tuned-nopenalty-v3/` — the same tuned profile with
`presence_penalty` 0, run to attribute the two failures.

## First attempt discarded

A first phase-1 launch recorded two 600 s deadline rows with zero provider
requests: Pi hung before its first request because the runner was started
at the tail of a compound shell command and inherited a stdin pipe that
never closed. The runner now passes `stdin=DEVNULL` (test
`test_run_once_never_inherits_stdin`); those rows carried no model evidence
and were deleted.

### Variant result

| rung | baseline | tuned | tuned, no penalty |
| --- | --- | --- | --- |
| 1 | 3/3 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 | 2/3 |
| 4 | 3/3 | 2/3 | 1/3 |
| 5 | 3/3 | 2/3 | 3/3 |
| empty finals | 1 | 2 | 4 |
| mean requests | 14.3 | 15.1 | 11.7 |
| edit anchor failures | 5 | 7 | 0 |

12 of 15 "without the penalty" — but the penalty was never in effect in
either run, so tuned (13/15) and this variant (12/15) are the same effective
configuration run twice: a direct estimate of noise at n = 3. Every failure
across the three phases (5 of 45 runs) is the same event — a turn ending
with `stopReason: stop` and no visible text, part-way through the task.
**Defensible conclusion: the empty-final stop occurs across every tested
configuration, and none of the settings that actually applied showed a
benefit. Independence from output cap or presence penalty is not
established, because neither was tested.** It is the phase-2 target.

The 16k output and the thinking budget remain reasonable insurance for
larger tasks than these fixtures; the ladder has no evidence either way at
that size.

Raw traces, stdout and diffs: [`phase1-tuned-v3.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase1-tuned-v3.tar.gz).
