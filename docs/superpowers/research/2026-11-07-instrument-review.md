# A review of the suites and harness on `integration`, before R.1

## For Andre

- **What this is:** a read-only review of the suites and the harness on `integration` (@614af5c),
  done by a second model (Fable) after F.2 closed. Nothing was run. It asked whether R.1 could
  trust what it measures. It found two blockers, both fixed in F.3. It also found four
  should-fixes, which are scheduled, not fixed.
- **Blocker 1, the suites:** `integration` still ran the suites from before 2026-11-06's
  correction. That is, Medium and Hard prompts that disagreed with their roadmaps and cued a wrong
  import, Hard's `layout.json` without `migrations.py`, a dead assertion at
  `hard/grader/test_phase5.py:36`, and a Phase 5 grade that depended on Phase 2 running first.
  The fix is on the old branch (16cf9f9, 7b791ff, 9105bd4).
- **Blocker 2, the budget:** `wall` was taken from trace timestamps, so F.1's 900 s hang read as
  59.8 s. `turns` was computed the same way as `requests`. `run.json` did not say whether the
  deadline fired. The old branch has an `execution.json` and `completion` to port.
- **What to look at:** the four should-fixes below, and where each one lands.

**What is measured.** Nothing new. The review read code at `614af5c`. The 59.8 s and 900 s figures
come from F.1's run (`evals/2026-11-07-f1-payload`). The suite defects are in the files named.
The old-branch fixes were tested there (learn/code 495 passed, node 696).

**What is conjecture.** Whether either blocker would have changed an R.1 verdict. The review
inferred that from the defects. It did not measure it.

**Provenance.** The full review text was not kept. This note is built from its summary in the
session log (`FIXES.md`, entry "2026-11-07 late — F.2 closed"), checked against the code on
`integration`.

## Ladder run

None for the review. F.3 proves its fixes with a Vanilla smoke on Easy at n = 3 (see the
[F.3 plan](../plans/archive/2026-11-07-f3-instrument.md)).

## Persuasion → enforcement

The review is about the instrument, not the worker, so it moves nothing from persuasion to
enforcement. Two of its findings are about enforcement in the settle layer. Both are listed
below, and they land before any `check/*` remedy is measured.

## Should fix (scheduled, not done in F.3)

| Finding | Why it matters | Lands with |
|---|---|---|
| `qualify` passes when any one check fails, so a vacuous check is invisible | A grader can be cited as qualified while one of its checks tests nothing | A stronger `qualify` (one broken fixture per module, or mutations), owed before any grader is cited as qualified |
| Settle checks have no timeouts, and each handler replaces `entries` (`runner.ts:1056`) | Two red gates lose a message, and a hung check hangs the session | The first `check/*` arm in R |
| The oracle runs under the model's pytest config and an unfrozen `uv run` | The worker could change how it is graded | R.1, with the acceptance package |
| Two rigs: the ladder's `screen.sh` runs with thinking off, the harness with thinking on, and `AGENTS.md` still names `screen.sh` | Numbers from the two rigs get mixed | F.3 Task 4 (the wording). The rule (no mixing) is already in R.1's Excludes |

**Also flagged:** R.1 has no arms, n or rule yet, and Easy's hidden checks are at the ceiling.
R.1 should be scored with the acceptance package, at n ≥ 12. **Improvements:** a port-8000
preflight in the harness. One old-branch mediated test is stricter than the spec.

## What would falsify this

The F.3 smoke would show it if a deadline-killed session's `wall` still differed from its process
time, or if its `completion` read `settled`. A rerun of an old Hard record with `--specs original`
that changed its grade, other than through the grader fixes, would show the variant is not
faithful.

## Risks

The summary may have dropped a finding that the full text had. The old-branch fixes were
reviewed once, in that branch's own context. F.3 reruns their tests on `integration`, but it does
not repeat that review.
