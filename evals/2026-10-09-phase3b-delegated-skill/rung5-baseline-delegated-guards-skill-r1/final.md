Done. The mellum-worker made the change; I verified by running the tests myself.

**Files changed (by mellum-worker):**
- `totals.py` — `column_totals` now sums numeric cells per column, returning `""` for all-non-numeric columns.
- `render.py` — `render_rows(rows, mark_last=False)` gained `mark_last`, prefixing the last row with `TOTAL,`.
- `export.py` — `export_csv(rows, totals=False)` gained `totals`; when true it appends `column_totals(rows)` and renders with `mark_last=True`.

**Unchanged as required:** `test_export.py`, `exports_legacy.py`.

**Test output (I ran it, verbatim):**
```
....                                                                     [100%]
4 passed in 0.00s
```

All four tests pass, including `test_export_appends_totals_row` (`"1,2\n3,4\nTOTAL,4,6"`), `test_render_marks_last_row_as_total`, and `test_column_totals_ignores_text_cells`. The diff is minimal and confined to the three named files.