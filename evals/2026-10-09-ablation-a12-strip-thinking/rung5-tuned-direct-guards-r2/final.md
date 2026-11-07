The tests have passed successfully! Here's what was changed and the test output:

**Files changed:**
- `export.py`: Fixed the call from `column_verses` to `column_totals` and updated the totals row generation
- `totals.py`: Rewrote `column_totals` to properly handle mixed numeric and text cells, summing only numeric values
- `render.py`: Added `mark_last` parameter to optionally mark the last row as "TOTAL,"

**Test output:**
```
....                                                                     [100%]
4 passed in 0.01s
```

The export now correctly includes a totals row when requested, handles mixed data types in totals calculation, and the tests all pass.