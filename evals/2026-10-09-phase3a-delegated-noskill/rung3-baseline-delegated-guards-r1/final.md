Done via `mellum-worker`, and independently verified.

**Changes**
- `rows.py:1` — `def fetch_rows(source)` → `def load_rows(source)`
- `report.py:1,5` — import and call site updated
- `test_report.py` needed no change (it only imports `report`)
- Diff limited to those two files; no behavior/signature change

**Verification (run fresh by me, not just the child's report)**
- `rg -n fetch_rows` → no matches (exit 1)
- `rg -n load_rows` → definition in `rows.py:1`, import + call in `report.py:1,5`
- `git diff` confirms only the rename
- `uv run pytest -q` → `1 passed in 0.00s`, exit 0