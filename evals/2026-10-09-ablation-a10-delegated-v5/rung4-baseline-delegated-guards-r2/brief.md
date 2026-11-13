Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-x7xxoe29/rung4

Goal: make every test in test_export.py pass. Do NOT modify test_export.py — it is the specification. You may edit export.py, render.py, and totals.py.

Start by running `uv run pytest -q` to see the 3 failures.

Required behavior:

1) totals.column_totals(rows)
   - Return one entry per column.
   - If every value in a column is numeric (int/float), return that column's sum.
   - If a column contains any non-numeric value, return "" for that column.
   - Empty rows -> [].
   - Example: column_totals([["a", 1], ["b", 2]]) == ["", 3]
   - Example: column_totals([[1, 2], [3, 4]]) == [4, 6]

2) render.render_rows(rows, mark_last=False)
   - Default (mark_last=False) stays as today: [",".join(str(v) for v in r) for r in rows].
   - When mark_last=True, render the same way but prefix the LAST row with "TOTAL,". So the last list entry is "TOTAL," + the comma-joined values of that row.
   - Example: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]

3) export.export_csv(rows, totals=False)
   - Default (totals=False) stays as today: "\n".join(render_rows(rows)).
   - When totals=True: compute column_totals(rows), append that totals row to rows, render all rows with render_rows(..., mark_last=True), and join with "\n".
   - Example: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"

Keep the existing function names and import paths unchanged.

After editing, run `uv run pytest -q` and confirm the summary says 4 passed.

Report back exactly: (a) list of files changed, (b) the final pytest summary line, (c) any tests still failing.