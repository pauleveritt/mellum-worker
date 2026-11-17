Done via `mellum-worker`, verified independently.

**Changes:**
- `rows.py:1` — `def fetch_rows(source)` → `def load_rows(source)`
- `report.py:1` — `from rows import fetch_rows` → `from rows import load_rows`
- `report.py:5` — `fetch_rows(source)` → `load_rows(source)`

**Verification (run by me, not just the child):**
- `grep -rn "fetch_rows" .` → no matches
- `uv run pytest -q` → `1 passed`
- `git diff` confirms only the 3 intended lines changed; no other behavior touched.