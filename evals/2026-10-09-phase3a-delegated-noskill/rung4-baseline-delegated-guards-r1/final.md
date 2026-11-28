Done. Delegated to `mellum-worker` (single writer, no worktree) and independently verified.

**Result:** `4 passed in 0.00s` (ran `.venv/bin/python -m pytest -q` myself).

**Changes made by the worker:**
- `totals.py` — `column_totals` now sums only numeric cells per column (including mixed columns like `["a", 1]`), returns `""` for all-text columns.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL`.
- `export.py` — `export_csv(rows, totals=False)` appends a `TOTAL,<col totals>` row, importing `column_totals`.

Existing default behavior is preserved (`test_export_without_totals` still passes), and `test_export.py` was not modified.