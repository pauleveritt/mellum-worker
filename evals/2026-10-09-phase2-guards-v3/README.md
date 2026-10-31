# Phase 2: guards, baseline profile, worker prompt v3

Date: 2026-10-08. Same launch, profile (baseline), prompt (v3), rungs, and
repeats as [phase 0b](../phase0b-baseline-v3/README.md), plus
`.pi/extensions/mellum-guards.ts` loaded in the child (`--guards`).

## Which guards, and why

The spec's rule: a guard is enabled only for a ladder column that was
non-zero. After 45 runs with prompt v3 (phases 0b, 1, 1b):

| column | runs | guard | decision |
| --- | --- | --- | --- |
| `write_shrink` (fragment-as-whole-file clobber) | 0 | new-file-only `write` | **dormant** |
| calls the ported loop breaker would refuse, replayed with its exact semantics (`loop_breaker_would_block`) | 1 of 105 runs: the 66-request thrash (5 r3), 3 calls, a failed run; no passing run touched | loop breaker | **dormant**, but the evidence now argues for it — it would have cut the one thrash and cost nothing elsewhere |
| `deadline_hit` | 0 | step budget | **dormant** |
| `empty_final` | 7, including all 5 failures | empty-final nudge | **enabled** |

The nudge: when the agent is about to settle and its last assistant turn had
no text and no tool call, propose one custom message —
"[mellum-guard] Your last turn ended with no reply and no tool call. The
task is complete only when the test command exits 0. Continue…" — and ask
for one more model request. Pure decision function, tested; the Pi adapter
hooks `agent_before_settle`.

Command:

```bash
uv run python -m ladder.run_ladder --profile baseline --guards --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase2-guards-v3
```

Two corrections. First (final review): the dormancy decision was taken on
`max_identical_streak` (adjacent repeats only), but the breaker counts
repeats within a 20-call window. Second (external review): my rescoring
counted five occurrences *including* the current call, while the breaker
refuses a call only when five matches already sit in the window — it blocks
the sixth. Replayed with the breaker's exact semantics over all 105 traces,
it would have blocked three calls in exactly one run, the failed 66-request
thrash, and nothing in any passing run. My earlier statement that it would
have refused re-reads in passing runs was wrong. `loop_breaker_would_block`
is now the scorer column, computed by that replay.

## Result

| rung | baseline, no guard (0b) | baseline + nudge (2) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 3/3 | 2/3 |
| 5 | 3/3 | 1/3 |

12 of 15. The nudge fired in three runs:

| run | nudges | outcome |
| --- | --- | --- |
| 4 r1 | 1 | **recovered**: after the nudge it read the three files, fixed `totals.py`, ran the tests to green, and reported "Files changed: totals.py, render.py, export.py" |
| 4 r2 | 2 | not recovered: both continuations ended empty again; 13 requests; no file changed |
| 5 r3 | 2 | not recovered, and worse: 66 requests, 12 edit anchor failures, 6 whole-file writes, two `cat > export.py <<'EOF'` heredocs, a 166k-char prompt, ending empty |

The other rung-5 failure, 5 r1, was not nudged: it reported failing tests
honestly and stopped with text. 5 r2 passed.

## Reading

**The nudge works when the stop was a lapse and hurts when it was a stall.**
One of three empty finals was a model that had simply not written its
reply; a single nudge finished the job. The other two were models that had
nothing further to do and said so by stopping; nudging them twice produced
either two more empty turns or a sixty-six-request thrash that surfaced, for
the first time in 60 runs, the heredoc-write channel (`bash_file_mutations`
2) and an anchor-failure cascade (12) — the pathologies local-ai-pi
recorded, appearing only once the run was pushed past its natural end.

With three repeats the gate cannot separate 12/15 from 15/15 (phase 0b)
or 13/15 (phase 1); the empty-final rate itself varied 1–4 per 15 across
identical configurations. What the three nudged runs do establish:

- The second nudge never helped. `ENABLED.emptyFinalNudge` was set to **1**
  after this run. External review then showed the cap does not bound what a
  nudge starts: in 5 r3 the first nudge landed at request 33, both heredoc
  writes at 58–59, and the second nudge only at 64 — thirty-one requests
  ran under a single nudge. A cap of one is therefore not a bounded remedy;
  the continuation itself needs a request or progress bound, and the
  one-nudge configuration has not been measured. **The nudge is
  experimental**, kept on through phase 3 so the delegated runs are paired,
  and to be made dormant (or bounded and re-measured) after them.
- The "lapse versus stall" reading assigns causes the experiment did not
  establish; it is an interpretation of three runs, not a finding.

**Where the empty-final problem actually belongs.** In the real recipe the
worker is a child of a parent session. A parent that reads the child's
final text and finds it empty can re-run the tests itself (as it did in
the first interactive run) or re-dispatch with a tighter brief; that is
phase 3's parent-side skill, and it has what the child lacks — the
sentence the user typed and the test result. The child-side nudge stays
enabled at 1 as a cheap first attempt, and ships with the dormant guards in
the same file.

## Attempt 1

`../phase2-guards-v3-attempt1/` ran the same configuration with the nudge on
`turn_end`. 15 of 15, but its one empty final was never nudged: Pi reports
`canContinue: false` on the final turn, and the handler deferred to it. A
print-mode probe showed `agent_before_settle` honours `continue: true`
there; the guard was moved and this phase re-run. Attempt 1's traces
remain as the record of the hook mistake.

## Proof the extension loads

`MELLUM_GUARDS='{"stepBudget":1}'` on a rung-1 run blocked the second tool
call and the model summarised and stopped, as the block reason asked. A
blocked call emits no `tool_result` event in `record-pi.js`; blocks are
visible in the next provider request and in `stdout.txt`, not in
`tool_errors`.

Raw traces, stdout and diffs: [`phase2-guards-v3.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase2-guards-v3.tar.gz).
