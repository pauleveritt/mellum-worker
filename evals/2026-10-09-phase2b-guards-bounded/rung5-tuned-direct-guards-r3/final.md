The export now includes a totals row when requested, and all tests pass.

**Files changed:**
- `export.py`: Added `totals` parameter and logic to append a totals row computed by `column_totals`.
- `totals.py`: Rewritten `column_totals` to handle numeric and non-numeric values gracefully.
- `render.py`: Updated `render_rows` to support `mark_last` parameter for marking the last row as total (prepends "TOTAL,").

**Test output:**
```
....                                                                     [100%]
4 passed in 0.00s
```

The issue "the export is missing the totals row" has been resolved.