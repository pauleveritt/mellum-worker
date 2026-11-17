Objective: Make every test in test_export.py pass by implementing the missing behavior. Currently 3 of 4 tests fail.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-cve06jac/rung4
Python: use the local venv interpreter: `.venv/bin/python -m pytest -q`

Authority boundary: You may edit ONLY export.py, render.py, and totals.py. Do NOT modify test_export.py, pyproject.toml, or any test. Do not run git commit.

Required contracts (derived from the tests):
1. totals.column_totals(rows): returns one result per column. For each column index, sum the numeric cells. If a column contains any non-numeric ("text") cell, that column's result is "" (empty string). Empty input -> []. Example: column_totals([["a", 1], ["b", 2]]) == ["", 3].
2. render.render_rows(rows, mark_last=False): keep current behavior (list of comma-joined strings). When mark_last=True, the LAST rendered row is prefixed with "TOTAL," as a label. Example: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"].
3. export.export_csv(rows, totals=False): keep current behavior when totals is False. When totals=True, append a final totals row using column_totals so the output ends with a "TOTAL" label row. Example: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". (The totals row's non-label cells come from column_totals(rows); skipping non-numeric columns is expected.)

Constraints: Keep changes minimal and idiomatic Python matching the existing code style. Do not add dependencies.

Validation (required): run `.venv/bin/python -m pytest -q` from the repo root and confirm 4 passed.

Stop/ask conditions: If a test appears to contradict these contracts, stop and report rather than changing the test.

Report back: status (done/blocked), files changed with a one-line description each, the exact final pytest output (e.g. "4 passed"), and any blocker or uncertainty.