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
The pipeline, the held-out discipline, and local tuning all stand. Two corrections
were tried: gentler hyperparameters (rank 8) regressed further (easy 0/6, zero tool
calls on half the runs), and a full-length data rebuild (rank 16, no compaction)
**fixed the behaviour collapse but not the pass rate** (easy 1/6, still below base's
4/6). Three screens agree it does not beat base.

**Correction (2026-11-11):** `make_sft.py` also dropped every history assistant turn
(the payload keeps `tool_calls` at message level, which `to_openai` never reads), so
all SFT contexts were tool results with no actions before them - 466/466 v2 examples.
The "self-distillation ceiling" explanation is therefore a theory, not a finding.
Details, and the native-format DPO rebuild, in the
[research note](../../docs/superpowers/research/2026-11-10-mellum-adherence-finetune.md).

## The pipeline

1. **`make_sft.py`** - mine clean-winner traces into (context → on-task action)
   examples in the model's native tool-calling format; hold phase-4 out.
2. **`mix_general.py`** - blend ~15% general coding-instruct (CodeAlpaca) as a
   regulariser against over-specialisation.
3. **`compact.py`** / `filter_raw.py` - cap each message and drop giant contexts
   (raw tool-output dumps) so examples fit memory and teach adherence, not noise.
4. **`train_run.sh`** + **`lora_config.yaml`** - DoRA, all attention projections,
   rank 32, lr 1e-4, grad-checkpoint, via `mlx-lm` on the 4-bit MLX base.

## Preference tuning (DPO, native format)

Two scripts replace the SFT path for preference work. Both use `mlx-lm` 0.32.2
and `mlx-lm-lora` 5.10.2, run on the M3 Max.

1. **`build_dpo_native.py`** - mines `runs/` and `evals/` run records and pairs,
   per phase, a clean winner (`chosen`) with a graded failure (`rejected`).
   - Each trajectory is re-rendered exactly as the server saw it.
   - Every assistant turn is restored with its reasoning and native `tool_calls`.
   - Tool results are capped (400-character head + 200-character tail).
   - The mask scores assistant tokens only.
   - Over-budget sequences are dropped, never truncated.
   - Phase-4 trajectories are held out for validation (2 winners, 3 losers).

   Run with no `--budget` to only measure. `--budget 41000` gave 48 train and 6
   valid pairs.
2. **`dpo_native_train.py`** - our own IPO-DPO step (loss normalised per token,
   β 10).
   - Scoring is chunked with a KV cache.
   - The backward pass is chunked over the LoRA parameters only.
   - `--check-grad` compares the chunked gradient against the exact one; cosine
     was 0.938 at chunk 512.
   - We use our own step because upstream `mlx-lm-lora` silently ignores the loss
     type and runs sigmoid; you can tell from an iter-1 loss of 0.693 instead of
     (1/2β)².
   - Upstream also fails to backprop through 4-bit weights and cannot reset
     Mellum's sliding-window cache.

```bash
uv run --with mlx-lm==0.32.2 --with mlx-lm-lora==5.10.2 python build_dpo_native.py --budget 41000 --model <mlx-model>
```

```bash
uv run --with mlx-lm==0.32.2 --with mlx-lm-lora==5.10.2 python dpo_native_train.py --data data_dpo_native --model <mlx-model> --beta 10 --lr 2e-5 --accum 4 --step 2048
```

**`--model` must be the model you serve.** The first DPO run trained and rendered
data on Mellum2 but was compared against a Mellum2.1 baseline. The two chat
templates differ, so that comparison is confounded (details in the research note).
Generated data and adapters are git-ignored.

## The data (committed)

- `data/train.jsonl` - 480 adherence + general examples (compacted, ≤2k tokens).
- `data/valid.jsonl` - 62 (note: shares traces with train, so its loss leaks -
  judge by the held-out set, not this).
- `data/holdout_phase4_test.jsonl` - 78 phase-4 examples, never in training.

## Small-model notes

Small models absorb **structure and style** (adherence), not new facts - so
Python 3.15 or new-API knowledge is a RAG/context job, never this tune. Keep the
general mix in to protect coherence; watch the held-out set, not train loss.
