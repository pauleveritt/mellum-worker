Done. `mellum-worker` implemented the missing totals row; I verified the workspace independently.

**Result: all 4 tests pass** (`.venv/bin/python -m pytest -q` → `4 passed in 0.00s`), and `exports_legacy.py` was left untouched.

Changes:
- `totals.py` — `column_totals` now skips non-numeric cells and emits `""` for all-text columns (`[["a",1],["b",2]]` → `["", 3]`).
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last rendered row with `TOTAL`.
- `export.py` — `export_csv(rows, totals=False)` appends the marked totals row when `totals=True`.

Residual note (not tested, not required): `export_csv([], totals=True)` returns `"\nTOTAL,"` rather than `""`; empty/edge input handling for the `totals=True` path could be tightened later if that case matters.