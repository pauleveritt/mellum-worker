Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-_scsb1ag/rung5

Bug: the CSV export is missing the totals row. `test_export.py` specifies the required behavior; 3 tests currently fail.

Make these exact changes (do not change test_export.py, and do NOT touch exports_legacy.py — its comment says "Do not change"):

1. totals.py — `column_totals(rows)` must return `[]` for empty rows, and for each column sum only the numeric cells, emitting `""` for columns that contain non-numeric (text) cells. Requirement: `column_totals([["a", 1], ["b", 2]]) == ["", 3]`.

2. render.py — `render_rows(rows, mark_last=False)` gains a `mark_last` kwarg. Each row is rendered as comma-joined stringified values. When `mark_last=True`, prefix the LAST rendered row with `"TOTAL,"`. Requirement: `render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]`.

3. export.py — `export_csv(rows, totals=False)` gains a `totals` kwarg. When `totals=True`, append the `column_totals(rows)` row and render with `mark_last=True`. Requirement: `export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"`. Edge case: if `rows` is empty and `totals=True`, do not append an empty row (keep output unchanged, e.g. `""`). Keep the existing default behavior when `totals=False` unchanged.

Verify with: `.venv/bin/pytest -q` from the repo root — all 4 tests must pass.

Report back: files changed, the exact pytest summary line, and any uncertainty.