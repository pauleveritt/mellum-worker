# THEORIES

Untested theories — hunches worth logging before they are measured. This file
is a staging area, not a record of findings. A theory lives here while it is
still a guess; once a ladder run or a research note tests it, move the outcome
to `evals/` or `docs/superpowers/research/` and strike the theory through
here with a dated pointer.

Rules:
- One theory per row in the table; detail below under the same id.
- A theory is a falsifiable claim plus how you would test it. "X is better"
  with no test is a wish, not a theory.
- Do not promote a theory to a settled rule without evidence in `evals/`.
- Keep the table honest: `untested`, `screening`, `supported`, or `refuted`
  (with a pointer), never silently deleted.

| id | theory | proposed test | status |
|----|--------|---------------|--------|
| T1 | Ordering retrieved context chronologically (not just by relevance) raises correctness on tasks whose steps have an order | rung with ordered edits; compare `order:"score"` vs `order:"time"` in `mellum-context` | untested |
| T2 | A recency boost on BM25 (temporal ranking) beats plain BM25 when the newest facts override older ones | screen `mellum-context` with `MELLUM_CONTEXT_HALFLIFE_MS` set vs unset on a rung with a corrected fact | untested |
| T3 | SQLite FTS5 retrieval beats loading whole files into the prompt for large code / large data (the rung-12 class) | run rung 12 with `mellum-context` indexing `numbers.txt` vs the worker reading it directly | untested |
| T4 | Caching the stable system prompt and appending only changing context lowers cost with no accuracy loss | measure tokens + pass rate, cached-prefix vs spliced-context, same rung | untested |
| T5 | A skeptical "rethink" extension that pushes back on human claims contradicting ground truth lowers the wrong-answer rate | plant a false premise in a rung's user sentence; compare pass/escalation with and without `mellum-rethink` | untested |
| T6 | A small vision model lets the worker act on pdf / excel / word / screenshots it otherwise cannot read | a rung whose spec ships a requirement only inside a pdf/xlsx; pass needs `mellum-files` + `mellum-vision` | untested |
| T7 | The NCM verify gate cannot supply capability a model lacks — it only converts a near-miss into a pass | already hinted by 3-bit 3/8 and 1.5B 0/8; needs a preregistered gate×size run to confirm | screening |
| T8 | A mediated acceptance test rescues rungs 4 and 5 for the 6-bit: it self-exits on an incomplete multi-file refactor when nothing re-dispatches it | re-run rungs 4-5 with `scripts/screen.sh` mediated (frozen test + redispatch) vs the un-mediated 0/3 baseline | untested |

## T1 — Chronological context ordering
Relevance ranking can hand the worker the right passages in the wrong order. For
a task with ordered steps (migrations, a sequence of edits, an audit trail),
applying context in the order it happened should matter. `mellum-context`
supports `order:"time"`; the test is a rung where the steps must be applied in
sequence, scored with and without time ordering.

## T2 — Temporal BM25 (recency boost)
When a later fact corrects an earlier one, plain BM25 may still surface the stale
passage. A recency half-life should pull the correction to the top.
`rankScore` subtracts a recency term; set `MELLUM_CONTEXT_HALFLIFE_MS` and screen
against a rung that corrects a seeded fact.

## T3 — Retrieval beats loading for large context
Rung 12 sums a file far larger than the context window. The theory is that an
indexed, streamed retrieval path beats trying to load the file — and that the
same holds for large code projects, where the worker should search the index
rather than read every file.

## T4 — Prompt-cache layering
The system prompt and unchanging prompts are cacheable; changing contextual
prompts are not. Keeping the stable prefix identical and appending volatile
context after the cache boundary should cut cost without hurting accuracy. See
the build rule; the test is a token + pass-rate comparison.

## T5 — Skeptical pushback
A worker that trusts a human claim contradicting the ground truth will encode the
lie. A rethink extension that detects the contradiction and pauses to re-examine
should lower the wrong-answer rate. Plant a false premise in the user sentence and
compare.

## T6 — Vision and document understanding
JetBrains ships no vision model (Mellum is code and text only), so document and
image understanding needs a separate small vision model plus file extractors.
The theory is that this genuinely extends what the worker can do; the test is a
rung whose requirement lives only inside a pdf or a spreadsheet.

## T8 — Mediation rescues rungs 4 and 5
In the 6-bit sweep, rungs 4 and 5 fail 0/3 while the harder AgentClinic rungs
6-9 pass 3/3. Evidence (re-running both preserved workspaces): 2 failed, 2
passed each. The worker edits one file (totals.py or export.py), leaves the
coordinated change across export.py / totals.py / render.py unimplemented
(`render_rows()` never gets `mark_last`; `totals.py` crashes on a text cell),
and self-exits on the incomplete fix — `test_export.py` untouched, the rung-5
decoy untouched, so not cheating, just wrong. These runs had no acceptance test
(`acceptance_test: None`), so nothing re-dispatched the worker. The theory: a
mediated run (external frozen test + verify + redispatch) finishes the refactor
and flips 4 and 5 green. This is the "don't trust its self-exit" lead, seen in
the wild on the two simplest-looking rungs.

## T7 — The gate cannot supply capability
The mediated verify gate turns a near-miss into a pass on a capable model, but it
cannot lift a model that never gets close. Early signal: the 3-bit halved model
reached 3/8 and the 1.5B 0/8, and the NCM gate fired zero times on the capable
6-bit. A preregistered gate × model-size run would confirm or refute it.
