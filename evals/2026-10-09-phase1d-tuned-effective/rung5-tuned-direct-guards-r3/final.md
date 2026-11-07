Files changed:
- export.py: Added totals parameter and logic to append totals row using column_totals
- totals.py: Fixed column_totals to handle mixed numeric and non-numeric values
- render.py: Modified render_rows to support mark_last parameter by prepending "TOTAL" to the last row

Test output:
```
....                                                                     [100%]
4 passed in 0.01s
```