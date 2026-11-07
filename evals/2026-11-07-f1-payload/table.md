# F.1 payload check — 2026-11-07

Easy, llama.cpp `Mellum2.1-12B-A2.5B-Thinking` (Q4_K_M) on an Apple M5 Max, deadline 900 s,
n = 1 per arm, with the worker that loads no delegate tool. Read from every recorded
`provider_request` payload in each session's `trace.jsonl` (raw trace not committed).

| Arm | Requests | Tools sent | `delegate` tool | Nudged requests | Passed | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `worker` | 36 | bash, edit, read, write | absent | 0 | no | hung on a foreground `uvicorn --reload` until the deadline |
| `bare` | 18 | bash, edit, read, write | absent | 0 | yes | left `python app.py` running (swept, `leaked`) |

Rule (preregistered in the [spec](../../docs/superpowers/specs/2026-11-07-worker-without-delegate-design.md)):
no payload lists `delegate` or carries the nudge, in both arms. **Met.** A presence/absence reading
at n = 1; the pass column is not a rate.
