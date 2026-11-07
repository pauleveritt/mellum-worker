# Flow harness solutions, and how agnostic they are

Date: 2026-10-25. A report on the fixes made while driving the FIXED small model
(Mellum 2.1, 6-bit via oMLX) through the seven-phase `hard` suite, and a direct
answer to the question: **are these solutions agnostic — would they help any
test, not just this suite?**

## The one-line answer

The solutions are **agnostic**: every one is general infrastructure or general
test-writing discipline, derived from the spec and from how tests should behave,
never from the hidden grader's specific values (verified: the examiner prompt
contains zero suite-specific routes, tables or numbers). They **transfer** to
any suite of this shape.

But agnostic does **not** mean "any test will pass". The fixes remove
*harness-side* obstacles so the model's correct work is not blocked or
corrupted. Passing still depends on the model actually producing a correct
implementation. On the database phases that last part is a **model grounding
limit**, which the harness fixes raise the odds on but cannot force.

## Goal and principle

Crack `hard`: a hidden-grader PASS on a 7-phase app built from scratch, scored
by an oracle the worker never sees. Standing principle: **never blame the
model** — it is fixed, so every gap is the harness's job. And (the user's
constraint) **stay agnostic**: fix general problems, never code to this suite.

## Results so far

- `easy`: visible + hidden PASS.
- `hard`: first ever **visible=PASS end-to-end** (all 7 phases build and pass
  their own gates). Hidden **29 → 31 / 34** after the fixture-restore fix.
  Remaining 3: `/visits` (×2) and migration-registration — a documented
  grounding ceiling, not a harness defect.

## The solutions

Each is problem → solution → why it's general → evidence.

| # | Problem | Solution | General because | Evidence |
|---|---------|----------|-----------------|----------|
| 1 | oMLX rejected every prompt (`prefill_memory_exceeded`) | raise `--memory-guard-gb` to 34 | infra config, no suite knowledge | easy went green immediately |
| 2 | Examiner asserted a redirect on a redirect-following client | build `TestClient(app, follow_redirects=False)` once | any redirect-based web app | frozen phase-4 gate 2 fails → 7/7 |
| 3 | A stray ```` ``` ```` broke the gate's `compile()` | `asCode` strips lone fences; `bestPytest` salvages the test from any block | any model that emits fenced code | gate compiles; phase 4 unblocked |
| 4 | Phase judged on the coder's own scratch tests | `run_gate` scores only the frozen gate (the definition of DONE) | the gate is the oracle in any suite | a brittle coder test no longer fails a correct build |
| 5 | Self-contradictory absence check (a label that is a prefix of a shown word) | target the specific control (its `action=` URL), not a bare substring | general assertion hygiene | phase 4/5 absence checks pass |
| 6 | Examiner (uncappable thinking model) spent its whole budget thinking, emitted nothing | raise `examine` `max_tokens` to 32000, then COMPRESS the prompt (~4650→~2560) so it converges | any thinking model whose reasoning can't be capped | measured: empty@16384 → full test@32000; lean prompt converges |
| 7 | Tests assumed a clean store / absolute totals / seed ids | self-contained: create own data, assert before/after DELTAs, never assume a seed id or state | universal test isolation discipline | phase 5 brittleness 5 fails → 1 |
| 8 | Report gates too weak (passed a stub) | compute the EXACT expected from the data the spec points to; cover a row a wrong reading of each definition mishandles | general completeness discipline | gates now exercise the real definitions |
| 9 | **Destructive gate corrupted the fixture DB** (`DELETE FROM tickets/visits` persisted; the grader read the examiner's data) | harness `restore_fixture_data`: restore each fixture table's rows from the pristine base before grading, keeping the coder's migrated schema | mirrors whatever `*.db` the suite ships — no hardcoded table or value | **hidden 29 → 31**; both phase-6 report failures cleared |
| 10 | Coder invents a column (`visited_at`) instead of the fixture's real `date` | coder grounding rule + inject the real schema (`<db>.<table>(cols…)`) into the task | reflects whatever tables exist; "grounding by construction" | schema note reaches the task verbatim; clean run measuring |

Plus tooling: **`--start-phase N --seed-from <workspace>`** resumes a run at a
later phase from a logged bundle (its built app + frozen gates), so iterating on
a late phase is minutes, not an hour.

## What is agnostic, precisely

- **No suite-specific values anywhere.** The examiner prompt names no route,
  table, column or expected number; it states discipline (compute from existing
  data, assert deltas, don't mutate a persistent store, target the specific
  control). Checked by audit each change.
- **The harness helpers reflect the workspace, not the suite.**
  `restore_fixture_data` and `fixture_schema_note` iterate whatever `*.db` and
  tables are present — a different suite with different tables is handled the
  same way, with nothing hardcoded.
- **Diagnosis used the hidden grader; the fixes did not.** The grader's failures
  were read to *understand*, but every fix is justified by the spec ("a report
  from the database", "dates in the inclusive range") or by general testing
  practice — never by copying the grader's answers.

## Where "any test passes" breaks down (the honest limit)

- The fixes make the harness **not get in the model's way** — they don't make
  the model correct. A hidden pass still needs the small model to build the
  phase right.
- On the DB/report phases there is a **grounding ceiling**: the small examiner
  and coder invent a schema or a definition rather than reading what is actually
  there, and prose rules land only unreliably. Harness-level grounding (restore,
  schema injection) raises the odds; it cannot force a correct query.
- The work has gone in **layers** — each fix revealed the next (redirect →
  fence → scoring → convergence → destruction → grounding). A new suite of a
  different shape could reveal a new *general* gap. The approach is agnostic and
  extensible, not complete.
- `restore_fixture_data` assumes the grade should see the pristine fixture rows.
  That is correct for any "report over a shipped fixture" suite; a suite whose
  tests are *meant* to leave persistent state changed would need a different
  policy. Agnostic **within the class**, not beyond it.

## Bottom line

Yes — this is being done agnostically: the solutions are general and would help
any suite of this kind, and none is coded to pass this specific test. What they
buy is a harness that no longer blocks or corrupts a correct solution. The last
3/34 on `hard` are a model grounding limit on database reasoning; closing them
needs either a more capable model for those phases or deeper harness grounding,
not suite-specific hacks.

## Addendum (clean full run): the visible gate can FALSE-FAIL a correct app

The from-scratch run exhausted all 4 rounds on phase 5 — the first time — but
the app was correct. The examiner's gate did `resolve` then `archive` and
asserted the audit log grew by **+1**, when both actions correctly log (so +2):
it used the before/after DELTA rule but forgot that its own setup `resolve` has
a side effect. A correct app cannot pass it.

Two things this nails down:

- The small examiner writes subtly-wrong gates **stochastically** — a different
  run surfaces a different brittleness (redirect-following, substring collision,
  destructive reseed, now a mis-counted delta). No finite set of prose rules
  makes it reliable; this is the grounding/authoring ceiling, restated.
- The **visible gate is only a proxy**; the hidden grader is the oracle. A
  brittle gate can false-FAIL a correct build (wasting rounds) without corrupting
  it, so the hidden grade — which runs the suite's own tests — can still pass
  that phase. This is why `run_gate` scoring the frozen gate is a convenience,
  and the end-to-end number that matters is the hidden grade.

The durable lesson: lean on the harness guarantees (fixture restore, schema
injection, gate-only scoring) and the hidden grade, not on the small examiner
authoring a perfect oracle every time.

### And one brittle gate poisons every LATER phase's visible score

Worse than a wasted phase: phase 6's app passed its OWN gate (2/2), yet phase 6
was marked FAIL — because the flow scores the **cumulative** gate (phases 1..N),
which still contains phase 5's brittle, unpassable test. So a single false-fail
gate drags down 6 and 7 too. The hidden grade is unaffected (it runs the suite's
own grader, not the examiner's frozen gates), but the *visible* run collapses
after the first brittle freeze.

This points at a real, agnostic harness improvement: a frozen gate that a phase
cannot pass within its round budget should be **re-examined (regenerated), not
carried forward as a permanent poison** — or the per-phase pass decision should
score only that phase's own gate while the cumulative check stays advisory.
Either keeps one stochastic bad gate from sinking the rest of the run. (Noted as
the next harness fix; the hidden grade remains the real measure meanwhile.)

**Implemented:** the per-phase pass decision now scores only that phase's OWN
gate (`run_gate(workspace, timeout, phase=pnum)`); `restore_gate` still
materializes every frozen gate so the coder sees them, and the final hidden
grade stays the regression backstop. A stochastically-brittle earlier gate can
no longer poison a later phase's pass. Confirmed by the clean from-scratch run's
failure mode: phase 5's brittle gate had marked 6 (which passed its OWN gate
2/2) and 7 as fails, the coder never got a pass signal, thrashed, and left
`app.py` with an unterminated triple-quoted string — a broken app that errored
all seven hidden graders (hidden 0). Scoring each phase on its own gate removes
that cascade.

## Key commits

`5a9106b` examiner non-destructive rule · `f15db25` harness `restore_fixture_data`
+ coder grounding (hidden 29→31) · `dc4b463` fixture schema injection · plus the
`--start-phase/--seed-from` resume flag and the convergence/compression fixes.
