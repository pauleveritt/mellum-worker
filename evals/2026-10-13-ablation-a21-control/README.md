# A21 control: A19's AgentClinic fixture on Pi 1.1.0

Preregistered in [the A21 preregistration](../../superpowers/research/2026-10-13-a21-preregistration.md);
read with the [result](../../superpowers/research/2026-10-13-a21-result.md), which applies the
decision rule.

**What is measured.** Mellum Mode, guards and facts on, rungs 6–9, three repeats, Pi 1.1.0,
oMLX 0.7.0, worker `v0.1.7-5-g30d441b` (prompt v5), 2026-10-13. Every request carried
the fixture's three bullets, including `Write only:`
(checked in all 12 traces).

Launch, from `ladder/`:

    uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 6 --rung 7 --rung 8 --rung 9 --repeat 3 --deadline 600 --mode-facts on --out ../evals/2026-10-13-ablation-a21-control

| rung | repeat | result | requests | wall s (untrusted) | deadline | hidden tests | outside layout | leftovers stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 1 | pass | 19 | 66 | False | yes | 0 | 0 |
| 6 | 2 | FAIL | 19 | 600 | True | no | 0 | 4 |
| 6 | 3 | pass | 20 | 38 | False | yes | 0 | 0 |
| 7 | 1 | pass | 24 | 54 | False | yes | 0 | 0 |
| 7 | 2 | pass | 25 | 72 | False | yes | 0 | 0 |
| 7 | 3 | pass | 18 | 64 | False | yes | 0 | 0 |
| 8 | 1 | FAIL | 110 | 600 | True | yes | 0 | 2 |
| 8 | 2 | pass | 28 | 134 | False | yes | 0 | 1 |
| 8 | 3 | pass | 62 | 342 | False | yes | 0 | 1 |
| 9 | 1 | FAIL | 22 | 127 | False | no | 0 | 0 |
| 9 | 2 | pass | 28 | 185 | False | yes | 0 | 0 |
| 9 | 3 | pass | 19 | 105 | False | yes | 0 | 0 |

`table.md` holds the runner's full row per run. Raw traces, stdout and diffs:
[`ablation-a21-control.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/ablation-a21-control.tar.gz)
(SHA-256 `a73cd5f77905af04b68d8016fc5986f7fefcdbbbf3e2485632c7b3e709c97e41`).
