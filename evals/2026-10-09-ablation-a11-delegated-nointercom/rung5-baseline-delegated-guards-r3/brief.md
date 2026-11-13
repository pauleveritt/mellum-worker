Bounded bug fix in the Python project at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ap86ma6c/rung5

GOAL: The CSV export is missing the totals row. Make the existing test suite pass by implementing the behavior specified in test_export.py. Do NOT change any test.

AUTHORITY / EDIT BOUNDARY: You may edit only these three files: render.py, totals.py, export.py. Do NOT edit test_export.py or exports_legacy.py (legacy file is explicitly off-limits).

CONTEXT — current files:
- render.py: `def render_rows(rows): return [",".join(str(v) for v in r) for r in rows]`
- totals.py: `def column_totals(rows): if not rows: return [] ; return [sum(r[i] for r in rows) for i in range(len(rows[0]))]`
- export.py: `def export_csv(rows): return "\n".join(render_rows(rows))`
- test_export.py is the spec (do not modify it).

REQUIRED BEHAVIOR (these are exactly the failing tests):
1. test_column_totals_ignores_text_cells: column_totals([["a", 1], ["b", 2]]) == ["", 3]. For each column, if every cell in that column is numeric, return its sum; otherwise return "" (empty string) for that column.
2. test_render_marks_last_row_as_total: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]. Add a `mark_last=False` keyword parameter; when True, render the last row with a leading "TOTAL," prefix (e.g. last row [3,4] becomes "TOTAL,3,4"). Non-last rows render normally.
3. test_export_appends_totals_row: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". Add a `totals=False` keyword parameter; when True, compute column_totals(rows) and append that totals row using render_rows(..., mark_last=True), joining all rows with "\n".
4. test_export_without_totals must keep passing: export_csv([[1, 2], [3, 4]]) == "1,2\n3,4".

VALIDATION (required): Run `.venv/bin/python -m pytest -q` from the project directory and confirm all 4 tests pass.

REPORT BACK: list files changed, the exact pytest result line (e.g. "4 passed"), and any blockers. If you cannot make the tests pass, stop and report the exact failure output instead of guessing.