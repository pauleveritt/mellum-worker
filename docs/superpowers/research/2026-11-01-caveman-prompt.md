# Does a telegraphic ("cave-man") prompt help the small model?

## What is measured

A prompt-register ablation on the thin worker, Q4_K_M, local M3 Max, n=3 per
cell, easy + medium suites, deadline 1800s. Two arms, identical content, only
the register differs:

- **v11** — the shipped worker prompt (`prompts/mellum-worker.md`).
- **caveman** — the same instructions rewritten telegraphically (short
  imperatives, keywords, minimal grammar); `MELLUM_MODE_PROMPT` pointed at it.

Both ran the worker arm only (vanilla is prompt-independent). Recorded in the
scoreboard as `…-Q4_K_M` (v11, the `local-q4-thin` worker cells) and
`…-Q4_K_M caveman-prompt`.

| suite | prompt | pass | avg turns | avg wall |
| --- | --- | --- | --- | --- |
| easy | v11 | 2/3 | 48 | 3:09 |
| easy | caveman | 2/3 | 36 | 2:23 |
| medium | v11 | 0/3 | 77 | 5:19 |
| medium | caveman | 0/3 | 63 | 5:48 |

**Result: null on pass rate.** The telegraphic register changed neither suite's
pass rate (2/3 = 2/3, 0/3 = 0/3). A secondary signal: caveman ran ~25% fewer
turns on both suites and was faster on easy.

## What is conjecture

- That the fewer-turns effect is *leanness* rather than *earlier give-up*. The
  caveman medium had a 46-turn rep that may be a premature exit, and the passing
  rep set is not identical across arms, so "a leaner pass" is a lead, not a rate.
- That the null transfers off Q4 / off these suites. Register could matter more
  where the task is longer or the instructions compete.

## Decision

Do not adopt a telegraphic prompt. It buys no correctness on this model, and the
turn reduction is ambiguous (leaner vs. quits sooner). This corroborates the
earlier finding that prompt *wording* is largely null on these suites
(LC.11/LC.11A: `no-prompt` scored the same as the full prompt); what moves pass
rates is harness structure — backgrounding servers, the verify-and-redispatch
gate, phase-scoping — not how the prompt is phrased.

## What would falsify this

A preregistered run at n ≥ 3 on a cell where caveman's pass rate differs from
v11's by more than one session, or a Q8/BF16 run where the register splits the
rate. The turn-count lead would be worth a real look if a leaner arm ever
*raised* the pass rate (a shorter pass is a better pass), rather than leaving it
flat as here.

## Risks

n = 3 is a screen for a comparison; one cell is one host, one quant. Treat the
null as "no evidence of help here," not "proven no effect everywhere."
