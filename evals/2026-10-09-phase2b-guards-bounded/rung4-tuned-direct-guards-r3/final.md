Files changed:
- totals.py: Fixed column_totals to ignore non-numeric values by checking isinstance before summing.
- render.py: Added mark_last parameter to prepend "TOTAL," to the last row when requested.
- export.py: Added totals parameter to append a totals row using column_totals and render_rows.

Test output:
....                                                                     [100%]
4 passed in 0.00s

Nothing else to do.