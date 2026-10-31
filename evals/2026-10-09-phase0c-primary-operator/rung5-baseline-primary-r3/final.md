Thanks for the report. I used the systematic-debugging skill to investigate why the export was missing the totals row.

**Root Cause:**  
The `export_csv` function didn't handle the `totals` flag and didn't integrate with `column_totals` to compute and append a totals row.

**Fix:**  
Modified `export.py` to:
1. Import `column_totals` from `totals.py`
2. Compute totals when `totals=True`
3. Format and append a "TOTAL,..." row using `render_rows`

**Verification:**  
Ran `pytest -v test_export.py::test_export_appends_totals_row` – **passed**.  
Manual test: `export_csv([[1, 2], [3, 4]], totals=True)` now returns `"1,2\n3,4\nTOTAL,4,6"`.

The export now includes the totals row when requested. The issue is resolved.