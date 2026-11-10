# Handover to Andre: what the re-boot found, for you to take or refuse

## For Andre

**Date:** 2026-11-09, for 2026-11-10. **From:** Paul. **What this is:** everything since the 2026-11-07
re-boot, F.1 to F.8, offered item by item. Take what you want and refuse the rest; each row says what
refusing costs. **What is measured:** the cited run records, deterministic tests and saved-build replays.
**What is conjecture:** anything about savings, later phases, Medium reliability or Hard.

**Where the code is.** On branch `integration`: F.1–F.8 and R.1a, 27 commits past our common base
`33e0b929`, with F.8 as one squashed commit (`64999fd2`). **It is not on a remote yet;** you see it only
once Paul pushes. A text merge of the F.8 tree into your `main` at `67f0138f` conflicts in 13 files,
mostly docs, the changelog and the remedies pages (counted before R.1a was added).

*Correction, 2026-11-10:* an earlier draft offered F.8's branch `f8-phase-boundary` as one commit per
guarantee so you could pick. Paul chose to hand over the squash only; that branch is deleted, so take or
refuse F.8's guarantees by the rows below and their named files.

### How it fits with your direction

You and we converged on the same core: an external test re-run at settle, a refusal for commands that
only start a server, requests as the cost measure, and a compile/import check. The differences are in how
much is proven: our Easy numbers are n = 32 per arm, preregistered, on repaired suites; your one-pass
results are n = 2–3 screens with no Vanilla arm, on suites without our corrections. Neither establishes
the other's claims. Our [review](2026-11-09-phase-worker-review.md) records where we read you differently.

### Decisions for you

| # | Offer | Evidence | Code | If you refuse |
| --- | --- | --- | --- | --- |
| 1 | **The floor:** Vanilla Pi + recorder; the worker is a command tool; every behaviour is an explicit remedy unit; presets are results, not inputs | F.1 payload check: Pi's four tools, no `delegate`, no nudge | `extensions/mellum-worker.ts`, `remedies/` | Presets keep bundled units no run has credited |
| 2 | **Trusted grading:** hidden checks on a disposable copy with the suite's own dependencies; supplied-test integrity; versioned graders | F.4/F.7 [matrix](2026-11-09-f7-qualify-acceptance.md): ours rejects 33/33 Medium defects and passes 10/10 valid builds; your `test_medium.py` 11/6, your `67f0138f` grader 2/9 | `learn/code/grading.py`, `grader_history.py` | A build can pass on its own config or an edited supplied test: all five hidden-full, non-strict Base attempts changed the supplied test, and four still passed the project's own pytest |
| 3 | **Enforced budgets and host cards:** requests and charged output stopped at a proxy; a run counts only with a passing host card | F.5 [note](2026-11-07-f5-run-trust.md) | `learn/code/budget-proxy.mjs`, `conformance.py` | Cost is reported, not bounded; host differences go unrecorded |
| 4 | **The Easy count as the reference result:** Base (bounded commands + settle re-run) 25/32 strict vs Vanilla 2/32, but 4.47× the median output tokens against a 3× rule, so presets stay empty | [count](2026-11-09-easy-count-result.md) | `evals/2026-11-08-easy-final-count/` | Your Easy guidance (6/6 on four checks) stands alone; it cannot replace a thirteen-check count |
| 5 | **Medium diagnosis:** two real causes, not four missing features; the status label false failure fixed, the cross-path ID check added; the original grader kept as `--grader 658bbea5` | [F.7](2026-11-09-f7-qualify-acceptance.md); retained Base r02/r03 replays | `learn/code/suites/medium/` | Medium results stay confounded by a grader defect |
| 6 | **Settle gate fixes,** applicable to your `mellum-verify`: a bounded run (yours uses `execSync` with no timeout), earlier gates' entries kept (yours replaces them), green only when every expected test passed (yours reads exit 0 as green), and the last repair after the cap checked | F.8 tests; read on your `main` at `67f0138f` | `remedies/gate-run.ts`, `remedies/mediated-test.ts`, `extensions/bounded.ts` | A hung test stalls settle; a project's own pytest or a skip can read green |
| 7 | **Handover closed:** acceptance tests reach the session as copies it deletes before the first turn, and no path stays in the environment | F.8 tests; R.1 found one path-heuristic contamination flag | `remedies/mediated-test.ts`, `learn/code/harness.py` | The settle-only arm is not hidden; a command can read the test it should not see |
| 8 | **`guard/supplied-tests`** (explicit, in no preset): supplied tests cannot be edited and are restored after any command that changes them | Every hidden-full, non-strict Base attempt changed the supplied test; **the unit itself is unmeasured** | `remedies/guard/supplied-tests.ts` | Nothing, until a run measures it |
| 9 | **The bash bound holds at 120 s** under any configuration | [stall census](2026-11-09-phase-worker-review/stalls.md): bounded 0/122 stalls; F.8 fixed the configured-default bypass | `remedies/tool/bounded-commands.ts` | `MELLUM_BOUND_SECONDS=300` reopens the stall the cap was added for |
| 10 | **One phase at a time:** `--phase N` grades phases 1..N on whatever the session left; accepted = strict pass + every mediated test; only accepted work becomes a checkpoint, and the next phase starts only from a verified one | F.8 tests; Easy `base-r02` accepted offline as a Phase-1 checkpoint; [R.1a](2026-11-09-r1a-easy-phase2.md) accepted Easy Phase 2 from it, n = 1 | `learn/code/phase_boundary.py` | Phases advance on the model's word or an exhausted send-back cap |

### What a merge would change for you

- **Your presets would empty.** Your `easy` and `medium` presets list three prompts and
  `guard/foreground-server`; ours are `[]` because no unit beat Vanilla within its budget. Keep yours
  under another name if you want them.
- **Your `--mode plan` is untested against F.1's removal of the delegate tool.** Check it before merging.
- **Your recent docs pass** (British spelling, no em-dashes, the lessons) touches the same pages ours do;
  most of the 13 conflicts are there.

### What is trusted, and what is only advice

The handed acceptance tests are closed: deleted at load, with their path gone from later commands. The
in-session gate, its log and its environment are advice: a determined session could forge the log or
plant code in the gate's environment. Only the boundary is trusted: grading on a disposable copy with the
suite's own dependencies decides acceptance and checkpoints, and nothing the session writes changes it.

### What we do not claim

- No acceptance rate or saving from F.8: its guarantees are proven by unit and replay tests only.
- A phase-acceptance rate. [R.1a](2026-11-09-r1a-easy-phase2.md) ran once, after F.8: Base as counted, on the Mac, built
  Easy Phase 2 from the `base-r02` checkpoint and was accepted with 97 requests and 47,860 charged output
  tokens. That shows it can happen, not how often.
- Linux cleanup of leftover session processes is unexercised; it reaches CI only when the branch is pushed.
- One known hidden-grader false failure (an exact `Complaints Board` heading) applies to Easy Phase 2.

## Ladder run

No new run for this handover. Each claim links its record: the counted Easy run, the F.6 screens, the
F.7 matrix and F.8's tests. Where your results and ours differ, a paired run on one stack decides.

## Persuasion → enforcement

Everything offered above is enforcement: a Pi hook (`tool_call`, `tool_result`, `agent_before_settle`) or
the harness outside Pi (budget proxy, trusted grading, checkpoints). No prompt text is offered; the one
prompt-shaped change is failure feedback that reports facts.

## What would falsify this / Risks

A paired run on your stack that shows your one-pass setup passing our thirteen-check Easy grade at lower
cost would overturn row 4's reading. A valid build that our grading rejects needs a dated correction;
the Phase-2 heading is the known candidate. The conflict count is a text merge only; nothing was run merged.
