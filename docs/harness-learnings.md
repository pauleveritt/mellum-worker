# Flow harness — learnings for a new builder

A handoff of what we've learned building the spec-driven flow harness
(`learn/code/flow_run.py` + `extensions/mellum-flow.ts`), which drives a FIXED
small model through a multi-phase build and grades it. Read `AGENTS.md` and
`docs/sdd.md` first — they're authoritative; this is the field guide.

Each point is marked **[measured]** (a run or a green test backs it) or
**[lead]** (plausible, not yet proven). Don't promote a lead to a claim without
a run.

## 1. The model is fixed; the harness is the only lever

The model doesn't change. Every gap is the harness's job, never "the model
can't." Say a result only when you've measured it, and label a lead as a lead.
This isn't modesty — it's what stops you from shipping a "fix" that a run would
have caught as a regression. **[measured]** (the project's whole record is
runs that overturned plausible-sounding changes).

## 2. The oracle and the proxy — never confuse them

- The suite ships a **hidden grader**. That's the **oracle** — the real pass.
- The examiner writes an **acceptance test** per phase. That's a **proxy** — the
  harness's own reading of the spec.
- A phase passing its own gate is **not** a hidden pass. The sharpest example:
  a build passed all seven phase gates and the hidden grader still scored
  31/34. **[measured]**
- So: judge on the hidden grade; report a proxy pass *as* a proxy pass. If your
  dashboard says "phase 5 PASS" and you quietly mean "passed the test it wrote
  for itself," you'll fool yourself.

## 3. Keep it agnostic — the gate is spec-derived, never the oracle

The examiner writes the gate from the SAME inputs the coder gets: the phase
spec (`plan/TASK.md`), `specs/`, and the real database schema. The hidden grader
is **absent from the workspace** — verify this stays true. **[measured]**

Reading the grader yourself to *diagnose* is fine. Encoding its answers —
hardcoding a route, a column, an expected value the spec doesn't give — is
cheating, and it makes every later pass meaningless. Fixes must be general
test/harness discipline that would help on any suite.

## 4. For a fixed small model, harness guarantees beat prompt rules

A prose rule in a prompt lands unreliably. A mechanism doesn't depend on the
model behaving. The ones that earned their place **[measured]**:

- **Restore the fixture before grading.** A report-phase test that mutated the
  fixture db corrupted the data the grader reads; restore each fixture table's
  rows from the pristine base before the authoritative grade, keeping the
  coder's migrated schema (column intersection).
- **Score each phase on its OWN gate.** One brittle earlier gate was
  false-failing every later phase; per-phase scoring stops the cascade.
- **Inject the real schema** into the phase task, so the coder uses columns that
  exist instead of inventing them.
- **Git-checkpoint each passing phase; revert a breaking change** rather than
  carrying rubble forward, and never grade an app that doesn't compile.

## 5. The retry loop MUST feed the concrete failure back to the actor

This is the biggest single lever we found. **[measured failure mode; fix
committed; hidden-grade impact is a lead]**

- When the gate fails, hand the coder the **actual failure** — the failing
  assertion, the 404 on the route it never built — not just "try again."
- We had a bug where it didn't: `code()` read only the reviewer's prose;
  `test()` wrote its pytest output nowhere the coder read. So on every retry the
  coder rebuilt from the plan **blind** and repeated the exact same omission
  (Mellum dropped a required `archive` route, 404 every round).
- **best-of-N does not fix this.** Parallel samples buy *variance* (they help a
  stochastic miss); a *systematic* omission repeats at every temperature. We
  watched both best-of-2 temps make the identical miss. Feedback buys
  completeness; concurrency doesn't.
- **Verified exit:** "done" means the harness re-ran the frozen gate and it
  passed — never the model's own say-so.

## 6. Don't let one command hang the whole loop

A blocking command (a foreground server, an unclosed-quote `echo`, a REPL, a
`read`) freezes the phase until the global reap. **[measured]**

- Use the runtime's per-command timeout, and make it an **idle** timeout —
  re-armed on every output chunk — so a long but *actively producing* command is
  never killed, only one that's genuinely silent/stuck. A flat wall-clock
  timeout kills work that's still making progress; that's not a fix. (We put the
  idle timeout in our pi fork's bash executor.)
- Close stdin by default (an unclosed quote then errors fast instead of
  waiting). Thread a real server into the background with its output to a log
  and its pid returned, so the model can read it and stop it.
- Make sure the harness runs **our** forked runtime, not the stock one, or none
  of this is active for whoever clones the repo.

## 7. Concurrency — what best-of-N actually buys

**[measured]**

- Throughput, not latency, and **sublinear**: ~2–2.5× aggregate at N=4 on the
  batched server, knee at N=4–8. A single dependent plan→code→test chain doesn't
  parallelise at all.
- The real win is variance-reduction on the hard phases; on a phase that passes
  first try, concurrency is pure wasted compute.
- Use **escalate-on-retry** (`--concurrency 1 --retry-concurrency N`): one cheap
  attempt first, best-of-N only where a retry actually happens.
- The bigger speed lever was often the **smaller context window** (leaner KV per
  request), not more parallelism.

## 8. Model portability — two floors, not one

**[measured]**

- **Format floor:** emit a tool call the runtime can parse. A content shim
  (`extensions/content-tool-call-assist`) lowers this — it promotes a call the
  model wrote as text (fenced JSON, a positional list, Hermes/Qwen XML) into a
  named-args call.
- **Capability floor:** form a *complete, correct* call and sustain a multi-step
  loop. The shim does nothing for this.
- A 1.5B reasoning distill cleared neither cleanly (it emits incomplete calls).
  A small instruct/coding MoE, heavily quantised, cleared both and drove the
  harness natively. Tool-use training and task type matter more than raw
  parameter count here.
- On this serving stack, per-request thinking controls (`--thinking`,
  `enable_thinking`) are **no-ops** — thinking is a property of the weights plus
  `max_tokens`. Don't build a "fix" that assumes you can toggle it per call.

## 9. Make every run debuggable and visible

**[measured]**

- Log **every** sub-agent tool call to the live feed — the command and its
  target. We had a bug where sub-agent calls were never logged (the streaming
  keyed on an event type the runtime doesn't emit), so a hung phase showed only
  a frozen event count and nothing to diagnose. A hang you can't read is a hang
  you can't fix.
- Keep long runs on screen; don't bury a run behind a sentinel that reports only
  the final number. You'll miss the stall that explains the result.

## 10. Process discipline (this is why the numbers are trustworthy)

- **Screens first, preregister the deciding run.** Fix arms, n, scoring and the
  rule *before* a run that decides a change. A screen is a lead, not a rate.
- **Record every measured result in the repo** (`docs/superpowers/research/`,
  `evals/`), never in a scratch dir. A claim with no committed record is a
  lead.
- Atomic, pushed, individually-revertible commits; tag known-good milestones.
- Everything through `uv run` — the pinned env is what makes a run reproducible.

## 11. The open levers (what we'd work on next)

All **[lead]** — unbuilt or unmeasured:

- **Completeness gate.** The planner and examiner both know a requirement is
  required (the gate asserts it), but nothing forces the coder to implement
  *every* named route/requirement before the gate runs. A coverage check — the
  routes/requirements the spec names must exist — would catch the
  requirement-drop that caps the hard phases.
- **Stabilise the examiner.** On the heavy phases it over-generates (one phase's
  gate swung between 54 and 187 lines across runs) and is slow and brittle. A
  lever to constrain and stabilise what it writes is worth a run.
- **Free vs forced flow.** A variant where the agent decides its own steps and
  the harness enforces only two invariants — a frozen external gate before any
  build, and a verified exit — is built behind `--flow-mode free`. The
  preregistered forced-vs-free comparison hasn't been run.
- **Learned memory.** A portable store of general, agnostic lessons distilled
  from the agent's own failures, injected like a skill. Prototype only; the
  with-vs-without uplift on the fixed model is unmeasured, and the agnostic
  guard (never store the suite's answers) is the load-bearing part.

## The one-line version

The hidden grader is the only honest judge; everything the harness does is to
remove obstacles between a fixed model and that judge — restore the data, feed
back the real failure, never let a command hang, and never kid yourself that a
test the harness wrote for itself is the real thing.
