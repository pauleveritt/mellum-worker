The following files were edited to fix the missing totals row in exports and resolve related test failures:

- export.py: Modified `export_csv` to support a `totals` parameter, compute column totals using `column_totals`, and append a totals row when requested.
- totals.py: Updated `column_totals` to handle mixed numeric and non-numeric values gracefully, returning empty strings for columns without numeric data.
- render.py: Enhanced `render_rows` to support a `mark_last` parameter for marking the last row as total (used in tests).

Test run result:
```
....                                                                     [100%]
4 passed in 0.00s
```

All tests now pass, confirming the export functionality includes the totals row when requested.