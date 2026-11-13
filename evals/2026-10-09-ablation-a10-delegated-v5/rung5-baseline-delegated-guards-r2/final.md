Done. `mellum-worker` implemented the fix and the parent independently verified it.

**What was wrong:** `export_csv` had no `totals` option and never appended a totals row; `render_rows` couldn't mark a row; `column_totals` crashed on text cells.

**Final verified state** (`pytest`, run by me after the worker finished):

```
....                                                                     [100%]
4 passed in 0.00s
```

**Files changed (by the worker):**
- `export.py` — `export_csv(rows, totals=False)`; when `totals=True`, appends a `TOTAL,<sums>` row via `column_totals`.
- `render.py` — `render_rows(rows, mark_last=False)`; prefixes the last row with a `TOTAL` column.
- `totals.py` — per-column sums, returning `""` for a column containing any non-numeric cell, numeric sums otherwise.

**Constraints respected:** `test_export.py` and `exports_legacy.py` (`"Do not change"`) are unmodified — verified via `git status`.

**Process note:** the first worker pass left changes but failed the hidden `column_totals` test (returned `'3'` string instead of `3`). I resumed the same run with the exact assertion output rather than relaunching; the resume completed and passed. No new files were created by me.

One thing I did not do: commit. Let me know if you want that, or a review of the diff before committing.