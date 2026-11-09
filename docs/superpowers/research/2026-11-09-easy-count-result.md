# Easy, Vanilla against Base: the count's result

## For Andre

- **Base missed the rule, on one clause out of three.** It took 25 strict passes to Vanilla's 2, and
  2.40 times the median requests, but 4.47 times the median output tokens against a limit of 3. The
  [rule](2026-11-08-easy-count-rule.md) was fixed before the first session, so `preset:base` and
  `preset:easy` stay `[]`.
- **What to look at:** the gain is large and the cost is larger than we said we would pay. Any
  different bar is a new decision, made in the open and not a re-reading of this one.
- **A hole in the unit:** the frozen test stayed readable in a temporary directory, and one Base
  session read it in full. See Risks.

**What is measured.** The table below, n = 32 per arm, from the tag
`checkpoint-2026-11-08-easy-final`. [Record and per-check table](../../../evals/2026-11-08-easy-final-count/table.md).

**What is conjecture.** Why the output tokens rise so far, and whether Medium or Hard behave alike.

| | Vanilla | Base | Rule | Met |
|---|---|---|---|---|
| Strict passes (of 32) | 2 | 25 | at least 8 more | yes (23 more) |
| Median requests, all sessions | 21.5 | 51.5 | at most 3 times | yes (2.40) |
| Median output tokens, all sessions | 7,598.5 | 33,993.5 | at most 3 times | **no (4.47)** |
| Full 13-check passes | 2 | 30 | reported beside | |
| Mean checks | 9.91 | 12.88 | | |
| Stalled | 7 | 0 | | |
| Ended on the budget | 0 | 10 | | |

The medians in `table.md` leave out stalled sessions; the rule's do not, so Vanilla's are the 21.5
and 7,598.5 here. The budget does not explain the miss: every session it ended was already above
Base's median, so a higher cap would leave the median where it is.

Output tokens here are the budget proxy's charge (`budget.spent.output_tokens`), which includes
compaction summaries; the rule did not name a count. The trace's own sum, `run.json`'s
`output_tokens`, leaves those out and gives Base 26,028, or 3.43 times. Both miss the limit. Base
compacted 52 times, Vanilla 5.

Figures the rule did not ask for, for reading and not for deciding:

- Vanilla's 28 misses of one check (of 31 graded sessions), `test_extending_page_can_override_layout_title`,
  are most of its lost full passes; Base missed it once.
- Output tokens per full pass, over all sessions: Vanilla 151,366, Base 36,633. Vanilla's figure
  rests on two passes.
- Median output tokens among full passes only: Vanilla's two spent 9,174 and 7,456, Base's thirty
  32,157.5 (3.87 times). Among strict passes only, Base's median is 21,552 (2.59 times). Either
  comparison rests on Vanilla's two sessions, so neither is an estimate.
- Base's five sessions with all 13 checks but no strict pass failed the project's own tests.

## Ladder run

Pod A40 under its host card, one session at a time, `scripts/r1_batch.py`, round-robin, session as
`mellum-session`, graded as `mellum-grade`. Arms in
[`arms.json`](../../../evals/2026-11-08-easy-final-count/arms.json). n = 32 per arm, Easy only,
budget 128 requests and 64,000 output tokens, stall 180 s. 64 sessions, 5.2 hours. The go-or-no-go
at n = 6 is in [its own record](../../../evals/2026-11-08-easy-final-screen/table.md): Base 5 strict
passes, Vanilla 0. One Vanilla session's checks never ran (it counts as zero).

## Persuasion → enforcement

Both of Base's units are enforcement: a timeout on every bash call and a re-run of an external test
before the session may end. Vanilla's 7 stalls, all on a server start, and Base's 0 show the first;
the re-dispatches (29 of 32 Base sessions, up to 3) are the second.

## What would falsify this / Risks

- **The frozen test was readable.** The settle half leaves its copy under `/tmp/mediated-*`, owned by
  the session user, and never deletes it. All 44 re-dispatch messages named the path, in pytest's
  output, and 41 carried a source line of the test. Two sessions looked; r27 read the whole test. It still passed
  strictly. Dropping it makes 24 strict passes and changes no clause. **Correction, 2026-11-09:** fixed
  after the count in `checkpoint-2026-11-09-settle-fixes`; the count's figures stand, with r27 noted.
- One suite, one host, one model. A different hardware or budget can move the token ratio.
- The mediated test covers the roadmap as written; a gap there is a gap in it too.
- A 4.47 ratio at n = 32 is well clear of 3, but a median over a spread this wide is not a tight
  estimate. Base's output ran from about 7,800 to 67,800 tokens.
