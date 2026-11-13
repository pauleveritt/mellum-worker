# The dense-phase wall survives every model-side lever

Date: 2026-10-27.

## What is measured / What is conjecture

**Measured (screens, n=1 per arm — directional, not preregistered rates).** On
the hard suite, the fixed model (Mellum 2.1 12B-A2.5B Thinking, served via
mlx_lm.server) fails **phase 5 ("Archive & Audit")** across every model-side
lever tried. Phase 5 bundles ~5 requirements (archive route with an exact 303,
an audit log with a monotonic sequence, status-filtered stats, migrations); the
model completes the salient one and drops the rest. Seeded runs start phases 1–4
from a fixed workspace (`ws-p5repro`) and run phases 5–7, so each arm is isolated
to the dense back half.

| Lever | Phase 5 result |
|-------|----------------|
| 6-bit base, best-of-N + coder feedback on | failed all 6 rounds (also seen in the overnight controls: 26/34, 27/34) |
| 6-bit + corrected tool-call adapter (v2, 200 samples) | failed rounds 1–2, same wall; tool *mechanics* clean (no malformed calls) |
| 8-bit base (precision bump) | failed round 1+, same wall |
| 8-bit + corrected adapter (retrain on 8-bit) | stalled (wedged in `plan`), no verdict |
| uniform decomposition (`MELLUM_SUBDIVIDE=1`, 35 sub-phases) | impractical — stalled on the *trivial* phase-1 sub-step |

The earlier format work is real and holds: the first (smoke) adapter, trained on
flat file dumps, **degraded** tool use (leaked `{"name":"plan","arguments":{}}`
as text); the corrected adapter, trained as tool-call trajectories, fixed the
mechanics. But fixing the format did not move phase 5.

**Conjecture.** That **adaptive decomposition** — run a phase whole, and only if
it exhausts its rounds subdivide *that* phase into one-requirement sub-phases and
retry — gets the model through the dense phases. Untested; it is the one path the
levers above point to and the only one not yet tried.

## Interpretation

The wall is a **throughput ceiling**, not a format, data, or precision problem:
the fixed small model cannot complete a phase that packs several requirements at
once, within budget, even told exactly what it missed. Three things this rules
out or settles:

- **Quantization is not the cause.** 8-bit is no better than 6-bit on phase 5, so
  the ceiling is the trained model, not the quant. (bf16 full precision was not
  tested — feasible but tight on this 48 GB machine; 8-bit is the precision point
  that was run.)
- **Format was a genuine bug, not the cause.** Correct tool-call training repaired
  the mechanics and still walled.
- **More of the same data won't help.** The 200-sample set, though correctly
  formatted, was structurally near-identical CRUD apps (val loss → ~0.0 =
  memorised the template); count and even precision stacked on it did not move the
  completeness gap on the dense phase.

## The lever that fits the diagnosis

Lowering the per-step load is the only thing that targets a throughput ceiling.
Uniform decomposition proves the mechanism (the loop gates, materialises
cumulatively, and checkpoints per sub-phase with no other change — see
`flow_run.py` `subdivide()` / `MELLUM_SUBDIVIDE`), but applied to *every* phase it
pays the full plan→examine→review→code→test overhead on the ~30 sub-phases that
already passed whole, and it stalled. **Adaptive** decomposition — subdivide only
a phase that fails whole — pays that overhead only on the walling phases (5, 6),
which is where it is worth paying.

## What would falsify this / Risks

- **n = 1 per arm.** These are screens, not rates; a preregistered multi-run is
  owed before any of this is stated as a measured pass rate.
- **A recurring generation stall confounds the runs.** The `code`/`plan` step
  wedges (event count frozen) on some runs, including a trivial sub-step, and the
  loop-breaker guard does not catch it. Some "failures" above are partly this
  serving/generation-stability issue, not pure capability — it must be fixed
  before the wall can be measured cleanly.
- **Adaptive decomposition is unproven** and is real loop engineering, not a flag.
- **bf16 full precision untested** — 8-bit settles most of the quantization
  question, but not all of it.
