Verified independently — 4/4 tests pass.

**Task complete.** `mellum-worker` fixed 3 failing tests in `/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ntazj29t/rung4`:

| File | Change |
|------|--------|
| `totals.py` | `column_totals` now returns `""` for columns containing non-numeric cells; sums numeric columns |
| `render.py` | `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,` |
| `export.py` | `export_csv(rows, totals=False)` appends a `TOTAL,...` row computed via `column_totals` |

Default behavior unchanged, so `test_export_without_totals` still passes. No test files were touched and no dependencies added.

Independent verification:
```
$ .venv/bin/python -m pytest -q
....                                                                     [100%]
4 passed in 0.00s
```

One note for your awareness (not a defect against the spec): `render_rows(..., mark_last=True)` labels the last row "TOTAL" without computing actual sums, whereas `export_csv(..., totals=True)` computes sums via `column_totals`. The tests define these behaviors independently, and both pass — flagging only if you intended a single consistent totals source.