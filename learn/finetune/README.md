# Fine-tuning Mellum for task adherence

A DoRA fine-tune that teaches the fixed Mellum model to **stay on the task** -
the pathology Andre named as the small model's worst habit (drop a requirement,
wander, build in the wrong file). See the full record and the risks in
[docs/superpowers/research/2026-11-10-mellum-adherence-finetune.md](../../docs/superpowers/research/2026-11-10-mellum-adherence-finetune.md).

## The result (held-out)

Trained on **winner traces only** (runs/evals where the hidden grader passed, the
build stayed in the layout, and the tests were untouched), with **phase-4 held out
entirely**. On that held-out phase-4 set the tune generalised:

| | base | tuned (DoRA) |
| --- | --- | --- |
| held-out loss | 1.806 | **0.613** |
| perplexity | 6.08 | **1.85** |

This is teacher-forced loss on winner traces - a proxy, not a pass-rate. **The live
harness reversed it:** the tuned Q4 lost on both tiers (easy 1/6 vs base 4/6;
medium 0/18 vs base 16/18). The proxy rewarded predicting winner-trace tokens -
terseness and early exit - not capability, so this configuration over-specialised
and does not ship. Full numbers and the lesson in the
[research note](../../docs/superpowers/research/2026-11-10-mellum-adherence-finetune.md).
The pipeline, the held-out discipline, and local tuning all stand; gentler settings
and a larger winner pool are the open corrections.

## The pipeline

1. **`make_sft.py`** - mine clean-winner traces into (context → on-task action)
   examples in the model's native tool-calling format; hold phase-4 out.
2. **`mix_general.py`** - blend ~15% general coding-instruct (CodeAlpaca) as a
   regulariser against over-specialisation.
3. **`compact.py`** / `filter_raw.py` - cap each message and drop giant contexts
   (raw tool-output dumps) so examples fit memory and teach adherence, not noise.
4. **`train_run.sh`** + **`lora_config.yaml`** - DoRA, all attention projections,
   rank 32, lr 1e-4, grad-checkpoint, via `mlx-lm` on the 4-bit MLX base.

## The data (committed)

- `data/train.jsonl` - 480 adherence + general examples (compacted, ≤2k tokens).
- `data/valid.jsonl` - 62 (note: shares traces with train, so its loss leaks -
  judge by the held-out set, not this).
- `data/holdout_phase4_test.jsonl` - 78 phase-4 examples, never in training.

## Small-model notes

Small models absorb **structure and style** (adherence), not new facts - so
Python 3.15 or new-API knowledge is a RAG/context job, never this tune. Keep the
general mix in to protect coherence; watch the held-out set, not train loss.
