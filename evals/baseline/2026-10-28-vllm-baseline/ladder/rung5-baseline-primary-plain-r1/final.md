The export functionality has been updated to include a totals row when requested. changes made:

1. **export.py**: Modified `export_csv` function to accept a `totals` parameter (default `False`). When `totals=True`, it calculates column totals using `column_totals` and appends a row starting with "TOTAL" followed by the totals.
2. **totals.py**: Enhanced `column_totals` to handle mixed data types gracefully. It attempts to sum numeric values and returns an empty string for columns with no numeric values, resolving issues with text cells.
3. The tests for exporting with totals now pass, confirming the totals row is included correctly.

The legacy export (exports_legacy.py) remains unchanged as it's marked for old integration.

You should now see the totals row in exports when calling `export_csv(rows, totals=True)`.