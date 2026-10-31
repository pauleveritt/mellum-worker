Bug: the CSV export is missing the totals row. Fix it so all tests in test_export.py pass.

Working directory: /var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-77zmqcg3/rung5 (the repo cwd)

Baseline evidence (currently 3 failed, 1 passed):
- test_column_totals_ignores_text_cells: TypeError: unsupported operand type(s) for +: 'int' and 'str'
- test_render_marks_last_row_as_total: TypeError: render_rows() got an unexpected keyword argument 'mark_last'
- test_export_appends_totals_row: TypeError: export_csv() got an unexpected keyword argument 'totals'

Required behavior (from test_export.py — do not edit the tests):
1. render.py: render_rows(rows, mark_last=False) -> list[str]. Existing behavior unchanged by default. When mark_last=True, the LAST rendered row is prefixed with "TOTAL,". Example: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"].
2. totals.py: column_totals(rows) must return one entry per column. Numeric cells are summed; non-numeric (text) cells are ignored and that column yields "" instead of a number. Example: column_totals([["a", 1], ["b", 2]]) == ["", 3]. Empty rows -> [].
3. export.py: export_csv(rows, totals=False) -> str. Existing behavior unchanged by default (rows joined with "\n"). When totals=True, append a final row "TOTAL," + comma-joined column totals. Example: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". Hint: use column_totals and render_rows(..., mark_last=True) rather than duplicating formatting logic.

Constraints:
- Modify only render.py, totals.py, export.py. Do NOT edit test_export.py or exports_legacy.py (legacy, explicitly do not change).
- Keep the public function names/signatures backward compatible (new parameters must be keyword-defaulted).
- Minimal diff; no new dependencies; no refactors beyond what the tests require.

Verify: run `.venv/bin/python -m pytest -q` in the repo and confirm 4 passed, 0 failed. Report: files changed, the final pytest summary line, and any uncertainty.