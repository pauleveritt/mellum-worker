The failing tests have been fixed and now all pass:

```
test_export.py ....                                                      [100%]

============================== 4 passed in 0.01s ===============================
```

Changes made:

1. **totals.py** – Updated `column_totals` to handle non-numeric cells by returning an empty string for columns containing text, and summing only numeric columns.

2. **render.py** – Added `mark_last` parameter to `render_rows` and modified the last row to prepend "TOTAL" when `mark_last=True`.

3. **export.py** – Added `totals` parameter to `export_csv`, integrated `column_totals`, and appends a totals row when `totals=True`.

These modifications satisfy all test cases:
- `test_column_totals_ignores_text_cells`
- `test_render_marks_last_row_as_total`
- `test_export_appends_totals_row`
- `test_export_without_totals` (still passes)

The codebase is now consistent with the expected behavior.