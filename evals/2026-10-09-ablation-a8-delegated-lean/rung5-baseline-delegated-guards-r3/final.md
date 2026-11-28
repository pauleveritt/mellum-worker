Delegated to `mellum-worker`; verified myself afterward.

**Result: fixed, 4/4 tests pass.**

Baseline (before): 3 failed, 1 passed — `export_csv()` had no `totals` param, `render_rows()` had no `mark_last`, and `column_totals()` crashed on text cells.

Changes (minimal diff, only the three target files):

- `render.py` — `render_rows(rows, mark_last=False)`; when true, prefixes the last rendered line with `"TOTAL,"`.
- `totals.py` — `column_totals(rows)` now sums numeric cells per column and yields `""` for any column containing non-numeric cells (int-coerced whole numbers, so no `.0`).
- `export.py` — `export_csv(rows, totals=False)`; when true appends the `TOTAL,...` line built from `column_totals`.

Untouched: `test_export.py`, `exports_legacy.py` (as instructed). Backward compatible — both new params are keyword-defaulted.

Verification (my own run, not just the child's gate):
```
$ .venv/bin/python -m pytest -q
....                                                                     [100%]
4 passed in 0.00s
```

Residual notes: no commit was made (working tree has the diff above if you want to review it first). `column_totals` sums with `float()` internally, so a column of mixed int/float returns an int when whole — behavior matches the tests, but flag it if you need strict type preservation.