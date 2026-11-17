# A21: the lighter `## Mellum` section and a one-file roadmap

Preregistered in [the A21 preregistration](../../superpowers/research/2026-10-13-a21-preregistration.md);
read with the [result](../../superpowers/research/2026-10-13-a21-result.md), which applies the
decision rule.

**What is measured.** Mellum Mode, guards and facts on, rungs 6–9, three repeats, Pi 1.1.0,
oMLX 0.7.0, worker `v0.1.7-5-g30d441b` (prompt v5), 2026-10-13. Every request carried
the two-bullet light section and `specs/roadmap.md`
(checked in all 12 traces).

Launch, from `ladder/`:

    uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 6 --rung 7 --rung 8 --rung 9 --repeat 3 --deadline 600 --mode-facts on --facts-section light --roadmap one-file --out ../evals/2026-10-13-ablation-a21-light-section-roadmap

| rung | repeat | result | requests | wall s (untrusted) | deadline | hidden tests | outside layout | leftovers stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 1 | pass | 24 | 86 | False | yes | 0 | 0 |
| 6 | 2 | pass | 23 | 53 | False | yes | 0 | 0 |
| 6 | 3 | pass | 17 | 67 | False | yes | 0 | 0 |
| 7 | 1 | pass | 21 | 65 | False | yes | 0 | 0 |
| 7 | 2 | pass | 27 | 134 | False | yes | 0 | 0 |
| 7 | 3 | pass | 56 | 310 | False | yes | 0 | 1 |
| 8 | 1 | pass | 65 | 297 | False | yes | 0 | 1 |
| 8 | 2 | pass | 23 | 71 | False | yes | 0 | 0 |
| 8 | 3 | pass | 15 | 60 | False | yes | 0 | 0 |
| 9 | 1 | FAIL | 19 | 104 | False | no | 0 | 0 |
| 9 | 2 | FAIL | 15 | 120 | False | no | 0 | 0 |
| 9 | 3 | FAIL | 16 | 100 | False | no | 0 | 0 |

`table.md` holds the runner's full row per run. Raw traces, stdout and diffs:
[`ablation-a21-light-section-roadmap.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/ablation-a21-light-section-roadmap.tar.gz)
(SHA-256 `dfec3ab7b89e8ead690a5799593a81eaa2a3f00f16beb192efb75f823d628890`).
