# Vanilla baseline — Mellum 12B BF16 (GGUF)

- **Date:** 2026-10-30
- **Server:** llama.cpp `llama-server` (build b11985), the same server the learner runs — not vLLM
- **Host:** Vast.ai A6000 48 GB, **one BF16 model at a time** (~23.7 GB each — three won't fit,
  so reps ran serial), reached over an SSH tunnel; harness driven from an Apple M3 Max
- **Model:** `JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:BF16`, `-ngl 999 -c 50000 -np 1
  --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0`
- **Arm:** `bare` — vanilla Pi + the recorder only
- **n:** 3, serial, `--deadline 1800 --stall 120`

## Results

| suite  | pass | turns (min/med/max) | out tokens (min/med/max) | wall s (min/med/max) |
|--------|------|---------------------|--------------------------|----------------------|
| easy   | 1/3  | 13 / 21 / 51        | 2.9k / 6.5k / 16.5k      | 45 / 93 / 240        |
| medium | 1/3  | 48 / 91 / 150       | 33.7k / 41.8k / 46.5k    | 425 / 733 / 954      |

(Per-rep wall is faster than the shared-GPU Q4/Q8 runs because each BF16 rep was the sole
occupant of the card — it just could not be parallelised.)

## The signal — precision does not fix the failure modes

BF16 is the highest-precision baseline and the one the ladder pins, yet its pass rate is no
better — easy 1/3 (below Q4/Q8's 2/3), medium 1/3 (below Q8's 2/3). At n=3 the per-cell count
is noise; the failure *shapes* are the same ones seen on every quant and host:

- **easy:** both fails missed the four Phase-1 home checks (html5 doctype, `lang`, nav links,
  200 + tagline) — the reproducible early-exit miss.
- **medium:** one clean pass (91 turns). One 48-turn collapse missed all 18 checks. One
  thrashed to 150 turns and missed 5 (the Phase-4 resolve/reopen contract plus spillover).

So higher precision buys nothing on the two weaknesses that matter — they are **model +
harness behaviour, to be fixed by a remedy, not by precision or a bigger box.**

Raw `trace.jsonl` / `stdout` / `workspace` stripped; each rep keeps `run.json`, `layout.json`,
`leaked.json`, `prompt.txt`.
