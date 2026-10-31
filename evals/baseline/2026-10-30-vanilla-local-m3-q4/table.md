# Vanilla baseline — Mellum 12B Q4_K_M on a LOCAL Mac (llama-server, Metal)

- **Date:** 2026-10-30
- **Server:** llama.cpp `llama-server` (brew, build 11429) on an **Apple M3 Max, 48 GiB**, Metal
  — the same server and flags as the Vast rig, run locally this time
- **Model:** cached `JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M`, `-ngl 999 -c 50000
  -np 1 --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0`
- **Arm:** `bare` — vanilla Pi + the recorder only
- **n:** 3, serial (one Metal device), `--deadline 1800 --stall 120`

## Results

| suite  | pass | turns (min/med/max) | out tokens (min/med/max) | wall s (min/med/max) |
|--------|------|---------------------|--------------------------|----------------------|
| easy   | 1/3  | 16 / 17 / 23        | 5.1k / 6.9k / 8.4k       | 47 / 63 / 76         |
| medium | 2/3  | 45 / 71 / 103       | 27.6k / 40.5k / 58.4k    | 303 / 522 / 899      |

(both suites ran serial — one Metal device.)

## The signal — local vs cloud, same model/server/quant

Local M3 Max is **fast**: 47–76 s per easy rep (serial, sole occupant of the GPU), versus
the Vast A6000's 114–293 s on easy (where three ran in parallel and shared the card). So the
Mac is perfectly capable for one session at a time — it was only "too slow" for running the
whole matrix three-wide at once.

Pass rate (1/3) sits below cloud Q4's 2/3, but at n=3 that is noise around the **same two
failure modes seen on every host and quant**:

- one fail got the tests green but tripped the **quality gate** (`tests_passed=true,
  quality_ok=false` — ruff / pyrefly / complexipy),
- one fail missed the four **Phase-1 home checks** (html5 doctype, `lang`, nav links,
  200 + tagline) — the reproducible early-exit miss.

On **medium** the Mac held up well — 2/3, matching the Q8 A6000 and beating cloud Q4's 1/3.
Two clean passes (71 and 103 turns, tests + quality green) and one 45-turn collapse that
missed all 18 checks — the same early-give-up shape, not a hardware limit.

The takeaway: the vanilla worker's weaknesses are **model + harness behaviour, not the
hardware or the quant**. A remedy, not a faster box or higher precision, is what should fix
them. Raw `trace.jsonl` / `stdout` / `workspace` stripped; each rep keeps `run.json`,
`layout.json`, `leaked.json`, `prompt.txt`.
