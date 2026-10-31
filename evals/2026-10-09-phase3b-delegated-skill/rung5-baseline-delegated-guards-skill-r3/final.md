Done. The export now includes a totals row.

**Files changed** (by `mellum-worker`):
- `totals.py` — `column_totals` now sums only numeric cells and returns `""` for all-text columns (previously crashed on `int + str`).
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,`.
- `export.py` — `export_csv(rows, totals=False)` appends the `column_totals(rows)` row marked as the total.

**Verification** (run by me, not the worker):
```
$ uv run --offline pytest -q
....                                                                     [100%]
4 passed in 0.00s
exit: 0
```

Protected files unchanged: `test_export.py`, `exports_legacy.py`, `pyproject.toml`. Diff is 3 files, +25/−5.

The worker made the final code change; I independently confirmed it. One note on the design: the `TOTAL` marker is produced by prepending to the rendered string, so a text column yields an empty cell in the totals row (e.g. `TOTAL,,3`). The tests don't cover that case, so flag it if you need different behavior.