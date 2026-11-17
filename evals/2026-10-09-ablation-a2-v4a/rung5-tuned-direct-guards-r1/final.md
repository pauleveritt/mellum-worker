The export functionality has been updated to include a totals row when requested. The code changes ensure that:

1. `export.py` now accepts a `totals` parameter and appends a totals row computed by `column_totals` when enabled.
2. `totals.py` correctly computes totals for numeric columns while handling mixed data types.
3. `render.py` can optionally mark the last row as total when needed.

All tests now pass successfully.