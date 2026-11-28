Verified independently — `4 passed`, and the diff is minimal.

## Result

Delegated to `mellum-worker` and verified myself. All 4 tests in `test_export.py` now pass.

**Run history:**
- First run (`c2d802d8`) stalled with an empty response after fixing only `totals.py` (2/4 passing).
- Per resume-first guidance I revived the same child (`25a0c8a0`) instead of launching a replacement; it completed the remaining files.

**Changes (all worker-authored, none by me):**
- `totals.py` — `column_totals` now sums numeric columns and returns `""` for columns containing any non-numeric cell.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,` when requested.
- `export.py` — `export_csv(rows, totals=False)` appends a `TOTAL` row built from `column_totals` when requested.
- `test_export.py` untouched; no commits made.

**Independent verification:**
```
....                                                                     [100%]
4 passed in 0.00s
```