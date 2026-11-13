# Delegation vs. remedies — does a thinking primary replace the remedy stack?

**What is measured:** nothing yet — this note holds a screen in progress, not a
result. **What is conjecture:** everything below the line until the run lands.

## The question

The worker now carries a primary-side `delegate` tool (and `/mellum <task>` runs
it): the primary explores, decides the layout and pins the goal with a failing
test, then hands the implementation to a bare local worker. The theory under
test is whether that division of labour closes the same gaps the remedy preset
exists to close — i.e. **whether we still need remedies on the harder tiers**.

An n=1 lead on easy already holds: on a generic slugify brief and on a FastAPI
`/health` brief, the primary delegated and the bare worker (no preset) passed,
verified by re-running the test. Easy is multi-modal, so one pass is a lead.

## The screen

- **Rig:** the shipped flow harness (`learn/code/flow_run.py` +
  `extensions/mellum-flow.ts`) — orchestrator (the primary, think high/medium)
  decomposes the suite into phases, drives the fixed worker, gates each phase,
  best-of-N within a phase, git-checkpoints a passing phase. This is the real
  harness, not a scratch driver.
- **Arm:** bare worker, **no remedy preset** — the orchestrator's plan and the
  phase gate are the only scaffolding. (The comparison arm, the tier preset, is
  a later run if this one warrants it.)
- **Suites:** `medium` (4 phases) and `hard` (11 phases).
- **Model:** Mellum 2.1 12B-A2.5B-Thinking, Q4_K_M, llama-server on :8001,
  `--context-window 50000`, `--concurrency 1 --attempts 4`.
- **Scoring:** the suite's **hidden grader** is the oracle, not the phase gate
  the orchestrator wrote. Report the hidden grade per tier, plus turns and wall
  per phase.
- **Command:**
  `uv run python learn/code/flow_run.py --suite medium,hard --concurrency 1 --attempts 4 --model Mellum2.1-12B-A2.5B-Thinking --context-window 50000`

## Result (easy, n=1 — a lead)

Easy = AgentClinic Phase 1 home page, delegation loop (`/mellum <task>`: architect
writes the handover, bare worker runs it to pass), **no remedy preset**, scored on
the suite's hidden grader (4 checks). The task fed in was the committed prompt
`suites/easy/prompts/01.md` verbatim.

| Architect's acceptance test | In-loop acceptance | Hidden grade |
|---|---|---|
| **thin** (v1: "define done", worker wrote ~1 check) | PASS ✅ | **2/4** — missed `lang="en"`, nav links |
| **complete** (v2: "assert EVERY requirement in the spec") | PASS ✅ | **4/4, full pass** |

The finding: the bare worker clears easy **when the handover is complete**. The
failure mode was never the worker — it was the architect writing a thin oracle
(200 + a tagline), which the worker dutifully passed while the spec's `lang` and
navigation went unbuilt (visible-pass / hidden-gap). Strengthening the architect
prompt to enumerate and assert every spec requirement lifted the hidden grade
2/4 → 4/4 with no change to the worker and no remedies. So on easy the lever is
**handover completeness**, which is the "make complete real" discipline
(AGENTS.md §6) applied to the architect rather than a remedy on the worker.

**Reliability:** the strengthened architect cleared easy 4/4 on three separate
clean runs (deleg3, deleg4, live3). The earlier one-off 0/4 was a grading race
(graded mid-flush), not a real fail. Architect span on the live run: 9 turns /
131s; the worker span is not in the records (see finding 2).

### Two findings from watching a run live (verbose)

1. **The architect (Mellum) sometimes writes a syntactically broken test** — e.g.
   `assert "href="/"" in content` (nested unescaped quotes). Completeness is up,
   but correctness of the authored oracle varies run to run.
2. **The freeze-the-oracle guard is leaky.** `chmod 0444` on the acceptance test
   did not stop the worker: an `edit` that rewrites/recreates the file bypasses
   the file's read-only bit while the directory is writable, so the worker edited
   `tests/test_acceptance.py` several times — here to repair the architect's
   syntax bug, but it could as easily weaken it. A real freeze needs the directory
   held read-only (or tamper-detection that re-fails on any change to the test),
   not just the file mode. **Candidate guard — add only if medium's evidence shows
   it changes the hidden grade** (per "only add guards if needed").

### Medium (single-shot, all 4 phases, bare) — hidden 0/18

Fed the committed medium spec (prompts 01–04 + specs/roadmap.md) as one task. The
architect wrote a 148-line acceptance test; the worker built app.py, models.py and
three templates. The home page is correct (200 + tagline + doctype + lang pass on
a direct probe), but the **hidden grade is 0/18** — and it's not a guard problem:

- **Root cause (handover completeness, not a guard).** The spec requires a
  **module-level `complaints` list** in models.py, seeded with 3–5 gripes (one
  exactly `Scope creep never ends.`). The worker instead used a class attribute
  `Complaint.complaints`, seeded one complaint, and never saved it. The grader's
  shared `_seed.py` does `tuple(models.complaints)` → `AttributeError` → the whole
  grader errors at collection → 0/18. One missed contract sinks every check.
- The architect's oracle was complete on routes/behaviour but **did not pin the
  exact named contract** (module-level `complaints`, the count, the exact seed
  string), so the worker passed the proxy while missing the real requirement —
  the same lever as easy (oracle completeness/accuracy), one level stricter.
- **No guard added.** The freeze-the-oracle leak (finding 2) never changed a grade,
  and the medium miss is completeness, not integrity. Per "only add guards if
  needed," none is warranted on this evidence.

Next lever to try: make the architect assert **exact named contracts** — module
and attribute names, collection names, counts, and verbatim seed strings the spec
gives — or delegate medium **per phase** (as the flow does), pinning each phase's
conventions before the next. Single-shot, bare, on medium is a lead at n=1.

### Medium re-run (named-contracts architect + compile-repair guard) — still hidden 0/18, new bottleneck

Two changes landed and were both exercised: the architect prompt now tells it to
assert **exact named contracts** directly (import the module, check the attribute,
its type, its length, the verbatim seed strings), and `doTask` now compile-checks
the authored oracle and re-dispatches to the architect to fix the **syntax** before
freezing (bounded, `MAX_ORACLE_REPAIRS`). What the re-run showed, n=1:

- **The named-contracts lever works and steers the worker.** The oracle pinned
  `hasattr(models, "complaints")`, `3 <= len <= 5` and the verbatim seed. The bare
  worker then built `complaints` as a **module-level `List[Complaint]` with 5 seeds**
  including `Scope creep never ends.` — exactly the contract the first single-shot
  missed (it had used a class attribute `Complaint.complaints`, seeded once). The miss
  the earlier screen root-caused is closed at the handover.
- **The compile-repair guard works, and finding 1 is reliable.** The architect again
  emitted a non-parsing test — nested double-quotes, `response.text.count("<div class="card"")`,
  the same shape as easy's `href="/""`. The guard caught it (`py_compile`), re-dispatched,
  and the architect fixed the quoting while keeping every assertion; the run then reached
  the worker, which the first single-shot never did (it looped on the frozen-but-broken test).
  The leaky freeze is now moot for this shape: the oracle parses before it is frozen.
- **Still hidden 0/18 — a different, third root cause.** The bare worker ran out of its
  turn budget while churning on **exact-match edits to `app.py`** (repeated read/edit cycles
  fixing indentation it had itself introduced), left `app.py` with an `IndentationError`
  on its final edit, and exited mid-fix. The grader errors at collection → 0/18. A read-only
  probe minutes earlier caught a transient `5 passed / 6 failed`, so the implementation was
  partway, not absent — the budget ran out before it converged.

So on single-shot medium the bottleneck has moved off the architect (completeness and
now syntactic validity are handled) and onto **worker throughput**: a bare worker holding
all four phases in one turn budget spends it on edit-precision churn and does not converge.
This is the case **per-phase delegation** is for — hand the worker one phase, checkpoint a
green phase, then the next — right-sizing each bite so no single turn budget has to carry
four phases. Not the model's ceiling; the bite is too big. Guards: the compile-repair guard
is kept (it changed the run — the first single-shot was blocked by exactly the bug it fixes);
no freeze or worker guard is added, since the freeze held and the miss is throughput, not
integrity. n=1, a lead.

### Per-phase delegation (MELLUM_DELEGATE_PHASED=1) — medium hidden 6/18, the first non-zero

Per-phase (`doTaskPhased`): the architect decomposes the spec into ordered phases and writes
one cumulative acceptance test per phase; each phase gets its OWN fresh worker (a fresh turn
budget) against the cumulative test, and a passing phase is git-checkpointed so a later phase
cannot silently break an earlier one. The throughput thesis held at n=1:

- **First non-zero medium.** The bare worker converged **phase 1 (home) and phase 2 (complaints
  board)**, both git-checkpointed, where single-shot churned a 4-phase spec to a hard 0. Hidden
  grade at the clean phase-2 checkpoint: **6/18** (phase-1 doctype/lang/tagline; phase-2 heading,
  seed-complaint listed, **seed count preserved** — the module-level `complaints` contract held).
  The final on-disk tree graded 8/18 with phase-3 residue (see the revert caveat).
- **The quote-rule and worker-scoping fixes worked.** All four phase tests compiled on the first
  authoring pass (no compile-repair needed), versus the two prior runs where the architect's
  nested-double-quote bug blocked the run. The worker, told to work only inside its own directory,
  stopped `find`-ing sibling workspaces (which had wasted a run).

What capped it at 6/18, each a known lever rather than a per-phase flaw:

1. **In-loop vs hidden completeness, per phase.** The architect's phase tests are looser than the
   hidden grader's: the worker's home page passed the in-loop phase 1 yet failed the hidden
   `nav_links` check; phase 2 passed in-loop yet failed the hidden shared-layout, seed-detail and
   model-contract checks. Same completeness gap as easy/medium single-shot, now per phase.
2. **A frozen-test RUNTIME bug the compile-check cannot catch.** The phase-3 test called
   `client.post(..., allow_redirects=False)` — removed from current starlette/httpx (it is
   `follow_redirects`). It compiles, so the guard passed it, but it errors at run time, so phase 3
   could not pass. Phase 4 was never reached; the loop reverted to the phase-2 checkpoint and
   stopped at 2/4.
3. **The freeze (chmod 0444) is defeated by `chmod +w`.** The worker ran `chmod +w` then `write`
   to edit the frozen phase-3 test (here to fix the `allow_redirects` bug — but it could as easily
   weaken a real check). `edit`/`write` alone were blocked; the explicit chmod was not. A real
   freeze needs a read-only directory or tamper-detection that re-fails on any change to a test.
4. **Revert-on-failure races the worker's trailing writes.** After phase 3 failed, `git reset
   --hard` ran, but the tree ended `M app.py` / `M test_phase3` — the spawned worker's last writes
   landed after the revert. So grade the committed checkpoint (6/18), not the dirty tree (8/18);
   the revert must wait for the child to fully flush.

Decision: per-phase is the right shape for a multi-milestone spec (first non-zero medium at n=1).
The remaining levers are the architect's per-phase completeness (match the hidden grader's
strictness), a freeze that a `chmod` cannot defeat, and a deterministic revert. Guards: none added
on this run — the evidence points at completeness and two harness-robustness bugs, not a worker
guard. n=1, a lead.

### Step-file delegation + code-eval remedies (MELLUM_DELEGATE_STEPS=1) — easy 4/4, medium 13/18 (n=1 leads)

Two levers from the 6/18 screen turned into a mechanism:

- **Steps, not phases.** `doTaskSteps` has the architect split the spec into the SMALLEST ordered
  chunks, each a `stepNN.md` doc (its own brief + named contracts) with a SELF-CONTAINED test
  `tests/test_stepN_*.py`, plus a `todo.md` ledger. A fresh worker reads only its step doc and makes
  that one test pass. The theory: a smaller bite than a phase is where a fixed turn budget converges,
  and a per-step doc keeps the worker from re-reading the whole spec each time. Each step is gated on
  its own test; a final full-suite run is the 100% check (a later step that regresses an earlier one
  fails there, not in a per-step gate — so "self-contained" stays honest).
- **todo.md is the harness's ledger, not the worker's.** The harness ticks a step only after it runs
  and passes that step's test itself, then git-checkpoints it; "done" means every box ticked AND the
  final full run green. This is the exit-gate discipline (don't trust the self-exit) made a file.
- **Remedies wired into the worker.** `MELLUM_DELEGATE_REMEDY=preset:medium` loads the measured
  remedy units as `-e remedies/<unit>.ts` before the worker extension — the same units the challenge
  harness applies — so the implementing worker gets the medium stack. Unset is the bare worker (the
  measured default); the architect pass stays bare. Whether the stack lifts the per-step hidden grade
  is the open question the next run answers.

The screen (local Q4 llama-server on :8001, `MELLUM_DELEGATE_STEPS=1`, verbose, n=1):

- **Easy — hidden 4/4, a full pass.** The architect split Phase 1 into 3 steps; it hit the
  nested-quote bug once and the compile-repair guard fixed it in one attempt. Each step's fresh
  worker (with `preset:easy` loaded) read its own step doc, built its slice, passed its own test →
  the harness ticked todo.md 3/3 and git-checkpointed. The in-loop 3/3 matched the hidden 4/4 — no
  visible-pass / hidden-gap. Architect 13 tool calls (+8 repair); workers 6/7/13; wall ~5m.
- **Medium — hidden 13/18, up from the 6/18 per-phase checkpoint.** The architect split the 4-phase
  spec into 4 steps (all compiled first pass, no repair). Every step ticked (todo 4/4, handover →
  step1 → step4 all checkpointed), and app.py + models.py + three templates were built. Hidden grade
  by phase: phase 1 home **4/4** (nav_links now passes, where per-phase missed it), phase 2 board
  **5/6** (misses seed-complaint *detail* rendering), phase 3 add **3/3** (per-phase never reached
  it), phase 4 resolve/reopen **1/5** (identity-stable-keyword-only, the resolve and reopen routes,
  and no-reorder all fail). Architect 28 tool calls; workers 12/15/24/23; wall ~13m (steps 62/94/
  249/221s).

So the smaller bite works: steps + remedies converged all four milestones' *own* tests and got the
first three phases to near-full hidden, where per-phase stalled at phase 2. What caps it at 13/18 is
the same lever as before, now concentrated on the **last milestone**: the architect's per-step test
is looser than the hidden grader (step 4's test passed in-loop, yet the real resolve/reopen contract —
stable keyword-only identity, the two routes' state change + redirect, board order held — is unmet),
plus one phase-2 seed-detail check. Not a step-file flaw; the per-step oracle needs the hidden
grader's strictness. n=1, a lead — a preregistered repeat against the per-phase arm would decide it.

## What would falsify "we no longer need remedies"

- A tier where the bare arm's **hidden** grade is below the tier preset's on a
  like-for-like run (same n, rig, model). The preset earns its place there.
- A failure shape the preset's units target (e.g. a foreground-server stall, a
  spec requirement the orchestrator's gate left thin) recurring in the bare arm.

## Risks

- n=1 per tier is a screen; a single pass or fail is a lead, not a rate. A
  deciding claim needs preregistered repeats against the preset arm.
- The orchestrator is itself scaffolding — a strong plan can do what a remedy
  would. "No remedies" is really "the orchestrator's plan instead of remedies."
