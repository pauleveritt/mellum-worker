Done. `mellum-worker` fixed the implementation and I independently verified.

**Result:** `4 passed in 0.00s` (was 3 failed, 1 passed).

**Changes (implementation only; tests untouched):**
- `render.py` — `render_rows(rows, mark_last=False)`; when `mark_last=True`, prefixes the last rendered row with `TOTAL,`.
- `totals.py` — `column_totals` now sums only numeric cells per column (ignoring text/bool and missing columns) and returns `""` for all-text columns.
- `export.py` — `export_csv(rows, totals=False)`; when `totals=True`, appends a `TOTAL,<col totals>` line.

**Verification:** I reran `.venv/bin/python -m pytest -q` myself and inspected `git diff` — all four tests pass and only the three implementation modules changed.