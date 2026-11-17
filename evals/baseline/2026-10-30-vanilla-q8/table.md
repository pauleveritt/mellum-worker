# Vanilla baseline — Mellum 12B Q8_0 (GGUF)

- **Date:** 2026-10-30
- **Server:** llama.cpp `llama-server` (build b11985), the same server the learner runs — not vLLM
- **Host:** Vast.ai A6000 48 GB (3× servers, one rep per server, true parallel; ~39 GB VRAM for 3× Q8 + KV), reached over an SSH tunnel; harness driven from an Apple M3 Max
- **Model:** `JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q8_0`, `-ngl 999 -c 50000 -np 1 --jinja -fa auto -b 512 -ub 512 -ctk q8_0 -ctv q8_0`
- **Arm:** `bare` — vanilla Pi + the recorder only, no remedies
- **n:** 3, `--deadline 1800 --stall 120`

## Results

| suite  | pass | turns (min/med/max) | out tokens (min/med/max) | wall s (min/med/max) |
|--------|------|---------------------|--------------------------|----------------------|
| easy   | 2/3  | 19 / 26 / 33        | 5.8k / 6.4k / 18.9k      | 114 / 122 / 293      |
| medium | 2/3  | 85 / 105 / 111      | 35.0k / 41.1k / 42.6k    | 1411 / 1558 / 1662   |

(medium ran one rep per server, parallel on 3× Q8; easy the same.)

## The signal

**easy:** same pass rate as Q4 easy (2/3), and the **same failure shape** — the one fail
missed the four Phase-1 home checks (html5 doctype, `lang`, nav links, 200 + tagline) with
`tests_passed=false, quality_ok=false`. The two passes are tighter than Q4's — 19 and 26
turns at ~6k output tokens, versus Q4's 20 and 58.

**medium:** 2/3, better than Q4 medium's 1/3. Two clean passes (tests + quality green). The
one fail got Phase 1–3 right but missed the **Phase-4 resolve/reopen** route contract
(`test_resolve_route_marks_complaint_resolved_and_redirects`,
`test_reopen_route_marks_complaint_open_and_redirects`) — tests fail, quality still green.

So Q8 buys cleaner successful runs and a better medium pass rate than Q4, but does not fix
the reproducible early-exit miss on the home phase, and Phase 4 stays the hardest rung.

Raw `trace.jsonl`, `stdout` and `workspace` are stripped; each rep keeps `run.json`,
`layout.json`, `leaked.json` and `prompt.txt`.
