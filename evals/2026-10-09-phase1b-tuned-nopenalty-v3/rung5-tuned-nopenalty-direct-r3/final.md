The following files were edited to fix the missing totals row in exports and resolve related test failures:

1. **export.py** - Added `totals` parameter, imported `column_totals`, and logic to append a totals row when `totals=True`.
2. **render.py** - Modified `render_rows` to support `mark_last` parameter for marking the last row as total (needed for existing tests).
3. **totals.py** - Updated `column_totals` to handle non-numeric values by returning empty strings for non-numeric columns.

Test output after changes:
```
....                                                                     [100%]
4 passed in 0.01s
```

All tests now pass, and the export functionality includes the totals row when requested.