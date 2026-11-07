The export functionality has been fixed to include the totals row when requested. The following changes were made:

1. **export.py**: Updated to import `column_totals` from `totals`, added `totals` parameter to `export_csv`, and appends a total row computed by `column_totals` when `totals=True`.
2. **totals.py**: Revised `column_totals` to safely handle mixed numeric and non-numeric values, summing only numeric values and returning an empty string for columns with no numeric data.
3. **render.py**: Modified `render_rows` to support a `mark_last` parameter that prefixes the last row with "TOTAL" when requested.

All tests now pass:

```
....                                                                     [100%]
4 passed in 0.00s
```

Verification example:
```bash
python -c "from export import export_csv; print(repr(export_csv([[1, 2], [3, 4]], totals=True)))"
```
Output: `'1,2\n3,4\nTOTAL,4,6'`

The export now correctly includes the totals row.