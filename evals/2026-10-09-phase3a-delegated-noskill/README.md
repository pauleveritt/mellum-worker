# Phase 3a: delegated mode, no skill

Date: 2026-10-08. The recipe as a user runs it: a normal Pi parent — the
operator's profile mirrored into a temporary agent directory (DeepSeek Flash
as the default model, Superpowers and pi-subagents installed, context7),
Superpowers' bootstrap active — given the sentence
`Use mellum-worker to do this: <rung sentence>`. The parent decides how to
brief the child. The child is the committed worker (prompt v3, guards on with
the nudge capped at 1, oMLX baseline profile) with the ladder's recorder
appended in the scratch copy of its agent file. Three repeats per rung,
900 s deadline. The child's requests carried the operator profile's Pi
defaults (`temperature 1, top_p 0.95, top_k 20, max_tokens 16384`), as in
every earlier phase.

Command:

```bash
uv run python -m ladder.run_ladder --mode delegated --profile baseline --guards --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/phase3a-delegated-noskill
```

## Result

| rung | direct, phase 2 | delegated, 3a |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 2/3 | 3/3 |
| 5 | 1/3 | 3/3 |

15 of 15. Every run delegated (`subagent` called once with
`agent: mellum-worker`); no re-dispatch; no nudge fired; no empty parent
final; `loop_breaker_would_block` 0. Full columns in [table.md](table.md);
each run directory holds the parent's brief as `brief.md`.

| measure (15 runs) | value |
| --- | --- |
| brief length, chars | 315–1,994, mean 1,260 |
| child requests per run, mean | 11.0 (direct phase 2: 17.8) |
| child tool errors | 2 runs (one anchor failure each) |
| parent assistant messages per run, mean | 6.6 |
| parent tool calls per run | 4–17 |
| runs where the parent ran the test command itself | 15 of 15 |
| wall seconds per run, mean (untrusted) | 62 |

## What the parent did without being told

The parent scoped every task before dispatching. A rung-5 brief
([rung5 r2](rung5-baseline-delegated-guards-r2/brief.md)) names the three
files, restates all four tests with their expected values, forbids edits to
the test file and the decoy, names the test command, and asks for the test
output back. After the child returned, the parent ran the tests itself in
every run before reporting.

So in delegated mode the "B before A" distinction collapses: a frontier
parent performs option A — parent-side scoping and verification — natively.
The child never received the user's sentence; it received a brief that
already had the answer's shape. That is why rung 5, which failed 2 of 3 in
direct mode, passed 3 of 3 here with fewer child requests.

What this does not show: that the parent's native scoping is reliable on
tasks larger than these fixtures, or that a weaker parent would do the same.
Phase 3b asks what an explicit skill adds on top of this behaviour; the
pass rate has no room to improve, so the comparison is about brief shape,
verification, re-dispatch, and cost.

## Caveats

Three repeats; the parent is a hosted model whose behaviour can change
between days; sampled decoding on both parent and child. The setup
warning `extensions: [] override ... disables ALL ambient extensions` from
pi-subagents appears on every run and is the intended effect.

Raw traces, stdout and diffs: [`phase3a-delegated-noskill.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase3a-delegated-noskill.tar.gz).
