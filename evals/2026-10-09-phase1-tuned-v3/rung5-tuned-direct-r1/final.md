Changed files:
- export.py: Added totals parameter and logic to append totals row using column_totals
- totals.py: Fixed column_totals to handle non-numeric values gracefully
- render.py: Updated render_rows to support mark_last parameter for test compatibility

Test output:
```
....                                                                     [100%]
4 passed in 0.01s
```

The export now includes the totals row when requested.