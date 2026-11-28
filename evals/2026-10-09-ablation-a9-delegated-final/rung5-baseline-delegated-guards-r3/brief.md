Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-dkc9533p/rung5 (Python, run tests with `.venv/bin/python -m pytest -q`).

Bug: the CSV export is missing its totals row. There are 3 failing tests in test_export.py that define the required behavior. Make them pass without breaking the passing one.

Required changes:
1. totals.py — `column_totals(rows)` must ignore non-numeric/text cells: `column_totals([["a", 1], ["b", 2]]) == ["", 3]`. Empty input still returns []. Sum numeric cells per column; use "" for a column with no numeric values.
2. render.py — `render_rows(rows, mark_last=False)`. When `mark_last=True`, the last row is prefixed with "TOTAL" as its first cell: `render_rows([[1,2],[3,4]], mark_last=True) == ["1,2", "TOTAL,3,4"]`. Default behavior unchanged.
3. export.py — `export_csv(rows, totals=False)`. When `totals=True`, append a totals row computed with `column_totals`, rendered as the marked last row: `export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`. Default (totals=False) unchanged.

Constraints:
- Do NOT modify exports_legacy.py (legacy, must stay as-is).
- Keep changes minimal and idiomatic.
- Run `.venv/bin/python -m pytest -q` and confirm ALL tests pass.

Report back: files changed, the diff, and the exact pytest output.