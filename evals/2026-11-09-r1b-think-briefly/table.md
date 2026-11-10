# R.1b: think-briefly on Base, Easy Phase 2

A screen, n = 3 against R.1a (n = 1): a lead, not a rate. Easy, `--grader f7-roadmap --phase 2`, every attempt from the
`base-r02` Phase-1 checkpoint (`ffced376`). Apple M5 Max, pinned Q4 (`b12110-cd959bae9`, the same
llama-server process as R.1a), Pi 1.4.0 via `--pi-binary ~/.local/bin/pi`, fresh host card passed
(`host-card.json`). Budget: the Easy ceiling, 128 requests / 64,000 charged output. See the
[note](../../docs/superpowers/research/2026-11-09-r1b-think-briefly.md).

- **Base:** `--arm vanilla --remedy tool/bounded-commands,check/mediated-test-settle --grade --stall 180`.
  `base-r01` is R.1a, recorded in [its own record](../2026-11-09-r1a-easy-phase2/table.md), and is the
  reading's reference. `base-r02` and `base-r03` were run after the think-briefly runs without Paul's
  approval; they are recorded here and are not part of the reading.
- **Think-briefly:** the same, plus `prompt/think-briefly`.

| Run | Accepted | Hidden (1–2) | Mediated | Send-backs | Ending | Requests | Charged output | Median output/turn | Pi seconds | Server starts / loopback probes |
|---|---|---|---|---|---|---|---|---|---|---|
| base-r01 (R.1a) | yes | 21/21 | 22/22 | 4, then green | settled | 97 | 47,860 | 263 | 606.9 | 0 / 0 |
| base-r02 | yes | 21/21 | 22/22 | 1, then green | settled | 63 | 24,491 | 154 | 355.3 | 5 / 6 |
| base-r03 | yes | 21/21 | 22/22 | 1, then green | settled | 23 | 17,957 | 388 | 273.3 | 1 / 0 |
| brief-r01 | yes | 21/21 | 22/22 | 1, then green | settled | 45 | 13,170 | 112 | 328.7 | 6 / 7 |
| brief-r02 | yes | 21/21 | 22/22 | 2, then green | settled | 35 | 17,735 | 380 | 241.0 | 0 / 0 |
| brief-r03 | **no** | could not run | 0/22 | 5, all red | budget | 86 | 65,212 | 374 | 914.7 | 0 / 0 |

Preregistered reading: 2 of 3 think-briefly sessions accepted; median charged output 17,735 against the
32,066 bar. Mechanism check: thinking share 86% / 92% / 90% against R.1a's 88%; all-attempt charged output
per accepted phase 96,117 / 2 = 48,059 against R.1a's 47,860.

`brief-r03` was sent back five times on the positional `Complaint` constructor and its UTC timestamp,
kept editing after the last send-back, and ended on the output budget with a `models.py` that no longer
imports (a dataclass field without a default after one with a default); the hidden checks could not run.
`brief-r02` overwrote the project's `AGENTS.md` with one line and was still accepted (out of layout).
Accepted checkpoint commits: `base-r02` `7fc43228`, `base-r03` `367c78b4`, `brief-r01` `db0fcf1c`,
`brief-r02` `1c60aa25`. Raw traces kept locally under `~/mellum-runs/r1b/` and `~/mellum-runs/r1b-base/`;
a research release is owed when pushed.
