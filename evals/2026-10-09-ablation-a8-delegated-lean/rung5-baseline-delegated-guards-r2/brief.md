Fix the CSV export so it can include a totals row, making the test suite pass.

Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-wl0csy56/rung5

Test command: uv run --offline pytest -q
Right now it reports: 3 failed, 1 passed. The task is complete only when it exits 0 with 4 passed.

Files that matter:
- test_export.py — the specification for the required behavior. It must not be changed.
- export.py — export_csv currently has no totals option.
- render.py — render_rows currently has no mark_last option.
- totals.py — column_totals currently raises TypeError on text cells.

Constraint: exports_legacy.py is marked "Do not change." Leave it alone.

Read the failing tests, change the implementation files (export.py, render.py, totals.py) so all four tests pass, then run the test command and report the files you changed and the final test output.