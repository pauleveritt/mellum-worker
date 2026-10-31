Done. `mellum-worker` performed the rename; I verified independently.

**Changes:**
- `rows.py:1` — `def fetch_rows` → `def load_rows` (body unchanged)
- `report.py:1` — import updated to `load_rows`
- `report.py:5` — call updated to `load_rows(source)`

**Verification (run by me, not just the worker):**
- `grep -rn "fetch_rows" . --include="*.py"` → no matches (exit 1)
- `grep -rn "load_rows"` → the 3 expected sites
- `.venv/bin/python -m pytest -q` → `1 passed`