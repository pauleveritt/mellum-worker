Files changed:
- totals.py: Updated `column_totals` to handle mixed numeric and non-numeric values, returning empty string for columns without numeric values.
- render.py: Modified `render_rows` to accept `mark_last` parameter and prepend "TOTAL," to the last row when requested.
- export.py: Rewrote to import `column_totals`, added `totals` parameter, and appends a total row when `totals=True`.

Test output:
....                                                                     [100%]
4 passed in 0.01s

All tests now pass.