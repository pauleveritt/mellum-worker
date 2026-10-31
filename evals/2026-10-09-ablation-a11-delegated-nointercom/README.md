# Ablation A11: pi-subagents' intercom bridge off

Date: 2026-10-09. [A10](../ablation-a10-delegated-v5/README.md) again with
pi-subagents' `intercomBridge.mode` set to `off`. pi-subagents reads that
only from `~/.pi/agent/extensions/subagent/config.json`; the runner's new
`--subagents-config` writes a replacement into the mirrored agent directory
so the operator's file is untouched. The setting removes the 1,582-character
"Intercom orchestration channel" block that every child otherwise receives,
which told the worker to use a `contact_supervisor` tool it does not have.

```bash
uv run python -m ladder.run_ladder --mode delegated --profile baseline --guards --subagents-config '{"intercomBridge":{"mode":"off"}}' --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/ablation-a11-delegated-nointercom
```

| rung | A10 | A11 |
| --- | --- | --- |
| 1–5 | 15/15 | 15/15 |

| measure (15 runs) | A10 | A11 |
| --- | --- | --- |
| child system prompt, chars | 2,711 | 1,220 (v5 643 + pi-subagents' 521-char preamble + `<active_agent>`/cwd lines) |
| child prefill, k chars per run | 221 | 176 |
| child requests per run, mean / max | 11.1 / 16 | 10.7 / 17 |
| child tool errors | 7 | 6 |
| children that "produced no output" / re-dispatched | 0 / 0 | 2 / 1 |
| parent turns / output tokens per run | 6.5 / 2,887 | 7.3 / 3,889 |
| wall seconds per run, mean (untrusted) | 54 | 57 |

## Reading

**Holds, and the child's prompt is 55% smaller (1,491 characters less).**
The 20% drop in prefill is the block's share of every request. Passes, requests and errors did not
move. Wall time did not move either: prefill on oMLX is mostly cache hits
(86% of the direct worker's input tokens in A3), so a shorter prompt is
cheaper in tokens, not noticeably in seconds.

**The empty turn came back, twice, and the parent recovered both.** A10's
zero was luck at n = 15; across the five delegated phases the rate is 2–3
runs in 15. The parent's re-dispatch remains the recovery in delegated
mode, now 12 of 13 occurrences.

**What the setting costs.** It is global: with the bridge off, none of the
operator's subagents get `contact_supervisor` or its instructions. For a
profile whose children are all leaf workers that is free; for one that uses
supervisor messaging it is not. The recipe lists it as an optional
operator setting with that caveat, not a default.

**The remaining 521 characters** are pi-subagents' child preamble ("You are
a child subagent, not the parent orchestrator…"), which has no switch. The
worker's own prompt is now just over half of what the model reads before
the task.

Raw traces, stdout and diffs: [`ablation-a11-delegated-nointercom.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a11-delegated-nointercom.tar.gz).
