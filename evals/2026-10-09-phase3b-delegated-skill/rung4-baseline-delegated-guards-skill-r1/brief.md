You are working in the git repo /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-rytbhney/rung4. Make the failing tests pass.

Run the tests with:
  .venv/bin/python -m pytest -q

Currently 3 tests fail:
1. test_column_totals_ignores_text_cells — totals.py column_totals crashes when a column contains non-numeric cells. Expected: column_totals([["a", 1], ["b", 2]]) == ["", 3]. Non-numeric cells should be skipped when summing; if a column has no numeric cells, its total is "" (empty string).
2. test_render_marks_last_row_as_total — render.py render_rows must accept a keyword argument mark_last (default False). When mark_last=True, the LAST row is rendered with the literal prefix "TOTAL" in place of its first cell, keeping the remaining cells. Expected: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"].
3. test_export_appends_totals_row — export.py export_csv must accept a keyword argument totals (default False). When totals=True, append a totals row computed with totals.column_totals(rows), prefixed with the literal "TOTAL". Expected: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". export_csv([[1, 2], [3, 4]]) must still == "1,2\n3,4".

Constraints:
- Only edit totals.py, render.py, and export.py. Do NOT modify test_export.py.
- Keep the existing function signatures backward compatible (new args must be keyword with sensible defaults).
- Read the files first, make minimal edits, then run the full test suite and confirm all 4 tests pass.
- Report exactly which files you changed, the final pytest summary line, and paste the final contents of the three files.