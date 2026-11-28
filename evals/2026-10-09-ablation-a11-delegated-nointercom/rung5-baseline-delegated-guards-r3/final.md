Verified independently — the worker's claim holds.

**Evidence:**
- `.venv/bin/python -m pytest -q` → `4 passed in 0.00s`
- Diff confined to the three authorized files; `test_export.py` and `exports_legacy.py` unchanged.

**Change summary:**
- `totals.py` — `column_totals` now checks each column is all-numeric; returns the sum, or `""` for columns containing non-numeric cells (fixes the `TypeError`).
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,` when `mark_last=True`.
- `export.py` — `export_csv(rows, totals=False)` appends the computed `TOTAL` row when `totals=True`.

The totals row now appears in the export. Changes are left uncommitted — say the word if you'd like me to commit them.