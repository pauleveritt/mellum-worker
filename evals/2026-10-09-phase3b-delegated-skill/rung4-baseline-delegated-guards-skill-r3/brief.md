Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-6w9y6133/rung4

Goal: Make all tests in test_export.py pass by editing the source modules. Do NOT edit test_export.py.

Current state: 3 failed, 1 passed. Run tests with: .venv/bin/python -m pytest -q

Required behavior revealed by the failing tests:
1. totals.column_totals(rows) must ignore non-numeric (e.g. text) cells so that column_totals([["a", 1], ["b", 2]]) == ["", 3]. Numeric columns sum normally; a column with no numbers yields "".
2. render.render_rows(rows, mark_last=False) gains a keyword arg. When mark_last=True, the last row is rendered with a leading "TOTAL" marker: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]. With mark_last=False behavior is unchanged: render_rows([[1,2],[3,4]]) == ["1,2","3,4"].
3. export.export_csv(rows, totals=False) gains a keyword arg. When totals=True, append a totals row computed with column_totals, rendered with the TOTAL marker: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". Default totals=False must keep export_csv([[1,2],[3,4]]) == "1,2\n3,4".

Constraints: keep changes minimal and consistent with existing style; do not add dependencies. Verify by actually running `.venv/bin/python -m pytest -q` and report the final pass/fail counts and the exact diff (git diff) in your final message.