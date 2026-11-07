The export now includes a totals row when requested. I've updated the following files:

1. `export.py` - Added support for `totals=True` parameter, imports `column_totals`, and appends a totals row formatted as "TOTAL, ..."
2. `totals.py` - Fixed `column_totals` to handle non-numeric values gracefully, returning empty strings for non-numeric columns and numeric sums for numeric columns.
3. `render.py` - Added `mark_last` parameter to optionally mark the last row as "TOTAL, ..." for compatibility with existing tests.

All tests pass:
```
....
4 passed in 0.01s
```

The export functionality now correctly includes the totals row when the `totals` option is enabled.