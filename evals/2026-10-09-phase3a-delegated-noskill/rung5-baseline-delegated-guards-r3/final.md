Fixed and verified independently.

**Result:** `4 passed in 0.00s` (was 3 failed, 1 passed).

`mellum-worker` changed 3 files:
- `totals.py` — `column_totals` now returns `""` for columns containing any non-numeric cell instead of crashing.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,` when asked.
- `export.py` — `export_csv(rows, totals=False)` appends a `TOTAL,<sums>` row via `column_totals` when `totals=True`.

Both new arguments default to the previous behavior, and `test_export.py`, `exports_legacy.py`, and the lock/deps were untouched as instructed. I re-ran the suite and inspected the full diff myself before reporting.

One judgment call worth flagging: numeric *strings* (e.g. `"5"`) count as non-numeric, so that column totals to `""`. The tests don't cover that case; if you'd prefer string digits to be summed, say so and I'll adjust.