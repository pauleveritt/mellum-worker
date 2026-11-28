Make the failing tests in this repo pass. Working dir: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-1t78z0j4/rung4

Current state: `python -m pytest -q` (use `.venv/bin/python -m pytest -q`) has 3 failures:
1. test_export.py::test_column_totals_ignores_text_cells — totals.py's column_totals does `sum(r[i] for r in rows)`, which crashes on text cells. Expected: text cells are ignored and contribute "" for that column; `column_totals([["a", 1], ["b", 2]]) == ["", 3]`.
2. test_export.py::test_render_marks_last_row_as_total — render.render_rows needs a `mark_last=False` keyword; when True the last row is prefixed with "TOTAL,": `render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]`.
3. test_export.py::test_export_appends_totals_row — export.export_csv needs a `totals=False` keyword; when True it appends a totals row rendered with the TOTAL marker: `export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`.

Requirements: do not modify test_export.py. Keep existing passing test test_export_without_totals passing. Implement the minimal changes in totals.py, render.py, and export.py. Then run the full test suite with `.venv/bin/python -m pytest -q` and report the exact output as evidence, plus a summary of the files you changed.