# 2026-10-20: ablating the v7 mediated lift on rung 9

**What is measured.** A single-variable ablation of the four changes stacked in
the [12/12 mediated win](../2026-10-20-mediated-6-9-v7/). Each arm toggles **one**
change back to its pre-win value and re-runs **rung 9** (phase 4, the historical
ceiling), n=3, direct/oMLX, mediated by the frozen `test_phase4.py`
(`--redispatch 5`). The other three settings stay at the win value.

| arm | the one change | else |
|---|---|---|
| armA-v6prompt | v6 worker prompt (`--prompt`) | win |
| armB-wholedir | `pytest tests` instead of `pytest tests/<name>` | win |
| armC-grepfind | tools `read,grep,find,ls,bash,edit,write` | win |
| armD-fixedhigh | fixed `--thinking high`, **no** `--effort-ramp` | win |

**Result (`table.md`): every arm is 3/3 on rung 9.** No change moves the pass
rate; they move cost. Arm D (fixed high budget, no ramp) passes on the **first
attempt, 0 re-dispatches, fastest (163s)**. So the crack is **the mediated
frozen test + a sufficient thinking budget**, not the prompt/command/tools or the
ramp. Reading, trade-off and scope:
[`research/2026-10-20-v7-ablation.md`](../../superpowers/research/2026-10-20-v7-ablation.md).

**Reproducibility.** The frozen acceptance tests the worker had to pass are in
[`acceptance/`](acceptance/) (the win left them in a scratch dir). Each run dir
keeps `run.json` + `final.md`; raw `trace.jsonl` / `stdout.txt` / `diff.patch`
are stripped per `AGENTS.md`. Compare mechanically with
`ladder/scripts/compare_runs.py`.
