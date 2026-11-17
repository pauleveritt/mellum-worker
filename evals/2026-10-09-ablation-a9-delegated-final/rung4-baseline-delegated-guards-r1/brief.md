Make the failing tests in this repo pass.

Repo cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-yudxemy1/rung4

Constraints:
- Do NOT modify test_export.py. Only edit source files: totals.py, render.py, export.py.
- Keep changes minimal and Python-idiomatic.

Failing tests and required behavior:
1) test_column_totals_ignores_text_cells: column_totals([["a",1],["b",2]]) == ["", 3]
   - Sum per column, but skip non-numeric cells. If a column has no numeric values, the total is the empty string "".
2) test_render_marks_last_row_as_total: render_rows([[1,2],[3,4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
   - render_rows(rows, mark_last=False). When mark_last=True, prefix the LAST row's rendering with "TOTAL," (i.e. "TOTAL,3,4"). Other rows unchanged.
3) test_export_appends_totals_row: export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"
   - export_csv(rows, totals=False). When totals=True, append a totals row computed via column_totals(rows), rendered with the "TOTAL," prefix, joined by \n.
- test_export_without_totals must stay passing: export_csv([[1,2],[3,4]]) == "1,2\n3,4".

Run `.venv/bin/python -m pytest -q` and iterate until all 4 tests pass. Then report the final file contents and the pytest output.