# Preregistration: E1 Reasoning Returned as Text, lesson check

**What is measured.** Nothing yet: fixed on 2026-10-30 before the deciding
run, at the commit that adds this note. It is the first lesson check under
the condition-produced rule ([spec](../specs/2026-10-29-uniform-lessons-design.md),
correction of 2026-10-29).

**What is conjecture.** That on the LAN host the bare session is fed its
reasoning back as text at least once, and that `context/repair-think-tags`
brings that to zero without breaking the task.

## The condition

The LAN vLLM host (`scripts/baseline/lan-profile/`: vLLM
`0.26.1rc1.dev1102+ge9d1398d9`, model id `mellum`, the 6-bit Mellum), whose
streaming reasoning parser misses every turn after the first
([note](2026-10-29-lan-reasoning-leak.md)). Pi 1.3.0 under `.baseline/`.

## Arms and running

`scripts/lesson-check.sh E1`, which runs the page's two lines:

- **Before:** `--suites-dir learn/challenges --suite reasoning-as-text`
- **After:** the same plus `--remedy context/repair-think-tags`

Both `--repeat 1 --deadline 600 --stall 120`, no `--grade`. A session passes
when the hidden tests pass and `run.json`'s `record_failures` is empty (the
challenge's `record.json` caps `reasoning_as_text` at 0).

## Rule

- **The lesson holds** if the before session FAILS with a record failure on
  `reasoning_as_text` and the after session PASSES.
- A before session that fails for another reason (its hidden tests, a stall)
  does not count as the lesson holding; it is recorded and the check is run
  once more.

## Leads behind it

Two screens on the LAN host, one session per arm: before `reasoning_as_text`
6 and 8 (tests passing both times); after 0 and passing on the second
screen, whose base had pytest's `pythonpath` set (the first after failed on
an unrelated import trap, fixed in `c308bce`).

## What would falsify this

A bare session with `reasoning_as_text` 0 on this host: then the parser does
not miss reliably, and the condition is not what this lesson says.

## Risks

- One session per arm; the screens make the before arm's failure likely, not
  certain.
- The host is not ours to pin; a server upgrade would remove the condition,
  and the page would have to name a host that still has it.

## Result, 2026-10-30

Run at `b7e538e` (`runs/E1-check-20261029T220741Z-b7e538e`, recorded under
`evals/2026-10-30-reasoning-as-text-check/`).

- **Before:** FAIL on the record: hidden tests passed, `reasoning_as_text`
  7 (9 requests).
- **After:** PASS: hidden tests passed, `reasoning_as_text` 0 (5 requests).
- **The lesson holds**, the first under the condition-produced rule. With the
  two screens, the bare session was fed its reasoning as text in 3 of 3
  sessions on this host (6, 8, 7 turns); a lead on reliability, not a rate.
