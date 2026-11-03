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
