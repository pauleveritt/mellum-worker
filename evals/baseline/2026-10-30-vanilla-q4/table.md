# Vanilla baseline — Mellum 12B Q4_K_M (GGUF)

- **Date:** 2026-10-30
- **Server:** llama.cpp `llama-server` (build b11985), the same server the learner runs — not vLLM
- **Host:** Vast.ai A6000 48 GB (3× servers, one rep per server, true parallel), reached over an SSH tunnel; harness driven from an Apple M3 Max
- **Model:** `JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M`, `-ngl 999 -c 50000 -np 1 --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0`
- **Arm:** `bare` — vanilla Pi + the recorder only, no remedies
- **n:** 3 per suite, `--deadline 1800 --stall 120`

## Results

| suite  | pass | turns (min/med/max) | out tokens (min/med/max) | wall s (min/med/max) |
|--------|------|---------------------|--------------------------|----------------------|
| easy   | 2/3  | 20 / 29 / 58        | 7.8k / 14.2k / 17.6k     | 175 / 340 / 352      |
| medium | 1/3  | 68 / 84 / 163       | 31.1k / 40.9k / 50.7k    | 731 / 880 / 1284     |

## How the failures fail (the signal)

- **easy (Bronze):** the one fail self-exited after 7–29 turns declaring "all files are in
  place", while missing the four Phase-1 home checks (html5 doctype, `lang`, nav links,
  200 + tagline). The server answered fine; the model gave up early.
- **medium (Silver):** one clean pass (84 turns). One rep got every hidden test green
  (`tests_passed`) but failed the **quality gate** (`quality_ok=false` — ruff / pyrefly /
  complexipy). One collapsed — 163 turns, 64 tool errors, 7 compactions, missed all 18 checks.

Raw `trace.jsonl`, `stdout` and `workspace` are stripped per the recording rules; each rep
keeps its `run.json`, `layout.json`, `leaked.json` and `prompt.txt`.
