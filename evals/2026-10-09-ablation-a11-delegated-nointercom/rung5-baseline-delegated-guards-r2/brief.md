Fix the CSV export so the totals row appears. This is a small Python repo at the current working directory.

CONTEXT — failing tests define the spec
`test_export.py` has 4 tests. Running `.venv/bin/python -m pytest -q` currently gives 3 failures:
1. test_column_totals_ignores_text_cells: `column_totals([["a", 1], ["b", 2]])` should be `["", 3]` but raises TypeError because `sum()` adds strings.
2. test_render_marks_last_row_as_total: `render_rows([[1, 2], [3, 4]], mark_last=True)` should be `["1,2", "TOTAL,3,4"]` but raises TypeError: unexpected keyword `mark_last`.
3. test_export_appends_totals_row: `export_csv([[1, 2], [3, 4]], totals=True)` should be `"1,2\n3,4\nTOTAL,4,6"` but raises TypeError: unexpected keyword `totals`.

REQUIRED CHANGES (minimal, one per module)
- `totals.py` — `column_totals(rows)`: for each column index, sum only the numeric values and ignore non-numeric cells; if a column has no numeric values, that column's entry is the empty string `""`. Keep `[]` for empty input. `column_totals([["a",1],["b",2]])` must equal `["", 3]`.
- `render.py` — `render_rows(rows, mark_last=False)`: default behavior unchanged. When `mark_last=True`, prefix the LAST row with `"TOTAL,"` (i.e. `render_rows([[1,2],[3,4]], mark_last=True) == ["1,2","TOTAL,3,4"]`).
- `export.py` — `export_csv(rows, totals=False)`: default behavior unchanged. When `totals=True`, append the computed `column_totals(rows)` row at the end and render with `mark_last=True`. `export_csv([[1,2],[3,4]], totals=True)` must equal `"1,2\n3,4\nTOTAL,4,6"`.

HARD CONSTRAINTS
- Do NOT edit `test_export.py` (it is the spec) and do NOT edit `exports_legacy.py` (it says "Do not change").
- Only touch `export.py`, `render.py`, `totals.py`. Keep existing default behavior for all callers.
- Do not add dependencies or refactor unrelated code.

VERIFY
Run `.venv/bin/python -m pytest -q` and confirm all 4 tests pass. Report: files changed, the exact pytest output, and any residual uncertainty.