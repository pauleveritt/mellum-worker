You are fixing a small Python project so its failing tests pass.

Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-pnsqmscn/rung4

Files: export.py, render.py, totals.py, and the test file test_export.py.
Run the tests with: .venv/bin/python -m pytest -q

Currently 3 tests fail (1 passes):
1. test_column_totals_ignores_text_cells:
   column_totals([["a", 1], ["b", 2]]) == ["", 3]
   The current implementation crashes summing a str with int. It must sum only numeric cells per column and put "" for a column with no numeric values.
2. test_render_marks_last_row_as_total:
   render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
   render_rows currently only accepts `rows`; add a `mark_last` keyword (default False) that prefixes the last rendered row with "TOTAL,".
3. test_export_appends_totals_row:
   export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"
   export_csv currently only accepts `rows`; add a `totals` keyword (default False) that appends a totals row (label "TOTAL" plus the column totals) when true.

Constraints:
- Keep the existing passing test test_export_without_totals working: export_csv([[1, 2], [3, 4]]) == "1,2\n3,4".
- Do not modify test_export.py.
- Make the minimal change.
- Run the full test suite and only stop when all 4 tests pass.
- Report the final exact pytest output and a short summary of the code changes (files/functions changed).