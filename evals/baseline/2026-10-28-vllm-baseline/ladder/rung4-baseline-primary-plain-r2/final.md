The failing tests have been fixed successfully. All tests in test_export.py now pass:

- test_column_totals_ignores_text_cells
- test_render_marks_last_row_as_total
- test_export_appends_totals_row
- test_export_without_totals

Changes made:
1. Updated `totals.py` to handle mixed numeric/non-numeric values by summing only numeric entries and returning empty string for columns with no numeric values.
2. Updated `render.py` to accept `mark_last` parameter and prepend "TOTAL," to the last row when requested.
3. Updated `export.py` to accept `totals` parameter, compute totals using `column_totals`, and append a formatted totals row with "TOTAL," prefix.

Let me know if you need further adjustments!