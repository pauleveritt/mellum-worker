# Ablation A14: Mellum Mode inside the main session

Date: 2026-10-09. The operator's full profile (Superpowers, pi-subagents,
context7, the skills catalog), model Mellum, the raw rung sentence as in
[phase 0c operator](../phase0c-primary-operator/README.md), plus
`.pi/mellum/mellum-mode.ts` forced on (`MELLUM_MODE=1`) and the guards.
While the mode is on, its `before_provider_request` hook rewrites every
request: the system message becomes the worker prompt (v5), the messages
are those since the mode began minus Superpowers' bootstrap, and the tool
list is the worker's seven (pi-subagents re-adds `subagent` and
`subagent_supervisor` after `setActiveTools`; the hook removes them).
Sampled at Pi's defaults, as the operator profile is. Three repeats.

```bash
uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a14-mellum-mode
```

| rung | operator profile, Mellum primary (0c) | Mellum mode (A14) | worker alone, direct, greedy (A3) |
| --- | --- | --- | --- |
| 1 | 3/3 | 3/3 | 3/3 |
| 2 | 2/3 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 | 3/3 |
| 4 | 2/3 | 2/3 | 3/3 |
| 5 | 0/3 | 3/3 | 3/3 |
| total | 10/15 | **14/15** | 15/15 |

| measure (15 runs) | 0c operator | A14 mode | A3 direct |
| --- | --- | --- | --- |
| sampling | Pi defaults (temp 1) | Pi defaults (temp 1) | greedy |
| system prompt, chars | 17,091 | 606 | 736 |
| tools offered | 9 (incl. `subagent`) | 7 | 7 |
| prefill, k chars per run | 1,055 | **237** | 308 |
| requests per run, mean / max | 13.7 / 26 | 13.1 / 18 | 14.3 / 27 |
| output tokens per run, mean | 5,658 | 5,701 | 5,344 |
| tool errors / nudges / empty finals | 17 / 0 / 2 | 13 / 7 / 1 | 17 / 2 / 0 |
| wall seconds per run, mean (untrusted) | 72 | 70 | 54 |
| wall by rung | 55 / 81 / 54 / 84 / 85 | 24 / 76 / 31 / 99 / 122 | 18 / 36 / 21 / 87 / 108 |

The one failure (rung 4 r2): an empty final after the nudge cap of three
was spent, with one of three files changed. The same pathology as
everywhere else.

## Reading

**"Run in main with guardrails" works.** Same profile, same sampling, the
same sentences: 10/15 becomes 14/15, rung 5 goes from 0/3 to 3/3, and the
model reads a 606-character prompt instead of 17k characters plus the
skills catalog. No parent round trip, no brief, no subagent. The user
types the task and gets the worker.

**It is not faster than your profile, and that is the prefill lesson
again.** 78% less prefill, identical wall time (70 vs 72 s) and identical
output tokens: on a cached local server the request size was never the
cost. What the mode buys is passes and simplicity, not seconds.

**Against the worker alone it is within noise on passes (14 vs 15) and
16 seconds slower**, which is the difference between sampled and greedy
decoding plus the day's variance; the direct runs are the same recipe at
temperature 0. The nudge fired seven times here versus two in A3, which
is the sampled model's higher empty-turn rate (0c operator saw it too).

**What it gives up.** The parent's scoping and verification. Rung 5
passed anyway, as it does in direct mode, because the worker prompt's
completion facts carry it; nobody runs the tests independently
afterwards. In delegated mode the parent did, in every run.

**Decision:** the mode ships as `.pi/mellum/mellum-mode.ts` with
`/mellum on|off`, documented in the recipe as the second way to use the
worker. The delegated recipe stays the one with independent verification.

## Caveats

Three repeats, sampled decoding. The guard extension was loaded in every
run (the mode always loads it) although these records' `guards` field
says `False` and the table label omits `+guards`; the runner was corrected
afterwards. **Only the headless path was measured by the ladder**: with
`MELLUM_MODE=1` no on-marker is sent. The interactive path was then
exercised over Pi's RPC mode (`ladder/probe_mode_rpc.py`, 2026-10-09): on,
a second on, a task, off, a parent turn, a second off, and the one-shot
`/mellum <task>`; each request carried exactly the expected prompt,
history and tools, and the model was restored. The compaction guard is
unit-tested. After `/mellum off` the parent now receives one handoff block
per finished span instead of Mellum's tool calls (added 2026-10-09; the
probe's parent request went from 18 messages to 3). Pi loads
`-e` extensions before packages, so the filter runs *first* among payload
hooks and later handlers could re-add content; none of the operator's
packages hooks `before_provider_request` today. After `/mellum off` the parent's next request carries the
mode's tool results in full; collapsing them into a handoff block is
follow-up work.

Raw traces, stdout and diffs: [`ablation-a14-mellum-mode.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a14-mellum-mode.tar.gz).
