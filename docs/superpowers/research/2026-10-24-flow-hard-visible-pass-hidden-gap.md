# Flow hard: first end-to-end visible pass, and the oracle gap it exposed

Date: 2026-10-24. Status: single measured run, not a rate. The spec-driven
flow (`flow_run.py` + `extensions/mellum-flow.ts`) drove the **hard** suite
through all seven phases from scratch, on Mellum 2.1 (6-bit) via oMLX at
concurrency 1.

## What is measured

One full run of `flow_run.py --suite hard --concurrency 1 --attempts 4`:

- **All seven phases reached `tests PASS`** against their frozen per-phase
  gates — the first time the flow has carried hard end to end.
- Final grade: **`visible=PASS`, `hidden-grader=FAIL`**. Re-running the suite's
  own hidden grader against the finished workspace: **29 of 34 assertions
  pass, 5 fail**, all in the last two phases:
  - Phase 6 (`/tickets` report): the computed sums are wrong, and "archived"
    is derived from status rather than from `archived_at IS NOT NULL` as the
    spec states.
  - Phase 7 (`/visits` report): the endpoint returns an empty list — the
    grouped / sorted / filtered report produces no rows.
  - The four between-phase migrations are not all recorded.

Phases 1–5 pass the hidden grader. The coder's phase-1–5 code was spot-checked
by hand and is correct (e.g. archive returns 400 for an open complaint, 303 for
a resolved one, a monotonic audit `seq`, `/stats` open count).

## What is conjecture

The gap is the **complete-acceptance-test** problem, not a model limit. The
examiner's phase-6 and phase-7 gates are too weak — they accept an app that the
hidden oracle rejects — so the coder was never forced to produce the exact
sums, the `archived_at` definition, a non-empty `/visits`, or recorded
migrations. The conjecture is that a gate that is a true **superset of the
hidden oracle on these requirement types** would force a correct build. This is
unproven here: no run yet pairs a complete gate with a hidden pass.

## How we got here (all harness, never the model)

Every blocker on the road to `visible=PASS` was a harness defect; the model's
code was correct each time it was checked. In order, each fixed and pushed:

- oMLX's memory guard rejected every flow prompt (`prefill_memory_exceeded`);
  raised `--memory-guard-gb`.
- The examiner asserted a redirect on a client that follows redirects by
  default → now builds `TestClient(app, follow_redirects=False)` once.
- A dangling markdown fence broke the frozen gate's `compile()` → `asCode`
  strips lone fences.
- A phase was judged on the coder's own scratch tests → judged on the frozen
  gate only (`run_gate`).
- A self-contradictory absence check (`"X" not in html` where `"X"` is a prefix
  of a word the page shows) → target the specific control.
- The examiner (a thinking model whose reasoning cannot be capped) burned its
  whole token budget thinking and emitted nothing on complex phases → raised
  its `max_tokens`, then **compressed its prompt** (~4650→~2560 chars) so it
  reasons over less and converges.
- `bestPytest` salvages the test from any assistant block when the examiner
  ends on chatter.

## What would falsify / risks

- **Falsify the complete-oracle conjecture:** strengthen the examiner on
  general, spec-derived completeness (a report/query endpoint is tested by
  seeding representative rows and asserting the exact grouped/sorted/filtered
  result, not a bare 200; assert each definition and edge the spec explicitly
  states), re-run, and check whether a passing gate now coincides with a hidden
  pass. If hidden still fails with a demonstrably complete gate, the gap is
  elsewhere (coder, or the flow's per-phase isolation).
- **Risk — coding to the eval:** the examiner must derive completeness from the
  **spec**, never from the hidden grader's specific values or rows. The rules
  added stay general; the diagnosis above is for understanding, not for
  encoding the grader's answers into the examiner.
- **Risk — convergence vs completeness:** every rule added to make gates
  stronger lengthens the examiner prompt, which made this uncappable thinking
  model over-reason and stop emitting. More completeness must not reintroduce
  the empty-output stall; keep the prompt lean.
- n=1. A rate needs a preregistered multi-session run in `ladder/`.

## Update 2026-10-25 — the hidden gap was a destructive gate, not incompleteness

Resuming at phase 6 (via the new `--start-phase 6 --seed-from <g34g workspace>`,
so phases 1–5 came hidden-verified-correct and only 6–7 re-ran) reproduced the
same `visible=PASS, hidden=FAIL` (29/34) with the strengthened examiner. The
cause is NOT that the gates were incomplete — it is that the phase-6 and phase-7
gates **destructively mutate the persistent fixture**:

- `phase_6.py` ran `DELETE FROM tickets` then inserted its own five rows;
  `phase_7.py` ran `DELETE FROM visits` then inserted its own five rows.
- Those writes persist in the workspace's `data.db`. The hidden grader then read
  the examiner's data, not the fixture: it expects the fixture's
  `all_time=2099, archived=1000, open=500` (7 ticket rows) but saw the
  examiner's `all_time=1500, open=600` (5 rows). Every phase-6/7 hidden failure
  traces to this one side effect.

The earlier "seed representative rows" completeness rule, and the self-contained
rule's "for a DB report INSERT the rows directly", are what told the examiner to
reseed — on an in-memory store that is harmless (each test process is fresh), on
a **file-backed** store it corrupts the data the spec's report ("from `data.db`")
and the grade depend on.

**Agnostic fix (in progress):** a test must not destructively mutate persistent
fixture state. For a report/query over data that already exists in a store,
READ what is there and compute the expected from it; never DELETE/overwrite it;
roll back any row you add. This is general test discipline, derived from the
spec's "from the database", not from the hidden grader's values. (Migration
recording is tracked separately; re-check after the data-destruction fix.)

### Deeper layer (same day): the small examiner/coder don't GROUND in the fixture

Prompt-only non-destruction did not land — a re-run's phase-6 gate still ran
`DELETE FROM tickets`. So the robust fix moved to the harness:
`flow_run.restore_fixture_data` puts each fixture table's ROWS back from the
pristine base before the authoritative grade, keeping the workspace's migrated
schema (column intersection, so a renamed/extended schema doesn't crash it).

Restoring the rows then exposed the NEXT layer, the same root cause one level
down: the coder had **invented a `visited_at` column** for `/visits` (and a
migration to add it) when the fixture `visits` table already ships a populated
`date` column — so `/visits` read an all-NULL column and returned nothing. And
`/report` defines "open" as `status='open'` where the spec's open is "not
archived". Both are *grounding* failures: the small examiner and coder invent a
schema/definition instead of reading the data that is actually there.

Agnostic fix added: the coder is told to inspect an existing table's real
columns/rows (`PRAGMA table_info`, a `SELECT`) and use what is there — never
invent a column or assume a name the data does not use. The examiner's
compute-from-existing rule is the examiner-side counterpart.

**Honest read:** on the database/report phases this is a *grounding ceiling* for
the small models — each layer fixed (destruction → schema invention → "open"
definition) reveals another, and prompt rules land only unreliably. The harness
restore is a durable guarantee; the grounding rules raise the odds but do not
make it certain. A hidden pass on 6–7 likely needs either a more capable model
for those phases or a harness that grounds the examiner/coder in the real schema
(e.g. injecting the fixture's `PRAGMA table_info` into the task), not more prose.

### Measured after the harness restore + grounding rule: 29 → 31 / 34

A resume run (`--start-phase 6` from a clean seed with a pristine `data.db`) with
`restore_fixture_data` wired in and the coder-grounding rule reached visible=PASS
and hidden **31/34** (was 29). The restore CLEARED both phase-6 failures
(`test_report_exact_sums`, `test_archived_defined_by_archived_at`) — on the
restored fixture the coder's `/report` computes the right sums. Three remain:

- `test_visits_filter_sort_and_limit` and `_range_is_inclusive_and_minutes_bound`:
  the coder's `visits` table has **no `date` column** — it invented `visited_at`
  (NULL) and the migration dropped/omitted the fixture's `date`, so the report
  reads nothing. The restore can't reinstate a column the schema lacks; the prose
  grounding rule did not stop the invention.
- `test_all_migrations_are_recorded`: not all four migrations are registered.

Next agnostic fix (implementing): inject the workspace's real fixture schema
(`<db>.<table>(cols…)`) into the phase task, so the coder/examiner see the
actual `date` column rather than relying on a prose "inspect the schema" rule
the small model ignores. Grounding by construction, not by instruction.

### Schema injection landed in the task, but the resume test was confounded

The task now carries `data.db.visits(id, agent, date, minutes, ticket_id)`
verbatim, yet a resume-at-6 run still finished 31/34 with the workspace `visits`
holding `visited_at` and no `date`. Cause: the resume seed (g34g's workspace)
carries a `migrations.py` whose `add_visited_at_column` a PRIOR coder invented —
this coder inherited it and recreated `visits` with `visited_at` instead of the
fixture's `date`. So the resume cannot fairly test schema injection: the
invented column is baked into the seed. The fair test is a full run from phase 1
with all fixes, where phases 6–7 are built fresh with the schema in view. Also
still open: `test_all_migrations_are_recorded` (not all four registered) — a
separate migration-registration gap, to diagnose after the clean run.
