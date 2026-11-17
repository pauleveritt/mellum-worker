I've fixed the export functionality to include a totals row. The changes involve:

1. **export.py**: Modified to compute column totals using `column_totals` and append a "TOTAL" row when the `totals` flag is set.
2. **totals.py**: Updated `column_totals` to ignore non-numeric cells and handle mixed data types correctly.
3. **render.py**: Enhanced to support marking the last row as total (for internal tests).

All tests now pass verify the fixes.

The export should now include the totals row when invoked with the appropriate parameters.