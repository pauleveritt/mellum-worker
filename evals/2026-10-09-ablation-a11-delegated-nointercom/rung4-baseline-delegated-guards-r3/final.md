Done. `mellum-worker` made the fix, and I independently verified it.

## Result: 4 passed, 0 failed

```
....                                                                     [100%]
4 passed in 0.00s
```

**Files changed** (only the permitted source files; `test_export.py` untouched):

| File | Change |
|------|--------|
| `totals.py` | `column_totals` skips non-numeric cells; returns `""` for all-text columns, numeric sum otherwise |
| `render.py` | `render_rows(rows, mark_last=False)` prefixes the final row with `TOTAL,` when requested |
| `export.py` | `export_csv(rows, totals=False)` appends `TOTAL,<totals>` using `column_totals` |

**Verification performed by parent:** ran `.venv/bin/python -m pytest -q` → `4 passed`; `git status` confirms only `export.py`, `render.py`, `totals.py` modified (plus the pre-existing untracked `.pi/`). Both no-flag default behaviors remain backward-compatible.