OBJECTIVE
Make all tests in test_export.py pass by fixing the implementation modules only.

REPO/CWD
/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ntazj29t/rung4
Python venv: .venv/bin/python ; test runner: .venv/bin/python -m pytest -q

AUTHORITY / EDIT BOUNDARY
You may edit only source files: totals.py, render.py, export.py.
DO NOT modify test_export.py or any test file. Do not add dependencies.

CURRENT FAILURES (4 tests: 1 pass, 3 fail)
1) test_column_totals_ignores_text_cells
   assert column_totals([["a", 1], ["b", 2]]) == ["", 3]
   currently raises TypeError: sum() over str.
2) test_render_marks_last_row_as_total
   assert render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
   currently render_rows() has no mark_last kwarg.
3) test_export_appends_totals_row
   assert export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"
   currently export_csv() has no totals kwarg.
Passing test (must stay passing): test_export_without_totals
   assert export_csv([[1, 2], [3, 4]]) == "1,2\n3,4"

REQUIREMENTS
- column_totals(rows): when a column contains non-numeric cells, that column's total is the empty string "" (e.g. ["", 3]); numeric columns summed normally.
- render_rows(rows, mark_last=False): when mark_last=True, prefix the LAST rendered row with "TOTAL," (so ["1,2", "TOTAL,3,4"]).
- export_csv(rows, totals=False): when totals=True, append a final row beginning with "TOTAL," built from column_totals(rows).
- Keep default behavior unchanged so the passing test still passes.
- Make minimal, clean changes.

VALIDATION (mandatory)
Run: cd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ntazj29t/rung4 && .venv/bin/python -m pytest -q
Confirm 4 passed.

EXPECTED OUTPUT
Report: files changed with diff summary, the exact pytest output, and any edge cases you chose (e.g. empty rows). Stop and ask if the tests are ambiguous or require changing a test.