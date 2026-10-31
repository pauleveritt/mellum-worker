Done. mellum-worker fixed it and I independently verified.

## Result

**All 4 tests pass** (`.venv/bin/python -m pytest -q` → `4 passed in 0.00s`).

### Changes made (test_export.py untouched)

- **`totals.py`** — `column_totals` now sums only numeric cells per column, returning `""` for columns with no numbers (`[["a",1],["b",2]] → ["", 3]`); empty input still returns `[]`.
- **`render.py`** — `render_rows(rows, mark_last=False)`; when `mark_last=True`, prefixes the last row with `TOTAL,`.
- **`export.py`** — `export_csv(rows, totals=False)`; when `totals=True`, appends a total row built from `column_totals(rows)`.

### Verification
- own pytest run: **4 passed**
- `git status`: only `totals.py`, `render.py`, `export.py` modified; `test_export.py` unchanged.

No residual issues. The `.pi/` directory is untracked but pre-existing and unrelated.