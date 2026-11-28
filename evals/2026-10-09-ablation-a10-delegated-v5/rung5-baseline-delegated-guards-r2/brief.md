Repo directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-leamp3oy/rung5

Task: make the CSV export include a totals row, so that all tests in test_export.py pass.

Test command: .venv/bin/python -m pytest -q

Currently 3 tests fail. The test expectations are the spec:
- render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
  (add a mark_last=False parameter; when True, prefix the LAST row with an extra first column "TOTAL")
- column_totals([["a", 1], ["b", 2]]) == ["", 3]
  (per-column sum; a column that contains any non-numeric cell yields "" for that column)
- export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"
  (add a totals=False parameter; when True, append a final row that is the string "TOTAL" followed by column_totals(rows))

Constraints:
- Do NOT modify test_export.py.
- Do NOT modify exports_legacy.py (explicitly marked "Do not change").
- Keep export_csv(rows) behavior unchanged when totals is not passed: export_csv([[1, 2], [3, 4]]) == "1,2\n3,4".

When done, reply with the files you changed and the final test output.