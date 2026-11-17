Done — verified independently, not just on the child's word.

**Result:** 4 passed in 0.00s (was 3 failed, 1 passed). `test_export.py` untouched.

Files changed (minimal, all three implementation modules):

| File | Change |
|---|---|
| `totals.py` | `column_totals` skips non-numeric cells; returns `""` for a column with no numerics |
| `render.py` | `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL,` |
| `export.py` | `export_csv(rows, totals=False)` appends a `TOTAL` row via `column_totals` |

**Verification I ran myself:**
```
....                                                                     [100%]
4 passed in 0.00s
```
`git status` shows only `export.py`, `render.py`, `totals.py` modified; the test file is unchanged, and the pre-existing default-behavior test (`test_export_without_totals`) still passes.

**Residual risk worth knowing:** for a column that mixes numerics and text (e.g. `[[1, "x"], [2, 3]]`), the child's implementation silently skips the text cell and totals the rest. No test pins that behavior, so it's an untested interpretation rather than a confirmed requirement. Flag it if mixed columns are meant to be an error or a `""`.