The failing test has been fixed! All tests pass now:

- `test_export_without_totals` PASSED
- `test_column_totals_ignores_text_cells` PASSED
- `test_render_marks_last_row_as_total` PASSED
- `test_export_appends_totals_row` PASSED

The changes made:
1. **export.py**: Fixed the totals parameter to use comma instead of semicolon when appending total row, and properly imports `column_totals`
2. **render.py**: Fixed the `mark_last` logic to prefix "TOTAL," instead of trying to replace the first column
3. **totals.py**: Updated `column_totals` to ignore non-numeric values and return empty string for non-numeric columns

All issues have been resolved.