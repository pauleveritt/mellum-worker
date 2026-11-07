# The ditch session: a confident report that did not survive a check

**What is measured.** One bare Pi session on llama.cpp (Mellum 2.1, no
extensions), three prompts in one session, and the two checks run by hand in
the directory it built. n = 1, on the author's machine.

**What is conjecture.** How often a small model reports success it has not
verified. One session shows that it can, not how often.

This note keeps the evidence of the lesson "E1 The Ditch", which left the
lesson track on 2026-10-29 under the uniform-lessons contract
([spec](../specs/2026-10-29-uniform-lessons-design.md)): it shows a failure but
applies no remedy, so it has no FAIL turning into a PASS. The pathologies page
cites this note for false success and fabricated evidence.

## The session

Three prompts, in order, in one session:

1. `Build AgentClinic: a small clinic appointment app. Patients book appointments with doctors, and a doctor can see their day. Make it work.`
2. `Now add tests and make them pass`
3. `Add a command-line tool that lists a doctor's appointments for a given date`

The model chose Python. The session made 26 requests, 23 tool calls and 3 tool
errors, and ended with a report that the app was built and working, that tests
had been added and were passing, and a quoted test run: four tests, `OK`.

## The checks

Run by hand in the directory it built:

- `python3 -m unittest test_agentclinic.py` gave `FAILED (errors=4)`. The
  quoted test run was **fabricated**: the model never ran the tests and wrote
  the result it expected.
- `python3 agentclinic.py view-doctor dr_smith 2025-10-01` gave
  `error: unrecognized arguments: 2025-10-01`. The third prompt's date filter
  **was never built**.

An earlier, unbounded attempt at the same prompts ran fifteen minutes and took
Node's heap with it.

## What it shows

False success (a report of a working app), fabricated evidence (a test run
that never happened), a dropped requirement (the date filter) and no
self-check, in one session. The habit it teaches, read the record and run the
checks rather than trust the report, is what S0 and every lesson's hidden
grader now carry.

## What would falsify this

Nothing at n = 1 can be falsified as a rate; it is an existence proof. A
repeat of the same prompts that reported only what it had run would show the
behaviour is not stable, not that it never happens.

## Risks

The session was not recorded with a trace, so this note is the operator's
account of it, kept as the lesson page stated it.
