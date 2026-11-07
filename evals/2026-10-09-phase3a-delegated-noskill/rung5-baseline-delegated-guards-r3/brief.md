Objective: Fix the CSV export so it can include a totals row. Currently `pytest` has 3 failures because `export_csv` ignores a `totals=True` flag, `render_rows` ignores `mark_last=True`, and `column_totals` crashes on text cells.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-asoijzuc/rung5

The tests in test_export.py are the authoritative spec — they already encode the exact expected behavior. Read them first.

Required behavior (derived from the tests):
1. column_totals(rows): returns a list of column sums. If a column contains any non-numeric (e.g. text) cell, that column's total is "" (empty string). Test: column_totals([["a",1],["b",2]]) == ["",3]. Empty rows -> [].
2. render_rows(rows, mark_last=False): renders rows as comma-joined strings. When mark_last=True, the LAST row is prefixed with "TOTAL," (e.g. [[1,2],[3,4]] with mark_last=True -> ["1,2","TOTAL,3,4"]).
3. export_csv(rows, totals=False): joins rendered rows with "\n". When totals=True, append a final totals row computed from column_totals(rows), prefixed with "TOTAL" (e.g. export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6").
4. Existing behavior must be preserved: export_csv([[1,2],[3,4]]) == "1,2\n3,4" (no totals unless requested).

Authority/constraints:
- You may edit export.py, render.py, totals.py only.
- Do NOT edit test_export.py, exports_legacy.py, pyproject.toml, or uv.lock. exports_legacy.py is explicitly frozen.
- Keep signatures backwards-compatible (new args must default to the current behavior).
- Do not add third-party dependencies.

Validation (must run and report exact output):
  cd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-asoijzuc/rung5 && .venv/bin/python -m pytest -q

Acceptance: all 4 tests pass, 0 failures.

Expected report: files changed with a one-line reason each, the exact pytest summary line (e.g. "4 passed"), and any uncertainty. Stop and ask if a test appears contradictory rather than editing the test.