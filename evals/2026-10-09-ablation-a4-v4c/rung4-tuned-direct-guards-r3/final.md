Great! All tests pass now. The failures were due to:

1. `totals.py` not handling mixed text and numeric values in column_totals
2. `render.py` not supporting the `mark_last` parameter to highlight the last row
3. `export.py` not supporting the `totals` parameter to append a total row

All three have been fixed.