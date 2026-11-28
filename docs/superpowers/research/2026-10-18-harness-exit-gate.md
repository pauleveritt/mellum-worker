# The exit gate: don't let the worker decide done

Date: 2026-10-18. A design input for M.11 (the mediated test) and for a
companion runtime guard that M.11's Excludes keeps out of scope. Written from
a review session; the probes below ran on a plain `mlx_lm.server` serving the
6-bit MLX weights on an M-series 48 GB Mac, outside the scored ladder (no Pi).

**What is measured.** Two single-arm, greedy (temperature 0) probes on the
served worker, n = 1 each, not the ladder's scored protocol:

- *Rung 1, full tool loop, hand-driven.* The worker was given the v5 prompt,
  the seven tool signatures and the sentence "the cart total ignores quantity,
  fix it"; each tool call was executed for real against a scratch copy of the
  `calculator` fixture and the result fed back. It reached a passing test in
  seven turns (~13 s): `find` -> `read calculator.js` -> `read
  calculator.test.js` -> `edit` (price * quantity) -> `read package.json` ->
  `bash npm test` (exit 0) -> stop. `node --test` then exited 0, 3/3.
- *Phase 4 (rung 9), single shot, no tools.* Given the v5 prompt, the
  `phase-4-resolve-reopen` spec and the current `models.py`, and asked for the
  updated `models.py` plus tests. Output added a `status` field and
  `resolve`/`reopen` methods but **no `id` field**, and its self-written tests
  asserted only status transitions. The hidden oracle's `first.id !=
  second.id` would raise `AttributeError`.
- *Phase 4 mediated test, hand-driven loop.* The main model wrote the failing
  test from the full spec (id included), it was confirmed red, then handed to
  the worker as "make this pass" and driven through the tool loop against the
  served weights. This time the worker added both a `status` and an `id` field
  to `models.py` — the fields the single-shot had omitted — so the external
  oracle did redirect it to the missed requirement. But its id code was buggy
  (it did not collect) and the crude driver truncated on `finish_reason=length`
  across several turns, so neither the mediated test nor the hidden oracle
  reached green. The lead: an external, complete oracle **redirects** the worker
  to a requirement its own tests drop, but reaching green also needs harness
  quality — generation budget, re-dispatch of the failure, enough turns —
  which this toy driver did not supply. Redirection is necessary, not
  sufficient.

**What is conjecture.** Everything about rates and about whether the fix
works. That a mediated (externally authored) failing test lifts rungs 6-9
against A21 (9/12) is unmeasured. That a freeze-the-oracle guard changes any
outcome is unmeasured. The single-shot Phase 4 is an illustration of the
[ac-demo lead](2026-10-13-ac-demo-one-file-sessions.md) (n = 3 per phase), not
new evidence.

## The principle

A self-exit is safe only when the oracle that defines "done" is **external**
(the worker did not author it), **complete** (it covers the whole spec, not a
subset the worker chose) and **unweakenable** (the worker cannot edit or delete
it). The two probes above differ on exactly these axes and nothing else:

- Rung 1 passed because `calculator.test.js` was already present and complete —
  it even names `zero quantity contributes zero`. The worker read it, satisfied
  it, and its self-exit was correct.
- Phase 4 false-exited because the worker authored the oracle from the spec's
  `Tests:` line, which omits the id; its test passed, so it stopped. Same model,
  same loop; the only difference is who wrote the oracle and whether it was
  complete.

So the fix is not "trust the worker less in general" — it is "move the oracle
out of the worker's hands and keep it whole."

## Two mechanisms

1. **Mediated test (= M.11).** The main model turns the spec into a failing
   test, confirms it red on the current tree, hands the worker "make this
   pass", and re-runs that test after. This supplies *external* and (if the
   author reads the whole spec) *complete*. It is screen-first; this note adds
   nothing to M.11's screen, it only records the companion below and the probes.

2. **Freeze-the-oracle guard (new; deferred).** M.11 Excludes "any ... guard
   change", so the *unweakenable* property is a separate item. The ladder
   already enforces it as a scorer — `existing_tests_kept` (no existing test
   edited or removed; additions allowed, checked at the AST level) and
   `outside_write_list` (no write outside the allowed paths). The proposal is to
   promote those two checks from grading into a runtime contract on the worker,
   and to gate the exit on an actual run of the frozen test with re-dispatch of
   the failure, rather than on the worker's final message. See the BACKLOG
   entry "Freeze-the-oracle exit gate".

## What would falsify this

- If M.11's rung-9 screen does **not** move with an external, complete failing
  test, then "supply the oracle" is not the fix (or not sufficient), and the id
  miss has another cause.
- If traces show the worker essentially never edits or deletes tests, the
  freeze-the-oracle guard is solving a problem that does not occur, and only the
  mediated test is warranted.

## Risks

- The judgment moves up a level, it does not vanish: a main model that writes an
  incomplete failing test reintroduces the same gap one layer higher.
- A ladder runner that calls the main model is excluded by M.11; the screen's
  test is written once by hand, so the screen measures the mechanism, not an
  automated test-writer.
- A runtime write-list/test-keep guard that does not mirror the ladder's allowed
  paths exactly could block legitimate edits; it must track `AGENTCLINIC_ALLOWED`
  and the additions-allowed rule, not invent its own.
- The probes here are n = 1 and greedy; they illustrate the mechanism and must
  not be cited as rates.

## Follow-up, 2026-10-18: the gate (not the oracle alone) reached green

The hand-driven Phase 4 probe above (which "did not reach green") was re-run
after adding the two things it had lacked, nothing else: the acceptance test
was **frozen** (edits to it rejected) and each stop was met by **re-running the
frozen test and re-dispatching its failure**, with a larger per-turn budget.
Same external test, same model, same served weights. It converged at turn 25:
the mediated acceptance test and the **hidden oracle** (never shown to the
worker) both passed, exit 0. The worker's final `models.py` gives each complaint
a distinct, stable auto id via a module `_next_id` counter in `__post_init__` —
the requirement the single-shot and the model-authored-test runs had dropped.

Why this is the point: the earlier probe already had the external, complete
oracle and still failed. Adding only the harness — freeze plus re-dispatch plus
budget — is what closed it. So the external oracle **redirects** the worker to
the missed requirement, but convergence came from **not trusting the self-exit**:
re-running the frozen test and handing the failure back until green. The oracle
(M.11) and the gate (the BACKLOG "Freeze-the-oracle exit gate") are both
load-bearing; the oracle alone is necessary, not sufficient.

Scope is unchanged. n = 1, greedy, a hand-driver against `mlx_lm.server`, 25
turns, not the scored ladder. It shows the mechanism can reach green end to end,
hidden oracle included; it is not a rate and does not establish that M.11 moves
rung 9. That remains the preregistered screen on Pi.
