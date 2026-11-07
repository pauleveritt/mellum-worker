I've fixed the issue by updating `export.py` to include a totals row when the `totals` flag is set. The function now imports `column_totals` from `totals.py` and appends a row formatted as `["TOTAL", ...totals...]` when `totals=True`.

Export now correctly includes the totals row:
```bash
python -c "from export import export_csv; print(export_csv([[1, 2], [3, 4]], totals=True))"
# Output:
# 1,2
# 3,4
# TOTAL,4,6
```

Tests still pass, and the export functionality should now work as expected.