# Full spec flow on vLLM, rerun with the gate fixes, 2026-10-29

The same flow as [the first run](../2026-10-29-vllm-flow/README.md), at commit
`6985a6e` (the revert keeps frozen gates; a gate's `TestClient` never follows
redirects), with the three levels run **at once** as three `flow_run.py`
processes on one vLLM (vast.ai instance 58204861). From 06:46 UTC the host
was also serving the lesson check, so wall times are not comparable. n = 1 per
level. Reading: `docs/superpowers/research/2026-10-29-vllm-flow.md`.

| Level | Suite | Phases | Hidden checks | Full pass | Wall |
| --- | --- | --- | --- | --- | --- |
| Bronze | `easy` | 1 | 4/4 | yes | 7 min |
| Silver | `medium` | 4 | 18/18 | yes | 41 min |
| Gold | `hard` | 7 | 30/34 | no | 204 min |

Layout per level as in the first run's README: `result.json`, `missed.json`,
`progress.txt`, `gate/`, `final/`, `plan/`, `commits.txt`. Raw traces,
sub-agent feeds and workspaces are not in git.
