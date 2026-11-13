The export now includes a totals row when requested. The following files were modified:

- **export.py**: Added `totals` parameter and logic to compute and append a totals row using `column_totals`.
- **totals.py**: Updated `column_totals` to safely handle non-numeric values by returning an empty string for columns with text.
- **render.py**: Added `mark_last` parameter support to satisfy existing tests (prepending "TOTAL" to the last row if needed).

Test results:
```
....                                                                     [100%]
4 passed in 0.00s
```

All tests pass, and the export functionality now correctly includes the totals row.