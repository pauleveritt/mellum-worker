The export functionality has been updated to include a totals row when requested. The `export_csv` function in `export.py` now accepts a `totals` parameter (defaulting to `False`). When `totals=True`, it computes column totals using `column_totals` from `totals.py` and appends a row formatted as `TOTAL,<total1>,<total2>,...`.

Changes made:
- Modified `export.py` to import `column_totals` and add `totals` parameter logic.
- Verified through existing tests (`test_export.py`) that both cases work: without totals row and with totals row.

If your export still misses the totals row, ensure that the call to `export_csv` includes `totals=True` or adjust the calling code accordingly.