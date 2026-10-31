# Eval-suite pipeline design: load, run, replay and submit

Date: 2026-10-22. Decided with Andre in chat (Superpowers brainstorming).
Inputs: this session's bare-vs-harness runs (ladder 6/12 bare; lesson suites
bare 0/3, harness-on 4/4 · 12/18 · 21/34 on the hidden graders), the fixed
`grade()` (drop the shadowed strict copy, keep `F,E9`; commit `5004187`), the
`mellum-quality` finish check (`431a146`), and two measured determinism
findings recorded in section 2. Andre's four choices drive the design: replay
re-executes the same temperature, prompt and seed and compares the model feed
(its own, or another model's); contributors submit a portable bundle file;
the ladder rungs and the learn suites unify into one format now; and a bounded
determinism track runs alongside.

Not yet built: nothing here ships until a plan carries it out. The worker,
prompt, guards and the Learning Center suites are unchanged by this design;
it adds a pipeline around them. The lesson suites remain Paul's — unification
preserves their hidden-grader and qualify contract and never edits a suite to
make the worker pass.

## 1. Goals

- Let anyone, on any machine, load an eval suite, run the worker against it,
  and record the run as one portable file others can read.
- Replay a recorded run: re-execute its exact temperature, prompt and seed,
  capture the model feed, and compare it — against the recorded feed (did it
  reproduce?) or against another model's feed (A versus B on identical input).
- Let contributors submit their runs for review and learning, and let a
  maintainer review a run without re-staging anything.
- Tell the truth about reproduction: the recording is always faithful;
  re-execution is not bitwise-reproducible on the current backend, and the
  design says so rather than implying a seed guarantees a rerun.

## 2. Measured constraints

Two results from this session ground the whole design; both are `screen`
(n is small), but both point the same way.

- **A seed does not reproduce a run.** The same prompt with `seed: 42` at
  temperature 1.0, sent twice to oMLX, returns different text.
- **Greedy does not reproduce either.** The same prompt at `temperature: 0,
  top_k: 1`, sent twice, still returns different text.

So the nondeterminism is in the backend — MLX reductions, kernels, batching
or the thinking path — not in sampling. The record a run writes (every prompt
sent, every response, every tool call and result) is reproducible because it
is a capture. Re-execution is not, until the determinism track in section 8
passes its exit test. Replay is built to be useful before that lands and more
exact after it.

## 3. The unified eval-suite format

One schema both the ladder rungs and the learn suites adopt. A suite is a
directory the loader reads:

- `suite.toml` — id, version, kind (`coding`, `agentclinic`, …), the phases in
  order, the write-list (paths the worker may change), the test command, the
  deadline, and the oracle (the hidden-grader entry point).
- `base/` — the starting workspace the worker sees.
- `prompts/NN.md` — one per phase, or a single `task.md` for a one-shot suite.
- `grader/` — the hidden graders, withheld from the workspace until the worker
  has exited.
- `expected.json` — the test ids the oracle must report as passing (a superset
  of any visible test, so passing means the phase is done, not that one
  function works).
- `fixtures/known-good` and `fixtures/known-broken` — qualify the grader in
  both directions before any run counts.

The ladder rungs (calculator, ledger, rename, feature, edge, and
agentclinic-p1 through p7) become suites under this format; the learn easy,
medium and hard suites already carry most of it. One loader and one runner
replace the two parallel mechanisms (`ladder/` and `learn/code/harness.py`),
which retire once every rung is ported and its numbers reproduce.

Unification is behaviour-preserving: a ported rung must score the same as
before on the same input, proven by re-running it, not asserted.

## 4. The run bundle

The unit a run produces and a contributor submits: one self-contained,
path-free file (a zip), so another machine loads it without edits. It holds a
manifest and three records.

The manifest states the schema version, the suite id and version, the model
(provider, id, quant), the full sampling block (temperature, top_p, top_k,
min_p, **seed**, max_tokens, thinking budget), the arm or profile and the
guard and quality configuration, the prompt version, the tool versions (pi,
omlx, uv, ruff), and the score (the suite verdict, the per-test pass and fail,
and the metrics — requests, wall, tokens).

The three records are the model `feed` (every prompt sent and every response —
the thing replay compares), the Pi `trace` (tool calls, results, guard and
quality decisions), and the `workspace.diff` (the worker's changes against
`base/` — the code it produced).

The seed and sampling block are stored as provenance and for the day the
determinism track lands; the bundle is faithful regardless of backend
determinism, because the feed and trace are a capture.

## 5. Load and run

- `eval load <id>` stages a fresh workspace from the suite's `base/`, withholds
  the grader, and qualifies it (known-good passes, known-broken fails) before
  anything runs.
- `eval run <id> [--arm bare|worker|mediated] [--model M]` runs the worker,
  grades it with the fixed `grade()` and the hidden oracle, and writes a
  bundle. The arm selects the scaffolding: `bare` is stock Pi with no
  additions, `worker` is the v11 prompt and the guards, `mediated` adds the
  frozen acceptance test and redispatch.

Grading stays split as this session established: the hidden grader is the
verdict (does the work the spec asked for actually work); lint and complexity
are reported but never style-gate a working solution.

## 6. Replay and compare

The heart of the pipeline, in Andre's words: a replay runs the same
temperature, prompt and seed, checks the feed from the model, and can compare
another model's feed.

`eval replay <bundle> [--model B] [--prompt-delta "…"]`:

1. Re-execute the bundle's suite at its exact sampling block (or swap the model
   for B, or append a prompt delta).
2. Capture the new feed.
3. Compare the new feed against the bundle's feed.

The comparison answers a different question per invocation: the same model asks
*did it reproduce?*; `--model B` asks *how does B differ from A on identical
input?*; `--prompt-delta` asks *did the change help?* — the faithful successor
to today's `mellum-replay`, which re-drives the model with a tweak but captures
nothing to compare.

Because the backend is not bitwise-deterministic yet (section 2), comparison
has layers, and a replay names which it used:

- `structural` (the default, available now): same tool-call sequence, same
  files touched, same verdict. Robust to token-level nondeterminism.
- `semantic` (now): edit distance and key-span match over the feed text.
- `exact` (gated on the determinism track): the feed is bitwise identical.

The output is a diff report: the verdict delta, the tool-sequence delta, and
the feed similarity, so a reviewer sees what changed without reading two
traces by hand.

## 7. Submit, review and learn

- `eval submit <bundle>` packages the portable file; the contributor sends it
  however they like (no git or service assumption — Andre's choice).
- `eval review <bundle>` (for a maintainer) loads the bundle, shows its score
  and a diff against a reference bundle, and replays or compares on request.
  Review is reading the bundle plus an optional replay, not re-staging a run.
- Learning is the corpus: bundles accrete, `eval compare <A> <B>` diffs two,
  and the existing `mellum-learn` ("name what went wrong across the last n
  runs") reads bundles instead of only local records.

A submitted bundle is data, not instructions: review treats its manifest and
feed as evidence to weigh, and nothing in a bundle changes how the reviewer's
tools behave.

## 8. The chase-determinism track

A bounded research line, run alongside the pipeline, not blocking it. It has
one exit test: two identical greedy calls return bitwise-identical feeds.

Steps, cheapest first: pin `mx.random.seed` per request; force deterministic
MLX reductions; serve single-stream with batch size one; fix the thinking
budget. If oMLX cannot be made deterministic, evaluate a deterministic backend
(llama.cpp greedy with `--seed` and batch one) and record the verdict in
`docs/superpowers/research/`.

Until the exit test passes, replay uses `structural` and `semantic`; when it
passes, `exact` unlocks, seeded re-execution becomes a real reproduction, and
the bundle's stored seed stops being only provenance. The track is `screen`
until then, and no lesson claims reproduction it has not shown.

## 9. What it builds on

The pipeline evolves parts that already exist rather than starting over:
`mellum-feed.ts` (the feed), `mellum-record.ts` and `run.json` (the record and
score), `trace.jsonl` (the trace), `mellum-replay.ts` (from tweak-and-rerun to
faithful replay and compare), `load_suite` and `run_suites` in
`learn/code/harness.py` and `RUNGS` in `ladder/` (into one loader and runner),
and `score_workspace` with the fixed `grade()` (the verdict).

## 10. Phases

1. The unified suite format and loader; port the ladder rungs and the learn
   suites, each proven to score as before.
2. The run-bundle writer and `eval run`; a bundle round-trips (write, then
   load and read back) with no machine-specific paths.
3. Replay with `structural` and `semantic` compare, and cross-model compare.
4. Submit and review: the portable file and the review command.
5. The determinism track, parallel; its exit test unlocks `exact`.

Each phase is a plan under `docs/superpowers/plans/`, and each lands with the
rung or suite it touches re-run, not asserted.

## 11. Risks

- **Reproduction is oversold.** The failure mode is a bundle that implies a
  seed reruns when it does not. Mitigation: the manifest marks seeds as
  provenance, and replay always names its compare layer.
- **Unification breaks a rung's score.** Mitigation: a ported rung is accepted
  only when it reproduces its prior number on the same input.
- **The bundle leaks machine or personal detail.** The host is anonymised, no
  absolute paths are stored, and the submit step is a review, not an automatic
  publish.
- **The determinism track never exits.** Then `exact` simply never unlocks;
  `structural` and `semantic` carry replay indefinitely, which is acceptable.

## Excluded

- A hosted index or service for runs (Andre chose a portable file; revisit
  only if the corpus outgrows file exchange).
- Editing Paul's lesson suites to raise pass rates; the suites are the
  measure, and the levers are the prompt and the scaffold.
- Seeded reproduction as a guarantee before the determinism track's exit test
  passes.
