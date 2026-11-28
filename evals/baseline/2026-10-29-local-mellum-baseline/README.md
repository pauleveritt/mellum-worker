# Local MLX 6-bit screen, 2026-10-29

Vanilla Pi (no extensions, skills, prompt templates or context files; the
recorder only) driving Mellum 2.1 **6-bit** on **oMLX 0.7.1rc1**, served at
`http://127.0.0.1:8001/v1` on one Apple M3 Max, with Pi 1.3.0 as the client.
Pins: `scripts/baseline/pins.env`; recipe: `scripts/baseline/README.md`;
reading: `docs/superpowers/research/2026-10-29-local-mellum-baseline.md`.

**This is a local MLX screen, not the pinned vLLM baseline.** The serving
stack (oMLX/MLX) and the weight precision (6-bit) both differ from the pinned
record, which runs Mellum 2.1 BF16 on vLLM 0.32.0 on a rented RTX A6000
(`evals/baseline/2026-10-28-vllm-baseline`). Read it as a quant-vs-full lead on
the same vanilla Pi, not as a second baseline.

- `manifest.json`: the commit, the knobs, the oMLX server and model read live,
  the host and client. It records one divergence from the pins — Node v26.9.0
  here against the pinned 22.19.0, because this run used the system `pi`, not
  the pinned toolchain. Pi itself (1.3.0) matches.
- `ladder/`: rungs 1–12, n = 3, `--mode primary --plain`, 600 s deadline:
  `table.md` and each run's `run.json` and `final.md`.

Raw traces, stdout and diffs are not in git.

## Result — 6-bit vs BF16, AgentClinic rungs 1–12, n = 3

| Rung | Local 6-bit (MLX) | BF16 (vLLM) | Δ |
|-----:|:-----------------:|:-----------:|:-:|
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

The 6-bit quant costs 5 passes against the pinned BF16. The loss is
concentrated on rungs 2, 4, 5, 7 and 9 (one pass each); the other seven rungs
match exactly, including the shared rung-6 wall (0/3 both). No rung where the
quant beats BF16.
