# 2026-10-21: the 6-bit clears the new hard rungs 10–12

**What is measured.** The 6-bit Mellum (`Mellum2.1-12B-A2.5B-Thinking-6bit`) run
on the three new AgentClinic rungs — 10 (Archive & Audit), 11 (reporting over a
database), 12 (sum two columns of a context-overflowing file) — the run
standard (`scripts/screen.sh`): direct mode, `tuned`, **mediated** (the committed
frozen phase test placed and re-dispatched on failure), `--redispatch 5`,
effort-ramp, guards on, repeat 3. Result (`table.md`): **rung 10 3/3, rung 11
3/3, rung 12 3/3 — 9/9.**

**Takeaway.** The three hardest rungs are winnable by a capable worker, and the
mediation does visible work getting there. The frozen test re-dispatched the
worker on **7 of the 9 runs** (`redispatch_attempts` 1–2): the first attempt was
a near-miss, the frozen test caught it, and the worker converged to a pass. Only
two runs passed on the first attempt. This is the M.11 lead in the wild — an
external, complete, uneditable test turning a near-miss into a pass — on rungs
built to punish the shortcut (rung 10's destructive-archive decoy, rung 11's
archived-but-open trap row, rung 12's file far larger than the context window).

**Why it matters for the new rungs.** Each rung is a real gate, not busywork:
the oracle is hidden and cumulative (rung 12 still runs phases 1–7), the frozen
acceptance test is a superset the worker cannot edit, and the write-list blocks
touching the decoy files. A worker that cut the corner each rung is built to
catch would fail it. The 6-bit did not cut them.

**Caveats.**
- **Mediated, so this measures the worker-plus-mediation, not the bare model.**
  The redispatch counts show the mediation mattered; an un-mediated run would
  likely score lower (see the shipped-Mode and un-mediated baselines).
- **n=3 per rung.** Enough to show winnable and repeatable, not to estimate a
  rate precisely.
- Wall times include the re-dispatched attempts, so a re-dispatched run reads
  slower than a first-try pass.

Plain-concept walkthrough of the three tests:
[`research/2026-10-21-rungs-10-12-explained.md`](../../superpowers/research/2026-10-21-rungs-10-12-explained.md).
Raw `trace.jsonl`/`stdout.txt`/`diff.patch` stripped (`AGENTS.md`); each run
keeps `run.json` and `final.md`.
