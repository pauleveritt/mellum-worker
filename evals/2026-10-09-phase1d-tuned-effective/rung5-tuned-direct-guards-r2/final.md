Changes made:

1. **export.py**: Modified to support `totals` parameter, compute column totals using `column_totals`, and append a totals row when `totals=True`.
2. **totals.py**: Updated `column_totals` to handle mixed data types by checking if column values are all numbers before summing, otherwise returns empty string.
3. **render.py**: Updated `render_rows` to support `mark_last` parameter, inserting "TOTAL" at the start of the last row when `mark_last=True`.

Test output:
```
....                                                                     [100%]
4 passed in 0.01s
```

The export now includes the totals row when requested, and all tests pass.