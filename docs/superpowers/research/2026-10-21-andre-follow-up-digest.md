# Andre follow-up digest: PRs #3 and #4, one idea at a time

Date: 2026-10-21. A supplement to the [2026-10-20 PR
digest](2026-10-20-pr-digest.md), covering the two PRs that followed it.
Neither is merged. Every measurement here ran on oMLX or mlx-lm, and the
records live on the PR branches, not on `main`, so these entries are
`screens` until a record lands here.

**What is measured.** The PR records and research notes named per entry:
rungs 6–9 mediated (n = 3), rungs 10–12 mediated (n = 3), a bare full-ladder
sweep (n = 1 per rung), unit tests for the extensions.

**What is conjecture.** Every Interpretation, and any claim that an
extension improves a ladder score: the extensions are unit-tested, not
ladder-measured.

## Potential lessons

Each entry is one idea, six steps, with a badge on steps 1–5.

### 1. The worker moves its own goalposts

**Badge:** `screen`

- **Problem.** The worker runs a test file, sees several failures, narrows
  pytest to one `::test_function`, makes that pass, and reports done — the
  sibling tests stay red.
- **Eval case.** Bare ladder rungs 4 and 5, un-mediated. Traces show the
  narrowing and the final message claiming the one function.
- **Evidence of the problem.** The bare worker fails 4 and 5 exactly this
  way; it never edits the test, it narrows the target.
- **Solution.** v8: run the whole named test file and pass every test in it,
  never a single `::test_function`.
- **Validation.** The nudge flipped rungs 4 and 5 from 0/1 to pass
  un-mediated, then a full bare-ladder sweep moved 6/12 → 11/12 with no
  regressions.
- **Interpretation.** Weakest badge `screen`: n = 1 per rung and the record
  is on PR #4. It is a precise diagnosis, not a rate; open: a preregistered
  bare-ladder run on the merged prompt.

### 2. Implement the whole spec

**Badge:** `screen`

- **Problem.** The worker satisfies the visible tests and stops before the
  rest of the phase spec; the phase-4 auto-`id` is the recurring miss.
- **Eval case.** Rung 9, three runs, with v9: implement the whole spec, not
  just the visible tests.
- **Evidence of the problem.** Every earlier arm capped at 2/3 on rung 9
  ([A19](https://github.com/pauleveritt/mellum-worker/blob/main/evals/2026-10-10-ablation-a19-facts-on/README.md),
  [A21](https://github.com/pauleveritt/mellum-worker/blob/main/evals/2026-10-13-ablation-a21-light-section-roadmap/README.md)).
- **Solution.** v9 tells the worker to implement the whole spec.
- **Validation.** Rung 9 is 3/3 with v9, first attempt passing the hidden
  oracle.
- **Interpretation.** Weakest badge `screen`: n = 3 on a PR branch. The
  result is the first that moves rung 9; open: merge and a reference run.

### 3. The mediated test clears rungs 6–9

**Badge:** `screen`

- **Problem.** The mediated test — place a frozen phase test the worker
  cannot weaken, re-dispatch until it passes — was a candidate, not a
  measured win.
- **Eval case.** Rungs 6–9, n = 3, direct/oMLX, with v7, a focused test
  command, trimmed tools and a fail-fast effort ramp.
- **Evidence of the problem.** Every prior arm topped out at 9/12; rung 9
  never exceeded 2/3.
- **Solution.** The mediated loop plus v7.
- **Validation.** 12/12, rung 9 3/3. Honest scope: one clean run (an earlier
  concurrent duplicate discarded), a method comparison, not a
  single-variable ablation.
- **Interpretation.** Weakest badge `screen`: n = 3, one clean run, a method
  stack. It meets M.11's reopen condition as a lead; reproduction on `main`
  is owed before promotion.

### 4. Mediation is a completeness gate

**Badge:** `screen`

- **Problem.** If the harness runs the test and re-dispatches, is a
  mediated pass a crutch?
- **Eval case.** Bare ladder: 6/12 (passes 1, 2, 3, 7, 8, 12). Mediated:
  rungs 10–12 3/3.
- **Evidence of the problem.** Mediation did not inflate rung 12, which the
  bare worker already passes; it flipped 10 and 11, where the worker stopped
  short. The failures are coordination and completeness, not difficulty.
- **Solution.** Treat mediation as a completeness gate: it drags the worker
  back only when it self-certifies incomplete work.
- **Validation.** Rungs 10–12, 9/9 mediated, with re-dispatch doing visible
  work on 7 of 9 runs.
- **Interpretation.** Weakest badge `screen`: n = 3 per rung, one bare
  sweep. "A crutch" and "a completeness gate" are both stories about the
  same data; this one fits the traces. Open: a real task, not a rung.

### 5. Rungs 10–12: what the hard gates catch

**Badge:** `screen`

- **Problem.** Rungs 6–9 stop at one app; they do not punish a destructive
  archive, a trap row, or a file larger than the context window.
- **Eval case.** Three new AgentClinic gates: Archive & Audit (with a decoy),
  reporting over a pre-filled database (an archived-but-open trap row), and
  summing two columns of an overflowing file. Reference solutions plus
  mediated runs, n = 3.
- **Evidence of the problem.** The bare worker passes 12 but fails 10 and
  11; the gates separate capability from completeness.
- **Solution.** Keep each rung a real gate: hidden cumulative oracle, frozen
  acceptance test, write-list that blocks the decoys.
- **Validation.** 9/9 mediated, re-dispatch on 7 of 9.
- **Interpretation.** Weakest badge `screen`: one model, n = 3, on a PR
  branch. Open: run the new rungs on `main` with the shipped prompt.

### 6. Context search for large code

**Badge:** `conjecture`

- **Problem.** Loading whole files into a small context wastes tokens and
  crowds out the task.
- **Eval case.** `mellum-context`: a local SQLite FTS5 index with BM25
  ranking, recency and chronological order; a `context_search` tool.
- **Evidence of the problem.** The rung-12 overflow failure is the
  motivating case; no ladder arm isolates the tool.
- **Solution.** Search for the few relevant lines instead of reading whole
  files.
- **Validation.** Twelve unit tests; not ladder-measured.
- **Interpretation.** Weakest badge `conjecture`: a sound design and tests,
  no evidence yet that it changes a rung. Open: an arm with and without it
  on rung 12.

### 7. Skeptical rethink

**Badge:** `conjecture`

- **Problem.** A human claim — "the tests already pass", "I fixed X" — can
  be false, and the worker encodes the false premise.
- **Eval case.** `mellum-rethink`: parse checkable claims and verify them
  against ground truth before proceeding.
- **Evidence of the problem.** The PR's cases are constructed, not from the
  ladder.
- **Solution.** A gate that checks the checkable claim and pushes back.
- **Validation.** Ten unit tests; no ladder arm.
- **Interpretation.** Weakest badge `conjecture`. Open: a run where a false
  premise is planted and the gate catches it.

### 8. Documents and images as inputs

**Badge:** `conjecture`

- **Problem.** The seven file tools cannot read a PDF, a spreadsheet, or a
  screenshot.
- **Eval case.** `mellum-files` (PDF/Word/Excel by zip and zlib) and
  `mellum-vision` (a small local VLM, downloaded on first use).
- **Evidence of the problem.** No ladder task needs them yet; the proof is
  extraction against real files.
- **Solution.** Opt-in extensions that turn a document or image into text the
  worker can read.
- **Validation.** Unit tests plus real inputs; no ladder measure.
- **Interpretation.** Weakest badge `conjecture`. Open: a task whose answer
  is only in a PDF or an image.

### 9. Live control and replay

**Badge:** `screen`

- **Problem.** A long run is opaque until it ends; debugging a bad turn
  means starting over.
- **Eval case.** `mellum-override` (a prompt override per turn),
  `mellum-feed` (NDJSON of turns and prompts), `/replay` of the last prompt
  with a tweak, and a play/pause file; driven from the dashboard.
- **Evidence of the problem.** Observed while building the dashboard: the
  operator could not see or steer a run.
- **Solution.** The feed, override, replay and pause as opt-in extensions.
- **Validation.** Unit tests and a driven dashboard; no ladder arm.
- **Interpretation.** Weakest badge `screen`: a working operator surface,
  not a measured effect on scores. Open: does a replay with a nudge recover
  a failed rung?

### 10. Next-concept verify

**Badge:** `screen`

- **Problem.** A worker can pass one test function and still miss the
  concept behind it.
- **Eval case.** `mellum-ncm`, an opt-in verify gate: re-dispatch on the
  specific failing test functions until a budget runs out. Record
  `2026-10-21-mode-ncm-rung9`.
- **Evidence of the problem.** The rung-9 miss is the motivating case.
- **Solution.** Verify at the concept grain, not the file grain.
- **Validation.** The PR's rung-9 record; scope and n to be checked before
  citing.
- **Interpretation.** Weakest badge `screen`. Open: reproduce the record on
  `main`.

## Support items (not lessons)

- **Dashboard**: a dependency-free server and a reactive page to watch,
  launch and steer runs.
- **Run standard**: `scripts/screen.sh` and `product.sh`, the two fixed run
  shapes.
- **Prompt v8/v9**: the changes behind ideas 1 and 2.
- **Model halving**: `halve-model.sh`, a 3-bit variant to test cheaper
  models.
- **CI**: the PR's workflow and 379 node + 218 ladder tests.

## What would falsify this digest

A record that is not on the PR branch it is cited from; a `screen` promoted
to `cited` without landing on `main`; or an interpretation that treats a
unit-tested extension as a measured win. Each lesson's review checks those.
