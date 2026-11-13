The following files were edited to fix the failing tests:

- totals.py: Fixed column_totals to handle non-numeric cells by returning "" for columns with text and summing numeric cells.
- render.py: Modified render_rows to support mark_last=True by prepending "TOTAL," to the last row instead of replacing the first column.
- export.py: Updated export_csv to accept a totals=False parameter, compute totals row using column_totals, and append a formatted totals row when totals=True.

Test output after changes:

```
....                                                                     [100%]
4 passed in 0.01s
```

All tests now pass.