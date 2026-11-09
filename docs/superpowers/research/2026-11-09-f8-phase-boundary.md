# F.8: a verified, bounded phase boundary

## For Andre

**Date:** 2026-11-09. **Cycle:** F.8, cut from `integration` at `3875af59` ([design](../specs/2026-11-09-f8-phase-boundary-design.md),
[plan](../plans/archive/2026-11-09-f8-phase-boundary.md)). **What is measured:** deterministic tests, each
seen failing before its code, and one offline acceptance of a saved build. No model or GPU ran.
**What is conjecture:** whether any of this changes a model's acceptance rate or cost. Nothing here says so.

**What changed.** A phase now ends with a verdict the model cannot give itself. Each guarantee is one
commit, so it can be taken or refused alone:

| Guarantee | Mechanism | Proven by |
| --- | --- | --- |
| The bash bound holds at 120 s | `MELLUM_BOUND_SECONDS` clamped; a timeout of 0, a negative or a string takes the bound | `tests/remedy-bounded-commands.test.mjs` |
| Green means proven | A report plugin beside the frozen copy; every test function in the frozen source must pass. Exit 0, a skip or a short inventory is never green. Dependencies frozen at load. | `tests/remedy-gate-run.test.mjs`, incl. two real `uv` + pytest runs |
| Explicit settle verdicts | `green`, `red`, `exhausted`, `infrastructure` to `MELLUM_GATE_LOG`; one silent retry on infrastructure; the last repair after the cap is checked; feedback carries assertions, not server logs | `tests/remedy-mediated-test.test.mjs` |
| Handover closed | Private copies outside the repository, deleted by the unit with their env path before the first turn | both suites (`handed`, `hand_over`) |
| Supplied tests stay supplied | New explicit `guard/supplied-tests`: refuses `write`/`edit`, restores after every tool, new test files untouched | `tests/remedy-supplied-tests.test.mjs`, one test per route |
| Phase scope | Grade phases 1..N only; Easy's Phase 2–4 briefs in `phase-prompts/` | `learn/code/tests/test_phase_boundary.py` |
| The boundary | `--phase N` grades the stopped snapshot on any ending; accepted = strict pass + every mediated test | `test_phase_boundary_run.py` |
| Verified checkpoints | Accepted only; flow's git checkpointing; `--from-checkpoint` refuses wrong suite or phase, changed files, or a failed re-run of earlier phases | `test_phase_checkpoint.py` |
| No advance when unverified | A settle-gated multi-prompt run stops at `unverified_exit` | `test_phase_boundary_run.py` |

**What to look at:** the definition of green in `remedies/gate-run.ts`, and `decide` in
`learn/code/phase_boundary.py`. Your `mellum-verify` on `main` (`67f0138f`) has four of the gate defects
fixed here: `execSync` with no timeout, settle entries replaced rather than kept, exit 0 read as green, and
no check after the cap. The [handover](2026-11-09-handover-to-andre.md) lists what each costs to refuse.

### Corrections to the design (dated 2026-11-09)

- **One false failure reaches R.1a.** The design said both known hidden-grader false failures wait for
  Phase 3. The exact `Complaints Board` heading check is also in Easy's `f7-roadmap` Phase 2
  (`test_phase2_board.py:36`). F.8 leaves the grader alone; the backlog entry's reopen condition now names it.
- **A Phase-1-only build fails Phase 2 whole.** Phase 2's checks import `models.py`, so collection fails
  and every check, Phase 1's included, is listed missing. The verdict is right; the diagnosis is coarse.
- **A two-prompt run with a settle gate now needs a green verdict to continue,** so test fakes that model
  a settled session write one.

### Whole-branch review

A fresh review found no critical issue. Fixed, each with a test seen failing first: the gate had dropped
uv's cache and Python location variables (a warmed pod would read `infrastructure`); a packaged project
was built from a folder holding only its config, and a src layout did not import; the before-prompt
restore could write, as root, through a `tests/` symlink the session planted; a long collection error
lost its last line. Deferred, in the plan's ledger: the gate log is predictable and writable by the
session, so the between-prompt stop and the recorded gate verdict can be forged (acceptance cannot); the
gate and trusted grading count test functions slightly differently; the shared gate environment and
import path are not a sandbox; `harness checkpoint` fails noisily on an existing `--out`.

## What R.1a now needs

- **A Phase-1 checkpoint: done.** Easy `base-r02` from the final count, accepted offline under
  `f7-roadmap` at phase 1 (hidden, project, lint, all 16 mediated functions; its trace shows no
  contamination), at `~/mellum-runs/f8/easy-phase1-base-r02`, commit `ffced376`. It is outside git;
  `harness checkpoint` rebuilds it from the retained workspace. `verify_checkpoint` passes for phase 2.
- **The command,** Base as counted plus the phase flags, run from `learn/code`:
  `uv run python harness.py run --suite easy --grader f7-roadmap --phase 2 --from-checkpoint ~/mellum-runs/f8/easy-phase1-base-r02 --arm vanilla --remedy tool/bounded-commands,check/mediated-test-settle --host-card <card>`
  with the Easy budget (128 requests / 64,000 charged output), pinned Q4 and a matching host card, and the
  trace follower on screen.
- **Paul's calls before it starts:** whether `guard/supplied-tests` joins the candidate (it would be a
  second change); whether to fix the Phase-2 heading check first, under a new grader identity, or let a
  heading miss on a valid build trigger the backlog entry; and pushing this branch if Linux cleanup should
  be exercised by CI first.

## Ladder run

None: deterministic tests decide. The one replay of a real build is the offline acceptance above,
through the trusted grading path. R.1a is the next inference, started only on Paul's word.

## Persuasion → enforcement

`tool_call` clamps the bound and refuses supplied-test edits; `tool_result` restores supplied tests
whatever route changed them; `agent_before_settle` runs the gate and records its verdict. The budget
proxy, trusted grading, the boundary decision and checkpoints sit outside Pi and need no cooperation from
the model. The only model-facing text that changed is failure feedback, which reports facts.

## What would falsify this / Risks

- A valid build the boundary rejects, or a defective one it accepts, needs a dated correction; the
  Phase-2 heading check is the known candidate.
- **Not a sandbox.** The model's code still runs in-process under the gate and the grader, and a session
  can find and write the gate log in its run directory. The boundary trusts only trusted grading.
- **Frozen dependencies need uv's cache.** The gate runs `--offline`; on a fresh host the first check can
  read `infrastructure` until the project has been synced once.
- **Linux cleanup is unexercised.** `stopSessionProcesses` reads process environments with `ps axeww`;
  its tests have run on macOS only. They reach Linux on CI when this branch is pushed.
- `guard/supplied-tests` is unmeasured; restoring a file could cost turns as easily as save them.
