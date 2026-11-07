The issue has been resolved. The export functionality now includes a totals row when requested. Changes were made to:

- `export.py`: Added logic to compute column totals and append a totals row when `totals=True`.
- `totals.py`: Updated `column_totals` to correctly handle numeric and non-numeric values.
- `render.py`: Enhanced `render_rows` to support marking the last row as total (for other uses).

All tests pass successfully.