Repository: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-93mi4smo/rung5

Test command (run this, exactly): uv run --offline pytest -q

Goal: make all tests in test_export.py pass. Three tests currently fail because the code does not implement the required keyword arguments. Implement them:

1. totals.py — column_totals(rows)
   Must sum each column, but a column containing any text cell is not summable, so its total is the empty string "". Example: column_totals([["a", 1], ["b", 2]]) == ["", 3]. Empty rows still returns [].

2. render.py — render_rows(rows, mark_last=False)
   When mark_last is True, the last rendered row is prefixed with "TOTAL". Example: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]. With mark_last False (the default) behaviour is unchanged.

3. export.py — export_csv(rows, totals=False)
   It joins render_rows(rows) with "\n". When totals is True it appends a final row: the literal "TOTAL" followed by column_totals(rows), marked as the last row. Example: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". With totals False (the default) behaviour is unchanged.

Rules:
- Keep default behaviour for existing callers unchanged.
- Do NOT modify exports_legacy.py (it is legacy and intentionally not changed).
- Do NOT modify test_export.py.
- Edit the existing files; do not rewrite them wholesale.

When done, run the test command and reply with the files changed and the test output. The task is complete only when that command exits 0.