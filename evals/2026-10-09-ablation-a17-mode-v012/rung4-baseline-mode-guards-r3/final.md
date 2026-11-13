Successfully made the tests pass.

Files changed:
- render.py: Added `mark_last` parameter to `render_rows` function to support marking the last row as total when `mark_last=True`.
- export.py: Added `totals` parameter to `export_csv` function to support appending a totals row when `totals=True`.

Test output:
```
....                                                                     [100%]
4 passed in 0.00s
```