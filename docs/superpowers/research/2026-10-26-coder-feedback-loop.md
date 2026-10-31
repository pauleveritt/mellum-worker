# Feed the gate failure back to the coder (the flow's missing retry signal)

Date: 2026-10-26. Status: measured failure mode + a fix (committed); the
hidden-grade impact is not yet measured — a lead, not a result.

## What is measured

Driving Mellum 2.1 through the hard suite (forced flow), Phase 5 (Archive &
Audit) failed its own gate every round, through 6 rounds of best-of-2:

- The gate fails with **404s**: it exercises `POST /complaints/{id}/archive`,
  `GET /stats`, the audit trail — and the app returns 404 on the archive route.
- The app declares `resolve` and `reopen` but **not** `/complaints/{id}/archive`.
  Mellum under-implemented the phase: it dropped one required route.
- Both best-of-2 temperatures (0.3 and 1.2) made the **identical** omission —
  a systematic miss, not sampling variance, so best-of-N cannot rescue it.
- Root cause in the harness: the **coder never saw why the gate failed**.
  `code()` reads `plan/REVIEW.md` (the reviewer's prose); `test()` wrote the
  failing pytest tail nowhere the coder reads — it went only to the
  orchestrator. So on each retry the coder rebuilt from the plan **blind** and
  repeated the same omission. (`code()`'s own description even claimed it reads
  "test feedback in REVIEW.md" — but nothing wrote it.)

## The gate is spec-derived, not the oracle (transparency)

The examiner writes the gate from the SAME inputs the coder gets: `plan/TASK.md`
(the phase spec — which literally specifies the archive route, the 400/303
behaviour, the audit entry shape, `/stats`), `specs/`, and the real DB schema.
The hidden grader is **absent from the workspace** (verified). So the gate is a
faithful, fallible **proxy** for the spec, never the oracle's answers. On Phase
5 the gate was **right** — archive is in the spec — and the build was
incomplete. A phase passing its own gate is still only a proxy pass; the hidden
grader is the oracle (31/34 = all gates green, hidden still docked 3).

## The fix

`test()` now writes the failing pytest tail to `REVIEW.md`, which `code()`
already reads. On a failed gate the coder sees the exact failing
assertion/route (e.g. the 404 on the archive route) and can fix **that** gap,
instead of rebuilding blind. This is the "didn't pass — here's what failed, try
again" loop the free arm already had, brought into the default forced flow.

## What is conjecture

That concrete-failure feedback lets the fixed model close requirement-omissions
like the missing archive route, and so lifts the hidden grade above the 31/34
ceiling on the heavy multi-requirement phases. Unmeasured — the deciding run is
a Mellum hard run on the fixed harness, judged by the hidden grader.

## What would falsify this / Risks

- **Falsified** if Mellum still drops the archive route with the failure in
  hand — then the ceiling is the model not acting on a concrete 404, not the
  missing feedback, and the lever is weaker than hoped.
- The feedback is the gate's tail; a truncated or confusing tail may not point
  the coder at the real gap.
- A systematic omission the examiner ALSO misses (writes no assertion for)
  would still slip through — feedback only surfaces what the gate already
  checks; completeness of the gate is a separate lever.
