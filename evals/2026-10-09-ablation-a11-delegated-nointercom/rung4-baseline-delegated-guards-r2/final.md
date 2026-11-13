Done. `mellum-worker` fixed the failing tests, and I independently verified the result.

## Result

**All 4 tests pass** (`.venv/bin/python -m pytest -q` → `4 passed`), test file untouched.

## Changes made (by mellum-worker)

- **`totals.py`** — `column_totals` now sums only numeric cells per column and returns `""` for a column with no numeric values (fixes the `int + str` crash).
- **`render.py`** — `render_rows` gained a `mark_last=False` keyword that prefixes the last rendered row with `"TOTAL,"`.
- **`export.py`** — `export_csv` gained a `totals=False` keyword that appends a `TOTAL` row built from `column_totals` when enabled.

## Verification

```
git diff --stat -- test_export.py   # empty → test file unchanged
.venv/bin/python -m pytest -q       # 4 passed in 0.00s
```

The working tree now has uncommitted changes in the three source files; `test_export.py` is clean. Let me know if you'd like these committed.