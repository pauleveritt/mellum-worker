# Mediation, crutches, and the real world

A note on a question Paul and the team keep landing on: if the harness runs the
test and sends the worker back until it passes, is that a crutch — and will a
mediated PASS mean anything once the worker meets a real task? Written off a full
un-mediated ladder pass and a look at what the worker actually did on the rungs
it failed.

## What the numbers say

The 6-bit, bare (direct, n=1, **no frozen test, no redispatch**): **6/12.**
Passes 1, 2, 3, 7, 8, 12. Fails 4, 5, 6, 9, 10, 11. Mediated (frozen test +
redispatch), rungs 10, 11 and 12 all pass 3/3.

Two things stand out:

- **Mediation did not inflate rung 12.** The bare worker already clears the
  context-overflow rung on its own. Where the model is capable, it passes with
  no help — so mediation is not a blanket prop.
- **Mediation flipped 10 and 11** (fail → 3/3). Those are the rungs where the
  worker stops short of a finished job.

The failures are not the *hardest* rungs — the worker passes 12, the one built
to overflow context — they are the **coordination** rungs: multi-file refactors,
a trap row to read correctly, an old phase to keep working. The worker fails on
completeness, not difficulty.

## Why it fails 4 and 5 — it moves its own goalposts

Reading the traces of the un-mediated 4 and 5 failures: the worker is **not**
incapable, and it does **not** cheat (it never edits the test). It runs the whole
test file once, sees several failures, then **narrows pytest to the single test
function it is working on** (`pytest test_export.py::test_export_appends_totals_row`),
gets that one green, and declares done — leaving the sibling tests in the same
file red. Rung 5's final message says exactly that: "`test_export_appends_totals_row`
passes." It fixed one of three and stopped.

So the gap is behavioural: the worker self-certifies against a **subset** it chose.
That is the same failure the exit-gate work named — the worker decides when it is
done, and it decides wrong — here by shrinking the goal rather than by writing a
bad test.

This is why the external frozen test rescues 10 and 11: it runs the **whole**
set, every time, and the worker cannot narrow it.

## Is that a crutch? The honest line

Running an external test the worker cannot edit, and sending it back on failure,
is what a developer does. It is CI, not a crutch. The crutch would be different
things, and we guard against each:

- **Letting the worker write or edit its own gate** → it would narrow or weaken
  it. Guarded: the test is external and uneditable (`existing_tests_kept`, the
  write-list), and the prompt already forbids touching it.
- **A test so thin the worker games it** → guarded: the hidden oracle is a
  **superset** of the frozen test the worker sees, so gaming the shown test still
  fails the held-out one.
- **Reporting the mediated number as the bare capability** → guarded by running
  the un-mediated pass and reporting both. 6/12 bare is the honest figure.

## How it transfers to the real world

It depends on one thing: where the acceptance test comes from.

1. **The test already exists, or is cheap and trustworthy.** A bug with a failing
   repro, a ticket with acceptance criteria, an existing CI suite, a spec-first
   team. The test *is* the spec; "redispatch until green" is ordinary practice. A
   mediated PASS means what it says. This is a large slice of real engineering —
   and it is exactly what rungs 4/5 model: the failing `test_export.py` ships with
   the task; we did not author it to flatter the worker.
2. **No test, but "done" is cheaply checkable.** Someone — a human, or a stronger
   model, never the worker — writes the test. The PASS is as good as that test.
   The cost is real, but it is the cost of knowing you are done at all.
3. **"Done" is subjective** (UX, judgement, open-ended). No frozen oracle exists,
   mediation does not apply, and the ladder number says little. Keep a human in
   the loop. This is the honest boundary of the approach.

The deployment that follows from the data is **not** "trust the worker's
self-exit." It is: worker proposes, external test disposes, redispatch on red, a
budget and loop breaker so it cannot thrash forever, and a human gate on anything
irreversible. That is a sane shape for any automated contributor, and you would
give a junior the same gate.

## The cheaper lever the trace points at

Because the failure is self-narrowing, not incapacity, a generic prompt nudge —
"run the whole test file, make **every** test in it pass, never a single
`::test_function`, before you finish" — should recover 4 and 5 **without** a
frozen external test.

**Measured, and it does.** With that nudge appended to the system prompt (via
`mellum-override`), un-mediated — no frozen test, no redispatch — the bare 6-bit
passed **both**: rung 4 in 53 s with the full three-file refactor
(`source_files_changed: 3`, where the bare run changed one file and thrashed 63
turns to an empty exit), and rung 5 in 90 s with the decoy left untouched. The
0/1 failures became clean passes.

That is not a crutch: the nudge is good practice stated plainly, task-independent,
and gives away no answer. It says the bare model can do these rungs and the gap
was a stopped-early habit the prompt can fix. Mediation then becomes the safety
net for when the habit slips, not the thing holding the pass up — which is the
honest answer to "is it a crutch": the completeness the gate was enforcing can be
asked for directly, and the model delivers it.
