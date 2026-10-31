The failing tests have been made to pass by fixing the three core files:
- `totals.py` now safely handles mixed numeric and text values in `column_totals`
- `render.py` now supports the `mark_last` parameter to annotate the last row
- `export.py` now supports the `totals` parameter to append a computed totals row

All tests pass successfully.