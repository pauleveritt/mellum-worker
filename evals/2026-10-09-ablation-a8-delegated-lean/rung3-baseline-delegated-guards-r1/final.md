Done — `mellum-worker` performed the rename, and I verified it independently.

**Changes**
- `rows.py`: `def fetch_rows` → `def load_rows`
- `report.py`: import and call site updated

**Verification (run by me, not just the child)**
- `grep -rn "fetch_rows"` → no matches (exit 1)
- `grep -rn "load_rows"` → definition + import + call site, all present
- `git diff` shows only the 3 intended line changes
- `.venv/bin/python -m pytest -q` → `1 passed`