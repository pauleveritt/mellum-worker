Done. `mellum-worker` implemented the missing totals support and I independently verified it.

**Changes** (3 files, +32/-5):
- `totals.py` — `column_totals()` now sums numeric columns and returns `""` for any column containing text.
- `render.py` — `render_rows(rows, mark_last=False)` prefixes the last row with `TOTAL` when requested; default output unchanged.
- `export.py` — `export_csv(rows, totals=False)` appends a `TOTAL,...` row when `totals=True`; default output unchanged.

**Verification:**
- `.venv/bin/python -m pytest -q` → `4 passed in 0.00s`
- `git diff --stat -- exports_legacy.py test_export.py` → empty; the legacy exporter and the tests were left untouched as required.

One implementation note worth flagging: `render_rows(mark_last=True)` is implemented as a string prefix (`'TOTAL,' + last_row`) rather than prepending a cell value. It satisfies the spec and all tests, but if a caller ever relies on the row-values path for `mark_last`, this is the spot to revisit.