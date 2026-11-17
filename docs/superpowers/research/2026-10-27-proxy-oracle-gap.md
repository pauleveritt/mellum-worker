# The gate passes, the grader fails: an 8-check proxy→oracle gap

Date: 2026-10-27.

## What is measured / What is conjecture

**Measured.** On the hard suite, forced flow, Mellum 2.1 6-bit via oMLX
(`--thinking medium --context-window 40000 --attempts 6 --concurrency 1
--retry-concurrency 2`, feedback OFF), one run (control-2) passed **all 7
self-authored phase gates and the visible suite** and still scored only
**26/34** on the hidden grader. The 8 misses were reproduced deterministically
(restore fixture rows, re-copy the frozen grader, `pytest -rA`) and each one is
stated **verbatim in the spec prompts** the planner was handed. The second
finished control run scored the same band (control-1: 27/34 but 4/7 phases,
visible FAIL — a different, incomplete run).

**Measured (screen, 2026-10-27).** The spec-coverage gate (`bbfac5f`) was run on
one hard run, feedback OFF, control-matched. It did what it was built to do: the
examiner's gate could no longer freeze while blind to a diagnosed artifact —
`[examine] residual uncovered spec tokens: add_tickets_status_archived_index`
appears in the trace, so the detector fires on the real miss, not a stand-in.
But **phase 5 failed its own gate across all 6 best-of-2 rounds** and carried its
best incomplete attempt forward — the same wall control-3 hit. The run was
**stopped at phase 6/7 before grading**, so there is no hidden=N/34 for it. One
screen, a lead, not a rate.

**Conjecture.** That a superset gate closes the gap enough to reach a hidden
pass. This screen weakens the "gate alone" form of it: a stronger **detector**
does not move a phase the model cannot satisfy — it only names what is missing.
The lever still untested is the gate paired with its **actuator**: coder feedback
ON (`MELLUM_CODER_FEEDBACK=1`), so the named miss reaches the coder on retry
instead of it rebuilding blind (see `2026-10-26-coder-feedback-comparison.md`).
Needs a ladder run: spec-coverage gate + feedback ON, control-matched.

## The 8 misses (control-2, all explicit in the spec)

| # | Hidden check | Spec says | App did | Phase gate |
|---|---|---|---|---|
| 1 | `test_phase3_add::...redirects...` | 303 (prompts 03/04/05) | `app.py:22` sends **306** | never asserted the code |
| 2 | `test_visits::filter_sort_and_limit` | `GET /visits` → `{"visits":[...]}` (prompt 10) | **no /visits route** | never checked the route |
| 3 | `test_visits::range_is_inclusive...` | same | same | same |
| 4 | `test_migrations::index_exists` | `idx_tickets_status_archived` (prompt 06) | index absent | — |
| 5 | `test_migrations::resolved_at_is_backfilled` | backfill to `2026-01-03T00:00:00` (prompt 08) | NULL after restore | checked the LIVE db, not post-restore |
| 6 | `test_migrations::note_column` | `note` column (prompt 11) | migration not written | — |
| 7 | `test_migrations::all_migrations_are_recorded` | tracked set (prompts 06/08/09/11) | no `_sqlite_migrations` | — |
| 8 | `test_migrations::rerunning...noop` | "re-running must be a no-op" | `migrate` never run | — |

`migrations.py` exists but registers **3 of 4** migrations (missing
`add_tickets_note`) and was **never applied via `sqlite-utils migrate`**, so no
tracking table, no index, and the backfill does not survive the pre-grade
fixture-row restore.

## Root cause

The examiner's 7 phase gates are a **loose, incomplete proxy** of the 11-task
spec. They don't pin the exact redirect code, the tracked/re-runnable migration
contract (including the note column), or the `/visits` endpoint. So the flow
goes **7/7 green while the hidden grader, reading the whole spec, finds 8
holes.** The gap is not Phase 4/5 thrash and not the feedback toggle — it is
gate incompleteness. This is the `mellum-dev` §6 "make complete real" lead seen
live: a gate that is not a superset of the spec passes a wrong build.

A harness subtlety compounds miss #5: `restore_fixture_data` (run right before
grading) wipes migration-derived data because the migration was not tracked or
re-applied — so a gate that checks the backfill at phase time passes while the
grader, after restore, fails. A faithful gate must verify migrations the way the
grader does: after a fresh `sqlite-utils migrate`, re-runnable.

## The lever (agnostic)

Make the examine/gate step author gates that are a **superset of the spec**:
enumerate **every** task in the prompts (not collapse 11 tasks into the 7 phases
the planner happened to name), and assert each **stated** contract — 303 exactly;
every named migration applied through `sqlite-utils migrate` with the
`_sqlite_migrations` no-op re-run, the index, the `note` column, the backfill;
the `/visits` JSON keys. Dry-run each gate **red** on the incomplete build and
**green** on a correct one. This reads only the prompts, never the hidden
grader — fully within the agnostic rule (AGENTS.md: reading the grader to
diagnose is fine, encoding its answers is not; nothing here is encoded, it is
all in the spec). A spec-complete gate is the only thing that can force the fixed
small model — via best-of-N and the feedback loop — to actually close these 8.

## What would falsify this / Risks

- **The model may not complete the extra work even under a strict gate.** A
  superset gate that stays red for the whole budget would show the ceiling is the
  model's throughput on this spec, not the gate — a real possible outcome, and
  still worth knowing.
- **A stricter gate makes runs slower** (more to satisfy, more retries). The
  hard run is already ~2–3 h; a superset gate could push it further.
- **Over-tightening risks a brittle gate** that false-fails a correct build
  (the per-phase-scoring guard exists for exactly this). Judge by the hidden
  grade, never the gate.
- The feedback-vs-no-feedback screen was **stopped before the feedback arm**
  (2 control runs done) once this gap proved to be the dominant effect; see
  `2026-10-26-coder-feedback-comparison.md`. That comparison is now secondary to
  closing the gate-completeness gap.
