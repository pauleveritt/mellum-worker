The following files were edited to fix the missing totals row in export:

1. `totals.py` - Updated `column_totals` to handle mixed numeric and non-numeric values correctly.
2. `render.py` - Modified `render_rows` to support `mark_last` parameter for marking the last row as total.
3. `export.py` - Updated `export_csv` to support `totals` parameter and append a totals row when requested.

Test output:
```
....
4 passed in 0.00s
```

All tests now pass, meaning the export functionality includes the totals row when requested, and the totals row is calculated correctly.