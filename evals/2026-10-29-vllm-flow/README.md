# Full spec flow on vLLM, 2026-10-29

`learn/code/flow_run.py` (forced mode, 6 rounds of 900 s per phase, one
attempt per round) driving Mellum 2.1 BF16 on vLLM 0.32.0 on one RTX A6000
(vast.ai instance 58157720), with Pi 1.3.0 on an Apple M3 client over an SSH
tunnel: the same pins as the
[vLLM baseline](../2026-10-28-vllm-baseline/README.md). One run per level
(n = 1), commit `fdcab52`. Reading:
`docs/superpowers/research/2026-10-29-vllm-flow.md`.

| Level | Suite | Phases | Hidden checks | Full pass | Wall |
| --- | --- | --- | --- | --- | --- |
| Bronze | `easy` | 1 | 4/4 | yes | 75 min |
| Silver | `medium` | 4 | 13/18 | no | 96 min |
| Gold | `hard` | 7 | 30/34 | no | 184 min |

Per level (one directory each):

- `result.json`: what `flow_run.py` wrote; `missed.json`: the hidden checks
  that failed, from re-grading the final workspace.
- `progress.txt`: the phase banners and round outcomes from the console.
- `gate/`: the frozen gate per phase as it stood at the end. Silver's
  `phase_4.py` is the gate re-frozen after a revert, not the one that failed
  rounds 1 to 5; that one survives only in the raw traces.
- `final/`: the app source at the end; `plan/`: `TODO.md` and `REVIEW.md`;
  `commits.txt`: the workspace's checkpoint commits.

Raw traces, sub-agent feeds and workspaces are not in git.
