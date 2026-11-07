# F.3 smoke — the honest budget fields, 2026-11-07

Easy (single-source suite), `--arm vanilla`, llama.cpp `Mellum2.1-12B-A2.5B-Thinking` (Q4_K_M)
on an Apple M5 Max (128 GiB), Pi 1.4.0 (`--pi-binary ~/.local/bin/pi`), thinking on
(`enable_thinking: true` in the payload), `--grade`. n = 1 per row. This smoke checks that the
record carries the new fields. It is not a rate. Raw traces are not committed.

| Run | Deadline | Completion | Wall (s) | Turns | Requests | Context | Output tok | Hidden | Health |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vanilla-r1` | 600 | settled | 48.6 | 18 | 18 | 11,438 | 6,982 | 4/4 | pass |
| `vanilla-r2` | 90 | settled | 41.4 | 20 | 20 | 11,162 | 5,581 | 4/4 | pass |
| `vanilla-r3` | 20 | deadline | 20.0 | 7 | 8 | 6,613 | 2,966 | did not run (no `app.py`) | pass |

- **r3 is the deadline case.** `execution.json` says `termination_reason: deadline` and
  `exit_code: -9`. `wall` equals the deadline. Turns are 7 of 8 requests, because the eighth was
  in flight when the deadline killed Pi.
- **r2 meant to hit 90 s and did not.** Both full sessions settled in under 50 s, which is why
  r3 exists.
- **Context** here is from the corrected `report` (the uncached input plus cache reads). The
  `run.json` files were written before that fix and carry 1,703, which is the largest
  *uncached* input. That gap is why the fix exists.
- `cleanup_ok: true` and `leaked: []` in all three. No server was left running.
