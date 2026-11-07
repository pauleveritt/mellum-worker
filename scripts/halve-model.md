# Halving a model — how far does a cheaper worker hold up?

`scripts/halve-model.sh` re-quantizes an MLX model to a lower bit depth, so you
can measure a smaller, faster worker on the ladder against the one that ships.
"Halving" a 6-bit model means **3-bit** — half the bits per weight; **4-bit** is
the gentler step.

## Run it

```bash
# 3-bit (literal half of 6-bit) → .models/Mellum2.1-...-3bit
scripts/halve-model.sh .models/Mellum2.1-12B-A2.5B-Thinking-6bit 3

# 4-bit, custom group size
scripts/halve-model.sh .models/Mellum2.1-12B-A2.5B-Thinking-6bit 4 32
```

Needs `uv` only — `mlx-lm` is pulled into an ephemeral env, nothing installed
globally. A 12B model takes a while and, when the source is already quantized,
a temporary fp16 copy (~24 GB) before it is removed.

## The honesty caveat

Re-quantizing an already-quantized model is **lossy-on-lossy**: a drop you see
may be the double-quant, not the smaller size. The script dequantizes to fp16
first (the least-bad path) but this is still not a clean single quantization.
For a fair "halved" comparison, convert from the original fp16/bf16 weights.
**Any ladder run that uses a re-quantized model must say so in its record.**

## Measure it

1. **Serve it.** oMLX serves every model under its `--model-dir` (`.models/`),
   so the new dir is picked up (restart oMLX if it does not appear in
   `GET /v1/models`).
2. **Run the mediated rung** against it in direct mode — the frozen complete
   test is the lever, so this is the fair test of the smaller worker:
   ```bash
   cd ladder && uv run python -m ladder.run_ladder \
     --mode direct --profile tuned --rung 9 --repeat 3 \
     --acceptance-test <path>/test_phase4.py --redispatch 5 --effort-ramp \
     --model omlx/<the-halved-model-id> \
     --out ../evals/<date>-halved-rung9
   ```
   (`--model` sets the provider and the id the request carries, so it matches
   what oMLX serves.) Watch it live with `python scripts/watch_ladder.py`.
3. **Compare** 6-bit against the halved run mechanically:
   ```bash
   uv run python scripts/compare_runs.py <6bit-record> <halved-record>
   ```

A halved worker that still passes rung 9 is headroom — cheaper and faster for
free. A drop on rung 9 (the hardest rung) says the bits were load-bearing.
