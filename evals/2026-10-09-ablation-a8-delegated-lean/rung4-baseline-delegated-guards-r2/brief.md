Make the failing tests in test_export.py pass. Work only in the current working directory.

Run this first to see the failures:
  .venv/bin/python -m pytest -q

There are 3 failing tests, all in test_export.py:
1. test_column_totals_ignores_text_cells: column_totals([["a", 1], ["b", 2]]) must return ["", 3]. Per column, sum only numeric (int/float) cells; if a column has no numeric cells, use "" for it. Keep the empty-rows behavior returning [].
2. test_render_marks_last_row_as_total: render_rows([[1, 2], [3, 4]], mark_last=True) must return ["1,2", "TOTAL,3,4"]. Add a mark_last=False keyword argument; when True, prefix the last rendered row with "TOTAL,". Default behavior for render_rows(rows) must stay unchanged.
3. test_export_appends_totals_row: export_csv([[1, 2], [3, 4]], totals=True) must return "1,2\n3,4\nTOTAL,4,6". Add a totals=False keyword argument; when True, append a totals row built from column_totals(rows) (so the numbers are summed), rendered with the same "TOTAL," prefix, joined by newlines. Default export_csv(rows) must stay unchanged.

Constraints:
- Do NOT modify test_export.py. Only change totals.py, render.py, export.py as needed.
- Keep the existing style (simple functions, no new dependencies).

Definition of done: run `.venv/bin/python -m pytest -q` and confirm all 4 tests pass. Report the exact final pytest output line and a summary of the edits you made.