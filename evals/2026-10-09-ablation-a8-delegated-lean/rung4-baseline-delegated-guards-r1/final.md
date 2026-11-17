Done. Delegated to `mellum-worker`; verified independently.

**What happened**
- First run ended prematurely (empty final message) after fixing only `totals.py` — captured the partial diff, then did a same-protocol retry.
- Retry completed the remaining edits.

**Files changed**
- `totals.py` — `column_totals` now skips non-numeric cells and emits `""` for text-only columns.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,`.
- `export.py` — `export_csv(rows, totals=False)` appends a `column_totals` row and marks it when `totals=True`.
- `test_export.py` untouched.

**Verification** (run by me, not just the subagent)
```
uv run pytest -q
....                                                                     [100%]
4 passed in 0.01s
```

Note: the first subagent run was a lane failure (model produced no output), not a code problem; the retry succeeded.