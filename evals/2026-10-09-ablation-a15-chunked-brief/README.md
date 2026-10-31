# Ablations A15 and A16: the Markdown brief, chunked and in one prompt

Date: 2026-10-09. The brief as the mediator between the user and the
executor. One fixed Markdown document per rung (`ladder/briefs/rung<N>.md`):
a header with the task, the test command and the do-not-touch files, then
`## Step` sections (read and restate; one edit per file; run the tests
until they exit 0; report). Two ways to deliver it, both under
[A3](../ablation-a3-v4b/README.md)'s settings (direct, greedy, prompt v5,
bounded guards):

- **A15, chunked:** one Pi invocation per step, continuing one session
  (`--session-dir`/`--session-id`), so each turn is bounded and "tests at
  the end" is a step the runner guarantees. 4–6 prompts per rung.
- **A16, one prompt:** the same document as a single prompt. The control
  that separates the brief's content from the splitting.

```bash
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode chunked --guards --profile tuned --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/ablation-a15-chunked-brief
MELLUM_GUARDS='{"emptyFinalNudge":3,"loopBreaker":true}' uv run python -m ladder.run_ladder --mode brief   --guards --profile tuned --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/ablation-a16-brief-one-prompt
```

| rung | A3 sentence, one prompt | A16 brief, one prompt | A15 brief, chunked |
| --- | --- | --- | --- |
| 1 | 3/3 | 2/3 | 3/3 |
| 2 | 3/3 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 | 3/3 |
| 4 | 3/3 | 1/3 | 3/3 |
| 5 | 3/3 | 2/3 | 3/3 |
| total | 15/15 | 11/15 | 15/15 |

| measure (15 runs) | A3 | A16 | A15 |
| --- | --- | --- | --- |
| prompts per run | 1 | 1 | 5.0 |
| requests per run, mean / max | 14.3 / 27 | 7.7 / 14 | 21.8 / 33 |
| output tokens per run, mean | 5,344 | 2,721 | **13,220** |
| prefill, k chars per run | 308 | 105 | 775 |
| tool errors / nudges | 17 / 2 | 8 / 3 | 16 / 6 |
| wall seconds per run, mean (untrusted) | 54 | 29 | **130** |
| wall by rung | 18 / 36 / 21 / 87 / 108 | 11 / 41 / 19 / 16 / 57 | 40 / 120 / 47 / 190 / 254 |

## Reading

**One prompt with steps in it: the model stops at the first "reply".**
Three of A16's four failures ended with a 29-character final after two,
three and seven requests, with no source file changed: the model did Step 1
("read … reply with one line"), replied, and treated the turn as done.
The fast times are the times of not doing the task. A step-wise document
is read as a conversation script, not a work order; a one-prompt brief
must not contain intermediate "reply" instructions. The brief shape worth
measuring on its own (files, change, test command, done-when, with no
steps) was not run here.

**Chunked: every rung passes, at 2.4× the time and 2.5× the output.**
Each step is a full turn that re-reads what the previous step read and
reports what it did, so on rung 2 the model made 27 requests for a task
the sentence finished in 10, and rung 5 took 254 seconds against 108.
The bounded turns did not reduce empty finals (six nudges against two).
What the runner guaranteed, tests at the end, the v5 prompt's completion
facts already produce.

**Decision:** neither ships. The sentence plus v5 remains the cheapest
reliable input to the worker. Both modes stay in the runner (`--mode
chunked`, `--mode brief`) with the briefs, for the "no steps" brief
experiment and for verification-between-steps, which this phase did not
measure.

Raw traces, stdout and diffs: [`ablation-a15-chunked-brief.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a15-chunked-brief.tar.gz).

*2026-10-13: the ladder code this phase used (`--mode chunked`, `--mode brief`, `ladder/briefs/`) was removed as rejected; it last exists at commit `44e1b0b`. The launch line above is history.*
