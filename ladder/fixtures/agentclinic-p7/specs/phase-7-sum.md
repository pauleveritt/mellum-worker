# Phase 7 — Sum two columns from a large file

`numbers.txt` sits beside the app: many rows, each `a b` — two non-negative
integers separated by a space. Build an endpoint that returns the column sums.
Write only `app.py`, `models.py`, `templates/`, `tests/`. Standard library only.

## /sum
`GET /sum` returns JSON `{"col1": <sum of the first column>, "col2": <sum of the
second column>}`, summed over **every** row of `numbers.txt`.

Pitfall: `numbers.txt` is far larger than fits in a prompt, or in memory as one
string. Read it **a line at a time** (stream it); do not load the whole file into
context. The sums must cover all rows — a sample or a truncated read gives the
wrong answer.
