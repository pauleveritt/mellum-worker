Verified independently — all 4 tests pass.

## Result

**Delegated to `mellum-worker`** (single bounded writer, blocked for same-turn result), then verified the work myself.

**Command:** `uv run --offline pytest -q` → **4 passed in 0.00s**

**Changes (3 files, `test_export.py` untouched):**
- `render.py` — `render_rows(rows, mark_last=False)`; when `mark_last=True`, prepends `TOTAL` to the last rendered row.
- `totals.py` — `column_totals` now sums only numeric cells per column and returns `""` when a column has no numbers.
- `export.py` — `export_csv(rows, totals=False)`; when `totals=True`, appends a `TOTAL` row built from `column_totals`.

The child reported `4 passed`; my own re-run and `git diff` confirm the report — no unverified claim accepted.