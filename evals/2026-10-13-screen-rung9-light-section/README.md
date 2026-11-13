# Check: rung 9 with the light section alone

An exploratory check (no preregistration), read with
[the note](../../superpowers/research/2026-10-13-rung9-screen.md). Mellum Mode, guards
and facts on, rung 9 (AgentClinic phase 4), three repeats, Pi 1.1.0, oMLX 0.7.0, worker
`v0.1.8-1-gb31372b`, 2026-10-13.

Launch, from `ladder/`:

    uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 9 --repeat 3 --deadline 600 --mode-facts on --facts-section light --out ../evals/2026-10-13-screen-rung9-light-section

| repeat | result | requests | wall s (untrusted) | hidden tests | outside layout |
| --- | --- | --- | --- | --- | --- |
| 1 | FAIL | 27 | 121 | no | 0 |
| 2 | pass | 23 | 113 | yes | 0 |
| 3 | FAIL | 35 | 212 | no | 0 |

Raw traces, stdout and diffs: [`screen-rung9-light-section.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/screen-rung9-light-section.tar.gz)
(SHA-256 `501b59825e7b482aceaae8765c0ebddd2310698c557c17513b311768049bf2ff`).
