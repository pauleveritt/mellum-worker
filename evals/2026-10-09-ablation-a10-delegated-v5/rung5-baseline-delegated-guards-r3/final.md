Done and independently verified.

**Fix:** `export_csv(rows, totals=True)` now appends the totals row. The child implemented three coordinated changes across `export.py`, `render.py`, and `totals.py`:

- `totals.py` — `column_totals()` returns `""` for non-numeric columns instead of raising `TypeError`
- `render.py` — `render_rows(..., mark_last=True)` prefixes the final row with `TOTAL`
- `export.py` — `export_csv(..., totals=True)` appends `TOTAL,<totals>`; defaults unchanged

**Verification (parent-run, not the child's word):**
```
$ uv run --offline pytest -q
....                                                                     [100%]
4 passed in 0.01s
```

Diff is minimal and root-cause targeted (3 files, +22/−5). `exports_legacy.py` and `test_export.py` were left untouched as instructed, and the pre-existing `test_export_without_totals` still passes, confirming default behavior is preserved.