Done — verified independently, not just on the child's word.

**Result:** 4/4 tests pass (`.venv/bin/python -m pytest -q` → `4 passed in 0.00s`).

**Files changed** (only these three; `exports_legacy.py` and `test_export.py` diff-clean):
- `totals.py` — `column_totals` now sums numeric cells only; all-text column → `""`
- `render.py` — `render_rows(rows, mark_last=False)`, prefixes last row with `TOTAL`
- `export.py` — `export_csv(rows, totals=False)` appends the marked totals row

**Residual note (not spec'd, unchanged):** `export_csv([], totals=True)` returns the bare string `'TOTAL'`, since `column_totals([])` is `[]`. No test covers empty input with `totals=True`; say the word if you want it to return `''` instead. The child also duplicated the marking logic in `export.py` rather than reusing `render_rows(..., mark_last=True)` — cosmetic redundancy, not a correctness issue.