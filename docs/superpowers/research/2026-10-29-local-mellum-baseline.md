# Local MLX 6-bit vs the pinned BF16 baseline — what the quant costs

Date: 2026-10-29. Lifecycle: screen (n = 3 per rung, one serving stack, one
host). The point of this run was to see how far a locally-served 6-bit MLX
quant drifts from the pinned BF16 vLLM baseline, on the same vanilla Pi, with
nothing else changed. The record is `evals/baseline/2026-10-29-local-mellum-baseline/`;
the comparison target is `evals/baseline/2026-10-28-vllm-baseline` (26/36).

## What is measured / What is conjecture

**Measured.** Vanilla Pi 1.3.0 (`--mode primary --plain`, the recorder only),
driving Mellum 2.1 6-bit on oMLX 0.7.1rc1 at `127.0.0.1:8001`, on an Apple M3
Max, over AgentClinic rungs 1–12 at n = 3, 600 s deadline. Scored by the
ladder's own pass/fail, the same arm and rule as the BF16 record.

| Rung | Local 6-bit | BF16 | Δ |
|-----:|:-----------:|:----:|:-:|
| 1  | 3/3 | 3/3 | = |
| 2  | 2/3 | 3/3 | ▼ |
| 3  | 3/3 | 3/3 | = |
| 4  | 2/3 | 3/3 | ▼ |
| 5  | 1/3 | 2/3 | ▼ |
| 6  | 0/3 | 0/3 | = |
| 7  | 1/3 | 2/3 | ▼ |
| 8  | 1/3 | 1/3 | = |
| 9  | 0/3 | 1/3 | ▼ |
| 10 | 2/3 | 2/3 | = |
| 11 | 3/3 | 3/3 | = |
| 12 | 3/3 | 3/3 | = |
| **Total** | **21/36** | **26/36** | **−5** |

The 6-bit quant lands **5 passes below** the pinned BF16. The gap is not
spread evenly: five rungs (2, 4, 5, 7, 9) each drop one pass, and the other
seven match exactly — including rung 6, the wall where both score 0/3. The
quant never beats the full-precision model on any rung.

**Conjecture.** The loss looks like a **marginal-case** effect, not a floor
collapse: the rungs the quant drops are the ones BF16 itself only half-clears
(2/3 at rungs 5 and 7, 1/3 at rung 9), so a small capability shave tips an
already-shaky pass into a fail. The rungs both clear cleanly (1, 3, 11, 12) and
the rung both fail (6) are untouched. That pattern is what a modest
quantization cost would predict — it eats the near-misses first — but n = 3 on
one host is too thin to call it more than a lead.

## What would falsify this / Risks

- **Different serving stacks, not a clean quant ablation.** Local is oMLX/MLX
  on Apple silicon; the baseline is vLLM 0.32.0 on an RTX A6000. Templating,
  samplers, tool-call parsing and defaults differ between the two servers, so
  part of the −5 could be stack, not precision. A true quant ablation would
  serve 6-bit and BF16 on the *same* stack.
- **A toolchain divergence rode along.** This run used the system `pi`, so Node
  was v26.9.0 against the pinned 22.19.0 (Pi 1.3.0 matched). Pi ships its own
  runtime, so this likely does not touch the model, but it means the run is not
  byte-identical to the pinned recipe.
- **n = 3, one host, one quant.** A screen, a lead — not a rate. The per-rung
  deltas are one pass wide and sit inside the noise a 3-sample count carries.
  An 8-bit run on the same oMLX stack would separate "6-bit specifically" from
  "any MLX serving of this model".
- **The comparison is against a recorded number, not a paired re-run.** BF16
  was measured on a different day on rented hardware; nothing was re-run
  alongside the local arm, so day-to-day server variance is uncontrolled.

## Decision

Keep this as the local screen for the quant: good enough to say the 6-bit MLX
path trails the pinned BF16 by about 5 passes and clears the cheap and the
hard-structured rungs unchanged, cheap enough to re-run on the laptop. It does
not move a measured default — the pinned baseline stays BF16 on vLLM. The open
lead is a same-stack 6-bit-vs-8-bit-vs-BF16 ablation on oMLX, which would
isolate the precision cost from the serving-stack cost this run confounds.
