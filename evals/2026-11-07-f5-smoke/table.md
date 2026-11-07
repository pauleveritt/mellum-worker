# F.5 smoke — host card and the session budget, 2026-11-07

Easy (single-source suite, 13 current checks), `--arm vanilla`, llama.cpp b12110 (`cd959bae9`,
Homebrew 0.9.0) serving `Mellum2.1-12B-A2.5B-Thinking` Q4_K_M on :8001, Apple M5 Max (128 GiB),
Pi 1.4.0 (`--pi-binary ~/.local/bin/pi`), thinking on, `--grade --stall 180`, runs outside the
repository (`~/mellum-runs/2026-11-07-f5-smoke`), the follower on screen. n = 1 per row: this checks
that the record carries the new fields and that each ending happens on the real path. It is not a
rate. Raw traces are not committed.

## Host card

[`host-card.json`](host-card.json): **passed**, in 180 s. Identity (build, weights sha256, every
pinned flag, two slots of 50,176); capacity 42,658 prompt tokens per slot; protocol (tool call,
reasoning split, `max_tokens` honoured); stability 10/10; throughput 341 prompt and 153 generated
tokens per second; numerics Metal 16.0085 against CPU 15.9176 (0.57%, tolerance 1%); tooling Pi
1.4.0, node 25.8.1, uv 0.11.6. The committed copy's `machine` field is redacted from the network
name to `Apple M5 Max, 128 GiB` (fixed in `bb2a9c6`); the runs' `host_card.sha256` is the
original's.

## Sessions

| Run | Counted | Completion | Censored | Requests (proxy / trace) | Output tokens (proxy / trace) | Wall (s) | Hidden missing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `vanilla-r1` | yes | settled | no | 23 / 23 | 6,369 / 6,369 | 55.4 | 2 of 13 |
| `vanilla-r2` | yes | settled | no | 18 / 18 | 7,860 / 7,860 | 81.0 | 1 of 13 |
| `vanilla-r3` | yes | stalled | no | 22 / 22 | 6,557 / 6,557 | 251.5 | 2 of 13 |
| `budget-5` | no | budget | no | 5 / 6 | 1,420 / 1,420 | 11.0 | did not run (13 of 13) |

- **The proxy and the recorder agree** on every counted session, request for request and token for
  token. In `budget-5` the trace has a sixth request, the one the proxy refused with 429; the
  proxy logged `budget_exhausted` once and the harness ended Pi (`exit_code: -9`, cleanup clean).
- **Easy's 64 / 32,000 did not bind** any counted session (most: 23 requests, 7,860 tokens).
- **`vanilla-r3` stalled** on a foreground `uv run python -m uvicorn app:app --port 8000 --reload`
  held open 180 s. The port-8000 guard checks before a session, not during one, so this is the
  known foreground-server stall, not a leftover.
- **Missing checks:** all three miss `test_extending_page_can_override_layout_title`; r1 and r3
  also miss `test_main_guard_launches_uvicorn_with_reload_and_keeps_serving`. These are model
  habits on the repaired oracle, for R.1 to measure, not harness faults.
