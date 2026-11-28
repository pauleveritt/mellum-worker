Done. `mellum-worker` performed the rename, and I verified it independently.

**Changes**
- `rows.py:1` — `def fetch_rows(source):` → `def load_rows(source):`
- `report.py:1` — `from rows import fetch_rows` → `from rows import load_rows`
- `report.py:5` — call site `fetch_rows(source)` → `load_rows(source)`

**Verification (parent-run, not just child-reported)**
- `grep -rn "fetch_rows"` across `*.py` → no matches (excluding `.venv`)
- `load_rows` present at all three expected sites
- `pytest -q` → `1 passed in 0.00s`

No behavior changes beyond the rename. Note the worker's edits are uncommitted in the working tree; say the word if you want them committed.