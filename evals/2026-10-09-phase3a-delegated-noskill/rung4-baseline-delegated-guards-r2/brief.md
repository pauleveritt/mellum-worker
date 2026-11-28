In the repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-uo9fh_d8/rung4, make the failing tests in test_export.py pass.

Current state: `.venv/bin/python -m pytest -q` shows 3 failed, 1 passed:
- test_column_totals_ignores_text_cells: TypeError in totals.py column_totals (sum mixes int and str)
- test_render_marks_last_row_as_total: render_rows() has no mark_last kwarg
- test_export_appends_totals_row: export_csv() has no totals kwarg

The 4 tests in test_export.py are the specification — do not edit test_export.py. Implement the behavior in export.py, render.py, and totals.py:
- export_csv(rows): currently takes only rows; needs to accept totals=False.
- render_rows(rows): needs to accept mark_last=False; when True, the last row is prefixed with "TOTAL".
- column_totals(rows): must ignore non-numeric (text) cells, producing "" for a column with no numeric values, and the sum of the numeric cells otherwise.

Run `.venv/bin/python -m pytest -q` and confirm all 4 tests pass. Keep the change minimal. Report the final pytest output and the exact files/edits made.