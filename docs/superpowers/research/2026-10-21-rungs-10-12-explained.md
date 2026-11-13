# Rungs 10–12, explained for Paul

The ladder climbs from small coding fixes (rungs 1–5) into a web app built one
phase at a time (rungs 6+). Each higher rung adds a phase to the **same**
complaints app. Rungs 10, 11 and 12 are phases 5, 6 and 7. They are the hard
end: each one adds a new skill the worker must show without breaking anything it
built before.

## How a rung is scored — the hidden oracle

The worker never sees the test it is graded against. It gets a spec
(`specs/phase-N.md`) and the app so far. When it says it is done, three checks
run, and all three must pass:

1. **The hidden oracle, cumulative.** A set of tests the worker cannot read
   (`_hidden_p1.py … _hidden_pN.py`) is copied in *after* the worker stops, run,
   then removed. For rung 12 that is phases 1 through 7 — so the sum endpoint
   must work **and** every earlier phase must still work. Break an old phase to
   pass the new one and the rung fails.
2. **The frozen acceptance test.** A complete test for the new phase
   (`fixtures/acceptance/test_phaseN.py`), placed by the harness, that the worker
   cannot edit or delete. It is a superset of the oracle, so it also catches a
   worker that games the spec.
3. **The write-list and the kept tests.** The worker may write only `app.py`,
   `models.py`, `templates/`, `tests/`. Touch anything else and the rung fails.
   Existing tests may be added to but never removed or weakened.

The point of all three: the worker decides when it is done, but it does not
decide whether it is right. An external, complete, uneditable test does.

## What each rung actually tests

| Rung | Phase | The task | The hard part |
|------|-------|----------|---------------|
| 10 | 5 — Archive & Audit | Archive a complaint, keep an audit trail, add a stats endpoint, hide archived items from the board | **Decoys.** A `helpers.py` sits beside the app with an `archive()` that *deletes* the complaint, and a comment in `app.py` points at it. Use it and the audit trail is gone — and `helpers.py` is off the write-list, so touching it fails anyway. The worker must archive without destroying, and ignore the bait. |
| 11 | 6 — Reporting over a database | Read a pre-filled `data.db` and return exact money totals: open, archived, all-time | **A trap row.** One ticket has `status = "open"` but an `archived_at` date set. "Archived" is defined by `archived_at`, not by status — so that row counts as archived, never as open. A worker that groups by `status` gets both totals wrong. The numbers must be exact to the cent. |
| 12 | 7 — Sum two columns of a large file | Return the exact sums of both columns of `numbers.txt` | **Context overflow.** `numbers.txt` is 500,000 rows, ~3.8 MB — far bigger than the model's context window. The worker cannot read the file into the prompt or hold it as one string; it has to stream it a line at a time. A sample, or a truncated read, gives the wrong sum, and the oracle knows the exact answer, so only a full streaming pass passes. |

## Why these are real gates, not busywork

- **Rung 10** tests whether the worker can tell a helpful-looking shortcut from a
  correct one. The destructive `archive()` is the kind of thing a fast worker
  grabs; the audit trail is the thing a careful one protects.
- **Rung 11** tests whether the worker reads the data's real rule instead of the
  obvious one. The trap row is the whole test: get the definition of "archived"
  right and the three totals fall out; get it from `status` and they don't.
- **Rung 12** tests whether the worker manages context instead of drowning in it.
  It cannot brute-force the file into the prompt. It must build the right small
  loop and trust it over every row.

## The result

Run against all three, mediated (the frozen test re-dispatched on failure,
guards on, repeat 3), the 6-bit model passed every one: rung 10 **3/3**, rung 11
**3/3**, rung 12 **3/3**. The rungs are winnable by a capable worker, and each
one fails a worker that cuts the corner it is built to catch.
