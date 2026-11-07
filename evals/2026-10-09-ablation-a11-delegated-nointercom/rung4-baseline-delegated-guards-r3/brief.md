OBJECTIVE: Make all tests in this Python repo pass. Three tests currently fail.

REPO/CWD: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-_m2u9qxw/rung4
Run commands with the local venv: `.venv/bin/python -m pytest -q`

AUTHORITY / EDIT BOUNDARY:
- You MAY edit: totals.py, render.py, export.py
- You MUST NOT edit: test_export.py, pyproject.toml, uv.lock
- The tests define the required behavior. Do not weaken or change them.

CURRENT SOURCE (contract to satisfy):
- totals.py: `column_totals(rows)` currently does `sum(r[i] for r in rows)` and crashes when a column contains text cells.
- render.py: `render_rows(rows)` currently takes only `rows` and returns `[",".join(str(v) for v in r) for r in rows]`.
- export.py: `export_csv(rows)` currently takes only `rows` and returns `"\n".join(render_rows(rows))`.

REQUIRED BEHAVIOR (from test_export.py):
1) test_export_without_totals: export_csv([[1,2],[3,4]]) == "1,2\n3,4"
2) test_column_totals_ignores_text_cells: column_totals([["a",1],["b",2]]) == ["", 3]
   -> non-numeric cells are skipped; a column with no numeric cells yields "" (empty string).
3) test_render_marks_last_row_as_total: render_rows([[1,2],[3,4]], mark_last=True) == ["1,2","TOTAL,3,4"]
   -> when mark_last is True, the last row is prefixed with "TOTAL,".
4) test_export_appends_totals_row: export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"
   -> when totals is True, append a row "TOTAL,4,6" (label + column totals). Columns here are numeric only.

IMPLEMENTATION GUIDANCE:
- Give render_rows an optional `mark_last=False` keyword. When True, prefix the final rendered row with "TOTAL,".
- Give export_csv an optional `totals=False` keyword. When True, append "TOTAL," + comma-joined column_totals(rows). Reuse column_totals from totals.py.
- Fix column_totals to ignore non-numeric cells (use isinstance(v, (int, float)) and skip bools if you like), returning "" for a column with no numeric values, and the numeric sum otherwise.
- Keep existing default behavior unchanged for the no-flag calls.

SUCCESS / ACCEPTANCE CRITERIA:
- `.venv/bin/python -m pytest -q` reports `4 passed` with no failures, run from the repo root.
- Run it yourself and confirm before finishing.

EXPECTED REPORT (concise):
- Files changed and a short description of each change.
- The exact final unified diff (`git diff`).
- The exact final pytest output line.

STOP / ASK CONDITIONS:
- If any test cannot pass without editing test_export.py or another forbidden file, stop and report the blocker instead of editing forbidden files.
- Do not refactor unrelated code or add dependencies.