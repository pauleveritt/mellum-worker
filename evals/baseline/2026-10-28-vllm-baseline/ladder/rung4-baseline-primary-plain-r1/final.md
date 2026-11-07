The failing test has been fixed. All tests now pass:

- `totals.py`: Updated `column_totals` to ignore non-numeric cells and compute sums only for numeric values.
- `render.py`: Modified `render_rows` to accept `mark_last` and prepend "TOTAL" to the last row when requested.
- `export.py`: Updated `export_csv` to accept `totals` parameter and append a total row with "TOTAL" and column totals.

Running `python -m pytest test_export.py` now yields 4 passed tests.