Done. `mellum-worker` fixed it, and I verified independently.

**Result: 4 passed** (was 3 failed, 1 passed).

Files changed (test file untouched):
- `totals.py` — `column_totals` now skips non-numeric cells per column; returns `""` for columns with no numeric values.
- `render.py` — `render_rows(rows, mark_last=False)`; when set, the last row's first cell becomes literal `TOTAL`.
- `export.py` — `export_csv(rows, totals=False)`; when set, appends a `TOTAL,<col totals>` row via `column_totals`.

Verified each target assertion directly:
- `export_csv([[1,2],[3,4]])` → `'1,2\n3,4'` (backward compatible)
- `column_totals([['a',1],['b',2]])` → `['', 3]`
- `render_rows([[1,2],[3,4]], mark_last=True)` → `['1,2','TOTAL,3,4']`
- `export_csv([[1,2],[3,4]], totals=True)` → `'1,2\n3,4\nTOTAL,4,6'`