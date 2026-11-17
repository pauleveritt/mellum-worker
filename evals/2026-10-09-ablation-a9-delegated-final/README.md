# Ablation A9: delegated confirmation of the lean worker (prompt v4)

Date: 2026-10-09. [A8](../ablation-a8-delegated-lean/README.md) again, with
the agent file in its final form: prompt v4, `excludeTools: contact_supervisor`
restored, no `thinking:`, `allowedAgents:`, or `defaultContext:` lines, guards
at their default (nudge cap 3, loop breaker live), no parent-side skill.

```bash
uv run python -m ladder.run_ladder --mode delegated --profile baseline --guards --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/ablation-a9-delegated-final
```

| rung | 3a (v3, full frontmatter) | A8 | A9 (ships) |
| --- | --- | --- | --- |
| 1 | 3/3 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 | 3/3 |
| 4 | 3/3 | 3/3 | 2/3 |
| 5 | 3/3 | 2/3 | 3/3 |
| total | 15/15 | 14/15 | 14/15 |

| measure (15 runs) | 3a | A9 |
| --- | --- | --- |
| child tools offered | the seven | the seven (`contact_supervisor` gone again) |
| child system prompt, chars | 3,580 | 3,174 = v4 (1,134) + pi-subagents' "Intercom orchestration channel" block, which `excludeTools` does not remove |
| runs that delegated / re-dispatched | 15 / 0 | 15 / 2 |
| child requests per run, mean | 11.0 | 11.5 |
| child tool errors | 2 | 5 |
| brief length, mean chars | 1,260 | 1,195 |
| parent ran the tests itself | 15 | 15 |
| children that "produced no output" (pi-subagents' error) | 3 runs | 3 runs |

## The failure

Rung 4 r3: the child edited `totals.py`, then its next turn was empty
(`stopReason: stop`, text `"\n\n"`). pi-subagents ended the run with
"Subagent produced no output". The parent re-dispatched; the second child
read three files and went empty again after three tool calls. The parent
then stopped, reported "blocked (mellum-worker lane failing)" with the
partial diff and both run ids, and did not claim success. That is the
correct parent behaviour and the honest failure of the night.

## The finding: the nudge does not fire inside a delegated child

In direct mode the nudge recovered every empty turn in phase 2b (seven of
seven). In sixty delegated runs (3a, 3b, A8, A9) the child's `nudges`
column is zero while eleven runs contain pi-subagents' "produced no
output" error, which is exactly the empty turn. The child's request trace
for rung 4 r3 shows the run ending at the empty turn with no continuation
request. pi-subagents ends a child run on an empty terminal assistant
message before an `agent_before_settle` continuation can act, or does not
forward that hook to children at all; the source has no reference to it.

So in the delegated recipe the recovery is the *parent's* re-dispatch,
which worked in ten of the eleven occurrences (58/60 passes across the
four delegated phases; the other miss was an async launch), not the
extension's nudge. The extension's nudge
is a direct-mode guard. Making the empty turn recoverable inside the child
under pi-subagents is the first item on the backlog, with a cheaper
alternative beside it: the worker's advertised description could tell the
parent what the skill used to ("re-dispatch once on 'produced no output'").
Neither is done; the parents here did it unprompted.

**Decision (superseded by A10):** the worker was to ship as measured here;
the review then reopened A3 and prompt v5 was confirmed in A10. 14/15 is within one of
the reference and the one failure is the known pathology with the parent
behaving correctly.

Raw traces, stdout and diffs: [`ablation-a9-delegated-final.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a9-delegated-final.tar.gz).
