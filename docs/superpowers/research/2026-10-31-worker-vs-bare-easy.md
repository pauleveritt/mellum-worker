# Why the worker loses to bare on easy — a design mismatch, not a broken worker (2026-10-31)

## What is measured / What is conjecture

**Measured.** Local M3 Q4, easy, n=3, same profile, bare vs worker:

| arm | pass | reps (turns / wall) |
|---|---|---|
| bare (vanilla) | **2/3** | 14t/41s · 25t/71s · 14t/31s (fail) |
| worker | **1/3** | 27t/175s · 21t/61s (fail) · 27t/115s (fail) |

Worker is worse **and** heavier. The decisive detail is in the failures: both worker fails built
**nothing** — zero `write`/`edit` calls, only exploration (`289b78`: bash 9, read 4, ls 3, find
2, grep 2; `832194`: read 7, ls 5, find 5, grep 5, bash 4) — and ended on an empty final
(`empty_finals=1`). Every bare run, by contrast, wrote the file (3–4 write/edit calls each, even
its one failure). The worker spent its whole budget looking around and never started `app.py`.

**Why (measured + design).** The worker's prompt opens *"You make one failing test pass"*, and
its docstring frames it as a bounded sub-worker dropped into a larger session to turn **a failing
test** into passing code. The easy workspace hands it `specs/` + `AGENTS.md` + `pyproject.toml`
and **no `tests/` dir — no failing test**. So the worker's whole contract ("read the failing
test, run the whole test file, done when every test passes") has nothing to anchor on: it hunts
for the test that isn't there and over-explores (pathology #7), then settles empty (#5). Bare has
no such contract, so it just reads the spec and writes the file. The per-turn facts block
reinforces the look-first posture.

This is a **design mismatch, not a broken worker.** The worker assumes *test-driven delegation*
(its home is the ladder, where a failing test is always provided); the prose suites are
*prompt-driven greenfield*. It is being measured off-design here. It also explains why the gate
stack wins on easy: `mellum-acceptance` **synthesises the missing test** (the derived contract)
and `mellum-ncm` makes the model pass it — handing the worker back the anchor its prompt was
written around.

## What would falsify this / Risks

- **n = 3 screen.** A lead, not a rate; the worker's 1/3 here plus the improve-loop worker runs
  put `arm:worker` at 4/13 on the board — low, but small n.
- **The claim is the mismatch, not "worker is worse."** On a *test-driven* task (the ladder, or a
  suite that ships a failing test) the worker's prompt has its anchor and should not over-explore.
  That is the test that would confirm or break this: worker vs bare where a failing test is
  present. Untested here.
- **Fix direction, if the worker should also handle prose tasks:** give it a "write first, then
  verify" nudge when no failing test is present, or always run it behind the acceptance gate so a
  derived test exists. Unmeasured.
