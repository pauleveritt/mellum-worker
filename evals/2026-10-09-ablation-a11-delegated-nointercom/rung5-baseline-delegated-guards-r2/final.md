Done. The totals row is now exported, verified independently.

**What was wrong (root cause):** `export_csv` had no `totals` path, `render_rows` had no way to mark the total line, and `column_totals` crashed on the text column because it `sum()`-ed strings.

**Changes (3 files, tests untouched):**
- `totals.py` — `column_totals` now sums only numeric cells per column and emits `""` for a column with no numbers (e.g. `[["a",1],["b",2]] → ["", 3]`).
- `render.py` — `render_rows(rows, mark_last=False)`; `mark_last=True` prefixes the last row with `TOTAL` (`[[1,2],[3,4]] → ["1,2","TOTAL,3,4"]`).
- `export.py` — `export_csv(rows, totals=False)`; `totals=True` appends `column_totals(rows)` and renders with `mark_last=True` (`[[1,2],[3,4]] → "1,2\n3,4\nTOTAL,4,6"`).

**Verification (run by me, not just reported):**
```
.venv/bin/python -m pytest -q
....                                                                     [100%]
4 passed in 0.00s
```
`git diff --name-only` confirms only `export.py`, `render.py`, `totals.py` changed — `test_export.py` and `exports_legacy.py` untouched.

**Delegation note:** `mellum-worker` was used as requested. It stopped silently on the first run after editing only `totals.py` (small-model empty stop). I resumed the same run with a bounded continuation; it then completed `render.py` and `export.py` and reported `4 passed`. I re-ran the suite myself to confirm.