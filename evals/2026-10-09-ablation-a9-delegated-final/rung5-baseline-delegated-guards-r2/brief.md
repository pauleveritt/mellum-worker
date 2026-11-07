Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-qsl3t3z7/rung5

BUG: The CSV export is missing the totals row. `test_export.py` is the acceptance spec. Currently 3 of 4 tests fail with TypeErrors because the new keyword arguments were never implemented.

Implement exactly these, keeping the existing passing test green:

1. totals.py — `column_totals(rows)` must skip/handle text cells so that:
   `column_totals([["a", 1], ["b", 2]]) == ["", 3]`
   i.e. a column containing any non-numeric cell yields "" (empty string); otherwise sum the column. `column_totals([])` must still return `[]`.

2. render.py — `render_rows(rows, mark_last=False)` keeps current default behavior unchanged:
   `render_rows([[1, 2], [3, 4]]) == ["1,2", "3,4"]`
   With `mark_last=True`, the last rendered row is prefixed with `TOTAL,`:
   `render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]`

3. export.py — `export_csv(rows, totals=False)` keeps default behavior `export_csv([[1, 2], [3, 4]]) == "1,2\n3,4"`. With `totals=True`, append a totals row computed by `column_totals(rows)` and marked as a total, so:
   `export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`

Constraints:
- Do NOT modify exports_legacy.py (it says "Do not change").
- Do NOT modify test_export.py.
- Keep the diff minimal and idiomatic; only touch totals.py, render.py, export.py.
- Do not add dependencies.

Verification (required): run
  cd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-qsl3t3z7/rung5 && .venv/bin/python -m pytest -q
and report the exact command and full output. All 4 tests must pass. Also run `git diff` and include it in your report. If you cannot make all tests pass, report exactly which tests fail and the raw error output; do not claim success.