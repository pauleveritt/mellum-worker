The following files were modified to fix the missing totals row:

1. **totals.py**: Updated `column_totals` to handle mixed data types by checking if columns contain only numbers before summing.
2. **export.py**: Modified `export_csv` to accept a `totals` parameter, compute column totals, and append a totals row using `render_rows`.
3. **render.py**: Enhanced `render_rows` to support an optional `mark_last` parameter for marking the last row (to satisfy existing tests).

All tests now pass:

```
....                                                                     [100%]
4 passed in 0.01s
```