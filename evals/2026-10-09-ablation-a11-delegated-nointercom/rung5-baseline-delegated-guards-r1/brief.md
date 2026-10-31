You are fixing a bug in the Python repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-0a6_8r1b/rung5 (this is your cwd).

BUG: The CSV export is missing the totals row. The test suite in test_export.py defines the required behavior and currently has 3 failures.

Run this first to see the failures:
  .venv/bin/python -m pytest -q

Required behavior (from test_export.py):
1. export_csv(rows, totals=False) must keep the existing default behavior:
   export_csv([[1,2],[3,4]]) == "1,2\n3,4"
2. export_csv(rows, totals=True) must append a totals row:
   export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"
3. render_rows(rows, mark_last=False) must support mark_last=True, which prepends "TOTAL" to the LAST rendered row:
   render_rows([[1,2],[3,4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
4. column_totals(rows) must sum numeric columns but return "" for any column containing non-numeric text:
   column_totals([["a",1],["b",2]]) == ["", 3]

Implementation guidance (keep it minimal):
- totals.py: guard each column so it only sums when every value is numeric; otherwise put "" for that column. Keep returning [] for empty rows.
- render.py: render_rows(rows, mark_last=False) renders rows as before, and when mark_last is True prefixes "TOTAL," to the last line (do nothing if there are no rows).
- export.py: export_csv(rows, totals=False) should build the output rows, append column_totals(rows) as the final row when totals is True, and render with mark_last=totals.

CONSTRAINTS:
- Use the "\n" line separator (LF), not "\r\n".
- Do NOT modify exports_legacy.py — it is intentionally frozen.
- Do NOT weaken, delete, or edit any test in test_export.py. All 4 tests must pass.
- Only edit export.py, render.py, totals.py.

When done, run:
  .venv/bin/python -m pytest -q
and report the exact final output plus which files you changed.