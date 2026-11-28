Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-84s7u9t3/rung4

Goal: make ALL tests in test_export.py pass. Do NOT modify test_export.py.

Current state (`pytest -q`): 1 failed, 1 passed. Failures come from three functions:

files:
- totals.py: `column_totals(rows)` currently does `sum(r[i] for r in rows)`, which raises TypeError on text cells.
- render.py: `render_rows(rows)` has no `mark_last` parameter.
- export.py: `export_csv(rows)` has no `totals` parameter.

Required behavior (exactly what test_export.py asserts):
1. `export_csv([[1,2],[3,4]])` -> `"1,2\n3,4"`  (no totals by default)
2. `column_totals([["a",1],["b",2]])` -> `["", 3]`  (ignore non-numeric cells; a column with zero numbers yields `""`; `column_totals([])` -> `[]`)
3. `render_rows([[1,2],[3,4]], mark_last=True)` -> `["1,2", "TOTAL,3,4"]`  (normal call without mark_last must stay `["1,2","3,4"]`)
4. `export_csv([[1,2],[3,4]], totals=True)` -> `"1,2\n3,4\nTOTAL,4,6"`  (append a row: literal `"TOTAL"` prefix, then the column totals for numeric columns)

Rules:
- Only edit totals.py, render.py, export.py. Do not touch tests or pyproject.toml.
- Keep signatures backward compatible (new params must be keyword defaults).
- Run `.venv/bin/python -m pytest -q` at the end and iterate until it reports all tests passing.
- Report back: files changed, the final pytest output line, and any assumption you made.