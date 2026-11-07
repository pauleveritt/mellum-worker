Tests passed! Here are the changes and test output:

Files changed:
- render.py: Added `mark_last` parameter to `render_rows` function to support marking the last row as total
- export.py: Added `totals` parameter and logic to append totals row using `column_totals`
- totals.py: Already updated earlier to handle mixed numeric/text cells

Test output:
```
....                                                                     [100%]
4 passed in 0.00s
```