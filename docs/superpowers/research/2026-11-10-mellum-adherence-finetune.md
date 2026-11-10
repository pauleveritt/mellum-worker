# Fine-tuning Mellum for task adherence - the learnings

## What is measured / what is conjecture

**Measured (2026-11-10, local M3 Max 48 GB):** that the model can be fine-tuned
on this Mac, what the trajectory corpus holds, and the training set we built from
it. **Conjecture:** that the tune actually improves adherence or cuts cost
without regressing the hidden pass rate. Nothing is trained for real yet. Every
number below is supply and setup, not a result.

## Why this exists

A pivot from the harness work: instead of only fixing the worker's failures in
the harness, teach the fixed model to stop making the cheap ones. The goal is to
cut cost, and the first target is the pathology Andre watched most - the small
model **not sticking to the task**. In the catalogue that is one root wearing
several faces: a dropped requirement (#3), a runaway search (#7), a skipped rule
(#16), and building in a file the spec did not name (#15, #12).

The small-model LoRA literature backs the target choice: small models absorb
**structure and style**, not new facts. Task adherence is structure - hold the
brief, act only on the named files, stop - so it is a good LoRA target. The same
rule says what NOT to tune: the migrations and visits factual gaps are a RAG or
harness job, never LoRA.

## What the feasibility probe found

- `mlx-lm` 0.32.2 has a **native `mellum` model class** (`MellumSparseMoeBlock`,
  64 experts top-8) - it loads and LoRA-trains the real 12B MoE, no patched
  build. A one-step smoke completed end to end: 4 LoRA layers, loss 2.49 -> 0.60,
  11 s, no OOM, adapter written.
- Stock mlx-lm ships **SFT LoRA / DoRA only, no DPO**. First tune is SFT; true
  preference (DPO) would need `mlx-lm-lora` or a small custom loss, later.
- Weights: train from the MLX safetensors, not the GGUF. Pulled
  `mlx-community/Mellum2-12B-A2.5B-Thinking-4bit` (6.4 GB).

## What the trajectory corpus holds

Measured over `runs/` + `evals/`:

| signal | count |
| --- | --- |
| graded runs (score + check) | 780 |
| hidden-pass | 166 |
| clean winners (hidden-pass + right files + tests intact) | 138 |
| clean winners with a trace still on disk | **44** |
| runs that wrote outside the layout | 18 (graded) / 140 (all records) |
| runs whose import broke (`checks_ran=false`) | 116 |

The final solution code is gone (winner workspaces were temp dirs), but the
**trace** survives, and for adherence the trajectory is the better signal: it is
the sequence of read-the-spec -> edit the named file -> verify -> stop. Winner
cost ran 11 to 88 requests, median 27; the cheap winners are the cleanest
demonstrations.

## The dataset we built

Pipeline (in scratch, to be promoted): `make_sft.py` + `mix_general.py`.

- **Positives:** each model response in a winner trace becomes one
  (context -> on-task action) example. The context is the exact messages the
  model saw; the action is the assistant turn it took, kept in the **native
  tool-calling format** so training matches inference (small models take the
  format literally).
- **Holdout:** phase-4 (the lost-id miss) is held out entirely - 478 examples -
  for measurement, so a gain is not memorisation.
- **Quality filtering:** every example must render through the model's chat
  template and fit the sequence budget; duplicates dropped. 1562 raw pairs, all
  passed.
- **Mixing:** blended 15% general coding-instruct (CodeAlpaca) as a regulariser
  against over-specialisation, in-domain (code) but off our eval.

Final set: **train 1134 (15.0% general), valid 141, phase-4 holdout 478.**

## The training config (small-model regime)

From the small-model LoRA guidance, to be run next:

- **DoRA**, not plain LoRA - it decomposes magnitude and direction and holds up
  better on small models.
- **All linear modules**, not just q/v (attention q/k/v/o for sure; the MoE
  expert projections if mlx-lm reaches them - to confirm).
- **Rank 32, alpha 64.**
- **Learning rate 1e-4** - the active param count is ~2.5B, so it behaves small.
- **1 to 3 epochs, eval every ~50 steps, early-stop** when val loss creeps -
  small models overfit fast.
- Track base-vs-tune with **MLflow**: hidden-pass, requests, wall, and the
  adherence verdicts (out_of_layout, checks_ran). Ship rule: cost drops AND the
  hidden pass rate does not.

## Speed track: the MTP draft head (fixed, needs llama.cpp >= b11747)

Mellum ships an MTP (multi-token-prediction) draft head for self-speculative
decoding, quoted at 1.4-1.8x with ~90% token acceptance. Measured facts:

- **The head is 308 MB** - 16 tensors (one extra decoder block `blk.28` plus the
  `nextn.eh_proj`/`enorm` projections). The shipped MTP gguf is 8.33 GB only
  because it *bundles* a full copy of the 8.07 GB trunk so it can load alone; the
  marginal head is 308 MB. Self-speculation (sharing the trunk) costs base +
  0.31 GB + KV + flash-attn ≈ ~12 GB, barely more than the base alone. Good
  economics: 308 MB for 1.4-1.8x.
- **Two things had to be right.** (1) The engine: build 11429 failed with
  `expected 355, got 339` - no code path for the `nextn` layer. The fix is
  **llama.cpp >= b11747**; we upgraded to 0.9.0 (build 12110). (2) The wiring:
  it is **self-speculation**, so serve the MTP gguf AS the main model with
  `--spec-type draft-mtp`, NOT a `-md` sidecar (the sidecar would load a second
  full trunk and does not use the nextn layers).
- **Verified:** on build 12110 the MTP gguf loads and
  `common_speculative_init_result: creating MTP draft context against the target
  model`, server healthy. Wired behind `MELLUM_DRAFT` in `scripts/backend.py`
  (off by default so measured runs stay on the simple config), test green.
- **Clean speed sweep (GPU idle): n-max 1 = 1.05x, deeper is worse.** none
  99.0 tok/s; draft n-max 1 = 104.0 (1.05x, acc 0.82, len 1.82); n-max 4 = 72.7
  (0.74x, acc 0.38); n-max 8 = 43.2 (0.44x, acc 0.19). The `nextn` head predicts
  ONE token well, so deeper drafts collapse acceptance and waste compute. On this
  M3 Max the Q4 2.5B-active target already runs ~99 tok/s (bandwidth-bound), so
  the draft overhead eats nearly all the gain: ~5% wall, nowhere near the vendor's
  1.4-1.8x (likely a CUDA/BF16 figure). Low-value for us, and it does not touch
  the request metric. (An earlier GPU-contended read showed 0.92x; contention hid
  the small real gain.)
- **Reproducibility note:** the ladder was measured on build 11669; moving to
  12110 changes the substrate, so a kept speed claim wants a re-baseline.
- **It does not help our cost metric regardless.** We score requests/turns; the
  head speeds wall only. It cannot remove a turn, so it never substitutes for the
  adherence tune.

## Factual knowledge (e.g. Python 3.15) is RAG, not this tune

New factual knowledge - a new Python version, a new library API - is the one
thing the small-model guidance says not to fine-tune: the model will hallucinate
a plausible-but-wrong answer. Split it:

- **The facts -> RAG / context injection.** Retrieve the relevant 3.15 "What's
  New" and the specific API docs a task touches into the prompt at inference.
  Reliable, updatable without a retrain. It fits the remedy architecture as a
  `context/python-315` unit, the same shape as the schema injection, and the
  Groundwire RAG in `tina4-harness` is the retrieval home.
- **The habit -> a thin style-SFT, only if wanted.** To make the model default
  to 3.15 (target the version, prefer new idioms, avoid removed ones), a small
  immaculate set of 3.15-style examples biases the default. That is style, which
  it learns; it is not teaching the semantics of every new API.
- **Keep it out of the adherence set.** Mixing 3.15 facts into the adherence
  data would fail and pollute the adherence signal. Separate track, separate
  data.

## First tune result - held-out transfer (measured)

A DoRA tune ran: all-attention keys, rank 32, lr 1e-4, 500 iters on 480 compacted
examples (15% general mix), grad-checkpoint, max-seq 2048. The leaky val curve
bottomed ~0.06-0.09 (train and valid share the same 44 traces, so it only shows
the traces were learned). The honest test is the **held-out phase-4 set** - 78
traces excluded from train and valid entirely:

| | base | tuned |
| --- | --- | --- |
| held-out phase-4 loss | 1.806 | **0.613** |
| perplexity | 6.08 | **1.85** |

Loss down ~66%, perplexity 3.3x lower on material the tune could not have
memorised. The adherence behaviour generalised. **Caveat:** this is teacher-forced
next-token loss on winner traces - a proxy. It shows the tuned model predicts
on-task winning actions far better, not yet that it passes more or spends fewer
requests. The real verdict is a harness run with the adapter (easy/hard suite,
tuned vs base, scored by the hidden grader on checks-missed and requests). A lead,
a strong one, not a rate.

## Live harness verdict (measured) - the proxy did not transfer

The held-out loss was a proxy, so we ran the real oracle. The tuned model was
converted to a servable Q4_K_M GGUF (the conversion is its own note below) and put
through the shipped harness against the base, same remedies both sides, on
llama.cpp. The result reverses the proxy:

| easy, n=6, `preset`-lean 3 prompts | passed | median requests | tool calls |
| --- | --- | --- | --- |
| base (JetBrains Q4) | **4/6** | 20 | 21, 18, 19, 32, 26, 17 |
| tuned (DoRA Q4) | **1/6** | 14 | 10, 15, 19, 9, 14, 20 |

| medium, n=1, `preset:medium` | hidden checks | requests | import ran |
| --- | --- | --- | --- |
| base | **16/18** | 79 | yes |
| tuned | **0/18** | 178 | no (broke the import) |

The tune is a broad loss, not a medium-specific one. On easy the tuned model runs
**fewer** requests and **fewer** tool calls than the base and exits with content
checks still unmet (`checks_ran` stayed true, so it is not an import break there -
it just stops short). On medium it broke the import and churned 178 requests, 2.3x
the base, before giving up. Two failure faces, one cause: the SFT taught the
**shape** of a winner trace, "stop" included, and the model now stops before the
task is actually done. The 15% general mix did not hold against 44 correlated
traces.

**The lesson about the metric.** Teacher-forced next-token loss on winner traces
rewards predicting winner-trace tokens, which correlates with terseness and an
early exit - not with capability. A 66% loss drop looked like a win and was a
regression. The hidden grader is the oracle (AGENTS.md); the proxy is not, and this
run is why. Record kept; the tune as configured does not ship.

**What this does not kill.** The pipeline, the held-out discipline, and the ability
to tune on this Mac all stand. The failure is this configuration - rank 32,
all-attention, 500 iters, 480 traces - over-specialising. Gentler settings (lower
rank, an earlier checkpoint, a heavier general mix) and a larger, less correlated
winner pool are the open corrections, each a fresh measured run, not a claim yet.

### Conversion (the serving path that unblocked the verdict)

mlx-lm's own GGUF export rejects the `mellum` type, and its server caps max_tokens
far below the profile's 16384 (pathology #9 - the agent loop dies mid-thinking at
`finish=length`). So the tuned adapter was fused and converted for the proven
llama.cpp path: `mlx_lm.fuse --dequantize` to fp16 HF, then llama.cpp's
`convert_hf_to_gguf.py`, then `llama-quantize Q4_K_M`. The converter wants
per-expert `mlp.experts.{0..63}.{proj}` while mlx-lm stores them pre-stacked as
`mlp.switch_mlp.{proj}` [64, out, in]; `remap_experts.py` slices the stack into
per-expert tensors - a pure slice, the layout already matches, no transpose. The
Q4 output is coherent (factorial correct) and tool-calls (`bash("ls")`), so the
regression above is the tune, not a broken conversion.

## What would falsify this / risks

- **44 trajectories is a narrow, correlated pool.** 1134 examples come from 44
  runs; the model may learn those runs, not the behaviour. Grow the pool by
  running the worker to mint more clean winners.
- **Training on suite traces risks memorising the suite.** Mitigation: phase-4 is
  held out, and the real test is the hard ladder the easy/medium winners never
  saw. A gain that does not transfer off the trained phases is memorisation.
- **The cost win could be the holdout, not the tune.** A fair measurement fixes
  the same deadline and scores requests, base vs tune, on held-out tasks.
- **Small-model forgetting.** The 15% mix is the guard; if general coherence
  drops, raise the mix or lower the rank.
- **Format drift.** We train in the native tool-calling template; if a later
  converter flattens tool calls to text, the gain would not reach the real
  harness.
- **SFT imitates, it does not prefer.** SFT on cheap winners teaches the short
  path by example; it cannot penalise the long one directly. DPO is the next
  tool if SFT underdelivers.
