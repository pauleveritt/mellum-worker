Bounded coding task in the current directory (a small Python project with `export.py`, `render.py`, `totals.py`, `exports_legacy.py`, `test_export.py`, `pyproject.toml`).

GOAL: The CSV export does not append a totals row. Make the failing tests in `test_export.py` pass. Do NOT change the tests to fit the code — change the code to fit the tests.

Baseline: `uv run pytest -q` → 3 failed, 1 passed.

Exact required contracts (from test_export.py):
1. `render_rows(rows, mark_last=False)` — when `mark_last=True`, render the last row prefixed with `TOTAL,`. Example: `render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]`. Default behavior (mark_last=False) must stay unchanged: `render_rows([[1,2],[3,4]]) == ["1,2","3,4"]`.
2. `column_totals(rows)` — must ignore non-numeric cells instead of raising. Example: `column_totals([["a", 1], ["b", 2]]) == ["", 3]` (a column with no numeric values yields `""`; note `sum([True,2])` and strings must not crash). Example: `column_totals([[1,2],[3,4]]) == [4,6]`. Empty input still returns `[]`.
3. `export_csv(rows, totals=False)` — default output unchanged: `export_csv([[1,2],[3,4]]) == "1,2\n3,4"`. With `totals=True`, append a totals row computed by `column_totals` and rendered with the `TOTAL,` prefix: `export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`.

HARD CONSTRAINTS:
- Do NOT modify `test_export.py` or `exports_legacy.py` (a comment in the latter says to leave it alone).
- Keep the default CSV format (comma-separated, "\n" joined) unchanged.
- Keep changes minimal and in `render.py`, `totals.py`, `export.py`.

STEPS:
1. Read all the files listed above.
2. Edit the code.
3. Run `uv run pytest -q` and confirm 4 passed.
4. Report back with: the final contents of the functions you changed, and the exact pytest output line (e.g. "4 passed").