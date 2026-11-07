Fix the failing tests in this repo. cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-om1angq2/rung5

Bug: the CSV export is missing the totals row. `.venv/bin/pytest -q` currently reports 3 failed, 1 passed:

- test_column_totals_ignores_text_cells -> TypeError: unsupported operand type(s) for +: 'int' and 'str' (totals.py:4)
- test_render_marks_last_row_as_total -> TypeError: render_rows() got an unexpected keyword argument 'mark_last'
- test_export_appends_totals_row -> TypeError: export_csv() got an unexpected keyword argument 'totals'

Required behavior (from test_export.py, which you must NOT edit):

1. totals.py `column_totals(rows)` -> list of per-column sums. Non-numeric ("text") cells are skipped. For `[["a", 1], ["b", 2]]` the result must be `["", 3]`: column 0 has no numeric values so its total is the empty string, column 1 sums to 3.
2. render.py `render_rows(rows)` -> list of comma-joined row strings. Add optional `mark_last=False`. When True, the LAST row is prefixed with `TOTAL,` before its values, e.g. `render_rows([[1,2],[3,4]], mark_last=True) == ["1,2", "TOTAL,3,4"]`.
3. export.py `export_csv(rows)` -> joins rendered rows with "\n". Add optional `totals=False`. When True, compute `column_totals(rows)` and append it as a final row rendered with the TOTAL marker, e.g. `export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`.

Constraints:
- Keep the existing signature working: `export_csv([[1,2],[3,4]]) == "1,2\n3,4"` (no totals row by default, no trailing newline).
- Do NOT edit test_export.py, exports_legacy.py (it says "Do not change"), or pyproject.toml.
- Make minimal changes, keep public function signatures backward compatible.

Steps: read the four .py files, run `.venv/bin/pytest -q` to see the failures, implement the fix, then run `.venv/bin/pytest -q` again until all 4 tests pass.

Report back: the exact edits (file + new content), the final pytest output line, and any uncertainty.