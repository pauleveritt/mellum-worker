Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-yd5hyonm/rung5 (cwd). Python venv at .venv. Run tests with `.venv/bin/python -m pytest -q`.

BUG: CSV export is missing the totals row. `test_export.py` is the authoritative spec — it currently has 3 failures. Make all 4 tests in test_export.py pass by implementing exactly the minimal behavior the tests require.

Required behavior:
1. `totals.column_totals(rows)` — return one sum per column, summing ONLY numeric (int/float) cells and ignoring text cells. If a column has no numeric cells, its entry must be the empty string "" (see `column_totals([["a",1],["b",2]]) == ["", 3]`). Return [] for empty input.
2. `render.render_rows(rows, mark_last=False)` — keep current behavior when mark_last is False. When mark_last is True, prefix the LAST row with the literal cell "TOTAL" before joining, e.g. row [3,4] renders as "TOTAL,3,4". Do not mark any other row.
3. `export.export_csv(rows, totals=False)` — keep current behavior when totals is False (`"1,2\n3,4"`). When totals is True, append a totals row built from `column_totals(rows)` and render it marked, e.g. `export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`.

Constraints:
- Do NOT modify test_export.py.
- Do NOT modify exports_legacy.py (marked "Do not change").
- Keep changes minimal and focused on these three files only.
- Use the existing modules; do not add new dependencies.

Definition of done: run `.venv/bin/python -m pytest -q` and report the exact final output line plus the full diff (`git diff`). If a test cannot be made to pass, say so explicitly instead of claiming success.