# Ablation A8: delegated confirmation of the lean worker (first pass)

Date: 2026-10-09. [Phase 3a](../phase3a-delegated-noskill/README.md)'s
command, with the worker as it stood after A2, A6, and A7: prompt v4,
guards at their new default (nudge cap 3, loop breaker live), no
parent-side skill, and the frontmatter without `excludeTools`,
`allowedAgents`, and `defaultContext`.

```bash
uv run python -m ladder.run_ladder --mode delegated --profile baseline --guards --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/ablation-a8-delegated-lean
```

| rung | 3a | A8 |
| --- | --- | --- |
| 1–4 | 12/12 | 12/12 |
| 5 | 3/3 | 2/3 |

| measure (15 runs) | 3a | A8 |
| --- | --- | --- |
| runs that delegated / re-dispatched | 15 / 0 | 15 / 2 |
| child requests per run, mean | 11.0 | 10.7 |
| child tool errors | 2 | 3 |
| nudges / empty finals | 0 / 0 | 0 / 0 |
| brief length, mean chars | 1,260 | 1,247 |
| child tools offered | the seven | the seven **plus `contact_supervisor`** |
| child system prompt, chars | 3,580 | 3,174 (v4 plus an injected "Intercom orchestration channel" block) |

## Two findings

**`excludeTools: contact_supervisor` was load-bearing; A6 was wrong about
it.** The pi-subagents docs describe `excludeTools` as narrowing the
`tools` allowlist, and `contact_supervisor` is not in the allowlist, so the
line looked redundant. In fact pi-subagents injects `contact_supervisor`
into every child and appends a supervisor-protocol block to the child's
system prompt regardless of the allowlist; the line was what kept both out.
Two children called the tool (rung 1 r3, rung 5 r3; both runs still
passed). The line goes back. The other two removals stand: no run showed a
descendant launch or a forked context.

**The failure is the parent's, and new.** Rung 5 r2's parent launched the
child *asynchronously*, told the user "I'll verify when it reports back",
and ended its turn. Headless, nobody comes back; the child's partial edit
(`totals.py` only) is what the check scored. 3a and 3b never saw an async
launch in 30 runs. n = 1, and the parent is a hosted model; recorded, not
acted on. If it recurs, the fix is a line in the worker's advertised
description ("launch synchronously"), which reaches the parent
unconditionally.

**Decision:** restore `excludeTools`, remove the inert `thinking: high`
(A5), and run the delegated confirmation once more with the file as it
ships (A9).

Raw traces, stdout and diffs: [`ablation-a8-delegated-lean.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a8-delegated-lean.tar.gz).
